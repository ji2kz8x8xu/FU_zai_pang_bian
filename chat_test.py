
from google import genai
import os

# --- 設定區域 ---
# 這裡填入你的 Google API Key
API_KEY = "AIzaSyCW9WS7wG82UlWeEBmn3jXo6WMUi_lXfkc" 

def start_chat():
    # 1. 初始化 Client (新版寫法)
    client = genai.Client(api_key=API_KEY)

    try:
        # 2. 建立聊天室窗 (Chats)
        # 新版 SDK 會自動處理連線版本，建議使用 'gemini-1.5-flash' (快速) 或 'gemini-2.0-flash-exp' (最新預覽)
        chat = client.chats.create(model="gemini-2.5-flash")

        print("--- Google GenAI SDK (新版) 聊天測試 ---")
        print("輸入 'exit' 或 'quit' 結束程式。\n")

        while True:
            # 3. 獲取使用者輸入
            user_input = input("你: ")
            
            if user_input.lower() in ['exit', 'quit']:
                print("結束測試。")
                break
            
            if not user_input.strip():
                continue

            # 4. 發送訊息並取得回應
            response = chat.send_message(user_input)
            
            # 5. 顯示回應
            print(f"AI: {response.text}")
            print("-" * 30)
            
    except Exception as e:
        print(f"發生錯誤: {e}")
        # 如果還是 404，可能是 API Key 權限或模型名稱打錯，可以試試 'gemini-1.5-pro'

if __name__ == "__main__":
    start_chat()