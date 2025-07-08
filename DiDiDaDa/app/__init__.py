from flask import Flask
import pymongo, cloudinary, tempfile

# Initialize database connection, bypassing SSL certificate validation
connection_string = "mongodb+srv://root:root123@mycluster.k8uzbnf.mongodb.net/?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"
client = pymongo.MongoClient(connection_string)

db = client.DiDiDaDa
# print("Database connection established successfully")

# 初始化 Flask 伺服器
app = Flask( __name__, static_folder="static", static_url_path="/" )
app.secret_key = "any string but secret"
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["db"] = client.DiDiDaDa

# 添加 Cloudinary 配置
cloudinary.config(
  cloud_name = 'dr9eanxyq',  
  api_key = '641493788268261',  
  api_secret = 'L0lhq-DX3Wj40yNRrlVCePF8d6U'  
)
# 引入路由設定
from . import route
