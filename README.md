# DiDiDaDa

## 專案介紹
DiDiDaDa 是一個基於 Flask 框架的網頁應用，結合 OpenAI API 與中央氣象局開放資料，提供使用者互動體驗和即時天氣資訊。

## 功能特色
- 使用 OpenAI 進行自然語言互動
- 取得中央氣象局天氣資料 API
- 使用者管理與檔案上傳功能
- 前端頁面與後端整合，操作簡易

## 安裝與執行

1. 克隆專案
```bash
git clone https://github.com/zander1122/DiDiDaDa.git
cd DiDiDaDa
2.建立虛擬環境並安裝相依套件
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Mac/Linux
pip install -r requirements.txt
3.設定環境變數（請替換成你的 API Key）
set openai.api_key=你的OpenAI_API_Key
set CWB_TOKEN=你的中央氣象局API金鑰
4.執行應用程式
python main.py

## 專案結構
DiDiDaDa/
├── app/
│   ├── route.py
│   ├── models/
│   └── static/
├── main.py
├── requirements.txt
├── .env
└── README.md
