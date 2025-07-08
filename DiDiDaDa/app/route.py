import openai, requests,os
from flask import *
from datetime import datetime, timedelta
from .import app, db  
from .models.upload import *

# Set your OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")

cwb_token = os.getenv("CWB_TOKEN")
URL = f"https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-D0047-091?Authorization={cwb_token}"

app.secret_key = 'your_secret_key'

# 全局變數來存儲消息和上一個 AI 回應
messages = []
last_ai_response = ""
# 用于存储对话历史的全局变量（限制为最近的 n 轮对话）
max_history = 10  # 您可以根据需要调整此值
dialog_history = []

# 設定 PromptPerfect 的 API 密鑰和 URL
YOUR_GENERATED_SECRET = os.getenv("PROMPTPERFECT_API_KEY")
promptperfect_url = "https://api.promptperfect.jina.ai/optimize"


@app.route("/")
def Index():
    return render_template('index.html')

# /error?msg=錯誤訊息
@app.route("/error")
def error():
    message = request.args.get("msg", "發生錯誤，請聯繫克服")
    return render_template("error.html", message=message)


@app.route("/Login")
def Login():
    if "username" in session:
        return render_template("mycloset.html")
    else:
        return render_template("login.html")  # 權限管理，沒有登入無法進入todays
    # return render_template('login.html')

@app.route("/Signup")
def signup():
    return render_template('signup.html')

@app.route('/4SignupPG', methods=['POST'])
def forSignupPG():
    #　從前端接收資料
    action = request.form.get('action')
    username = request.form.get('username')
    password = request.form.get('password')
    sex = request.form.get('sex')  # 這是新增的性別字段
    height = float(request.form.get('height', 180))  # 新增接收身高
    weight = float(request.form.get('weight', 80))  # 新增接收體重

    # 計算 BMI
    bmi = weight / (height/100)**2

    if action == 'signup': 
        collection = db.user
        # 檢查是否有相同 使用者 的文件資料
        if collection.find_one({"username": username}):
            return redirect("/error?msg=用戶名已經被註冊")
        # 把資料放進資料庫，完成註冊
        collection.insert_one({
            "username": username,
            "password": password,
            'sex': sex,
            "height": height,
            "weight": weight,
            "bmi": bmi  # 存入計算的 BMI
        })
        return redirect("/Login")
    elif action == '2signup':       return redirect("/Signup")
    elif action == '2login':        return redirect("/signout")
    elif action == 'login':
        if not username or not password:
            return redirect("/error?msg=用戶和密碼不得為空")

        # 和資料庫互動
        collection = db.user
        # 檢查帳號密碼是否正確
        result = collection.find_one({
            "$and": [
                {"username": username},
                {"password": password}
            ]
        })
        global usersex, userbmi
        usersex = result["sex"]
        userbmi = result["bmi"]
        # 找不到對應的資料，登入失敗，導向到錯誤頁面
        if not result:
            return redirect("/error?msg=帳號或密碼輸入錯誤")
        # 登入成功，在 Session紀錄會員資訊，導向到會員頁面
        session["username"] = result["username"]
        return redirect("/Mycloset")

@app.route("/signout")
def signout():
    if "username" in session:
        del session["username"]  # 移除 Session 中的會員資訊
        return redirect("/Login")
    else:
        return redirect("/Login")




@app.route("/Mycloset")
def mycloset():
    # 檢查是否有登入使用者
    if 'username' in session:
        current_username = session['username']
        
        # 根據用戶名稱檢索相關的圖像數據
        lower_body_images = db.user_images.find({"category": "lower_body", "userid": current_username})
        upper_body_images = db.user_images.find({"category": "upper_body", "userid": current_username})
        
        return render_template('mycloset.html', lower_body_images=lower_body_images, upper_body_images=upper_body_images)
    else:
        return redirect("/error?msg=尚未登入")
    
@app.route('/upload', methods=['POST'])
def upload():
    # 取得上傳文件、使用者名、上下身
    file = request.files['fileToUpload']
    username = session.get("username")
    category = request.form.get('category')

    # 调用函数上传并存储文件
    upload_image(file, username, category)

    # 返回空响应
    return ('', 200)


@app.route('/getPrompt', methods=['POST'])
def get_prompt():
    global combined_prompt
    if userbmi < 18.5:
        category = 'slimmer'
    elif 18.5 <= userbmi < 24.9:
        category = 'moderate'
    elif 24.9 <= userbmi < 29.9:
        category = 'fat'
    else:
        category = 'heavier'
    # 清除旧的会话变量
    session.pop('generated_image_url', None)
    session.pop('combined_prompt', None)

    top_image_url = request.form['topImageURL']
    bottom_image_url = request.form['bottomImageURL']

    # 查询MongoDB以找到与这些图像关联的记录
    top_image_prompt = db.user_images.find_one({'url': top_image_url})
    bottom_image_prompt = db.user_images.find_one({'url': bottom_image_url})

    if top_image_prompt and bottom_image_prompt:
        top_prompt = top_image_prompt.get('prompt', 'Prompt not found')
        bottom_prompt = bottom_image_prompt.get('prompt', 'Prompt not found')

        combined_prompt = f"A {category} {usersex} full-body portrait of a person wearing  with {top_prompt} And are also wearing {bottom_prompt}"
        session.pop('generated_image_url', None)  # 清除已存在的图片 URL
        session['combined_prompt'] = combined_prompt
        print(combined_prompt)
        return jsonify({'success': True, 'redirect_url': url_for('Todays'),'combined_prompt': combined_prompt})
    else:
        return jsonify({'success': False, 'error': 'Image not found in database'})



