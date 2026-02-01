
from google import genai
import os

# 填入你的 API Key
API_KEY = "AIzaSyCW9WS7wG82UlWeEBmn3jXo6WMUi_lXfkc"

def list_available_models():
    client = genai.Client(api_key=API_KEY)
    
    print("正在查詢可用模型 (如果不支援會直接跳過)...\n")
    try:
        # 直接走訪所有模型
        for model in client.models.list():
            # 新版 SDK 的 model 物件屬性通常是 model.name
            print(f"- {model.name}")
            
    except Exception as e:
        print(f"查詢失敗: {e}")

if __name__ == "__main__":
    list_available_models()