@app.route("/Todays")
def Todays():
    if "username" in session:
        # 获取城市名称列表
        response = requests.get(URL)
        data = response.json()
        locations = data['records']['locations'][0]['location']
        city_names = [location['locationName'] for location in locations]

        # 检查 session 中是否有 combined_prompt
        combined_prompt = session.get('combined_prompt')


        if combined_prompt:
            # 如果有，调用 generate_image 函数生成图片
            generation_response = openai.Image.create(
                prompt=combined_prompt,
                n=1,
                size="1024x1024",
                model="dall-e-3",
                response_format="url"
            )
            generated_image_url = generation_response["data"][0]["url"]

            # 清除 session 中的 combined_prompt
            session.pop('combined_prompt', None)

            # 将生成的图片 URL 传递给模板
            return render_template('todays.html', city_names=city_names, image_url=generated_image_url)
        else:
            # 如果 session 中没有 combined_prompt，正常显示 todays 页面
            return render_template('todays.html', city_names=city_names, image_url=None)
    else:
        return redirect("/error?msg=尚未登入")


@app.route('/generate_image', methods=['POST'])
def generate_image():
    data = request.get_json()
    optimized_prompt = data.get('optimized_prompt')

    if not optimized_prompt:
        return jsonify({'error': 'No optimized prompt provided'}), 400

    try:
        generation_response = openai.Image.create(
            prompt=optimized_prompt,
            n=1,
            size="1024x1024",
            model="dall-e-3",
            response_format="url"
        )

        generated_image_url = generation_response["data"][0]["url"]
        return jsonify({'image_url': generated_image_url})
    except Exception as e:
        return jsonify({'error': f"Error: {str(e)}"}), 500


@app.route('/chat', methods=['POST'])
def chat():
    global last_ai_response
    global dialog_history

    data = request.get_json()
    user_message = data.get('user_message')

    if not user_message:
        return jsonify({"ai_msg": "No message received"}), 400

    try:
        if len(dialog_history) >= max_history:
            dialog_history.pop(0)

        dialog_history.append({"role": "user", "content": user_message})

        # 这里直接发送一个翻译的指令给 AI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Translate the following to English: " + user_message}
            ] + dialog_history,
        )
        ai_response = response.choices[0].message['content']

        dialog_history.append({"role": "assistant", "content": ai_response})
        last_ai_response = ai_response
        print(last_ai_response)

        return jsonify({"ai_msg": ai_response})
    except Exception as e:
        return jsonify({"ai_msg": f"Error: {str(e)}"}), 500
    
    
@app.route('/optimize_prompt', methods=['POST'])
def optimize_prompt():
    # 从请求中获取AI的回答
    last_ai_response = request.get_json().get('last_ai_response')


    if not last_ai_response:
        return jsonify({'error': 'No AI response to optimize'}), 400

    try:
        headers = {
            "x-api-key": "GUHSU3G8P2mYP4qb0Tju:ed8c25973e50480d7536bee548ba5bb8f48d79b5361c776a78168b51b22b0215",
            "Content-Type": "application/json"
        }
        payload = {
            "data": {
                "prompt": combined_prompt+ last_ai_response ,
                "targetModel": "dall-e"
            }
        }

        # 发送请求到 PromptPerfect API
        response = requests.post(promptperfect_url, headers=headers, json=payload)

        if response.status_code == 200:
            response_json = response.json()
            optimized_prompt = response_json.get('result', {}).get('promptOptimized')
            return jsonify({'optimized_prompt': optimized_prompt})
        else:
            return jsonify({'error': f"请求失败，状态码：{response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

@app.route('/weather', methods=['POST'])
def get_weather():
    selected_city = request.form.get('city')

    response = requests.get(URL)
    data = response.json()
    locations = data['records']['locations'][0]['location']

    # 獲取當前日期和星期，只取五天的日期
    today = datetime.now()
    days = [(today + timedelta(days=i)).strftime('%m/%d') for i in range(5)]
    chinese_days = [(today + timedelta(days=i)).strftime('%A') for i in range(5)]
    chinese_day_dict = {
        'Monday': '星期一',
        'Tuesday': '星期二',
        'Wednesday': '星期三',
        'Thursday': '星期四',
        'Friday': '星期五',
        'Saturday': '星期六',
        'Sunday': '星期日'
    }
    chinese_days = [chinese_day_dict[day] for day in chinese_days]

    temperatures = []
    rain_chances = []

    for location in locations:
        if location['locationName'] == selected_city:
            for weather_element in location['weatherElement']:
                element_name = weather_element['elementName']

                if element_name == "T":
                    temperatures = [t['elementValue'][0]['value'] for t in weather_element['time']][:5]
                if element_name == "PoP12h":
                    rain_chances = [pop['elementValue'][0]['value'] for pop in weather_element['time']][:5]

    weather_data = []
    for i, day in enumerate(days):
        if i < len(temperatures) and i < len(rain_chances):
            weather_data.append({
                'date': day,
                'day': chinese_days[i],
                'temperature': temperatures[i],
                'rain_chance': rain_chances[i]
            })

    return jsonify(weather_data)

