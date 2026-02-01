"""
AI 聊天模組 - 整合 Google Gemini API
"""

import os
import google.generativeai as genai
from typing import List, Dict
import asyncio
from PyQt6.QtCore import QThread, pyqtSignal


class AIWorker(QThread):
    """AI 處理執行緒"""
    
    response_received = pyqtSignal(str)  # 回應訊號
    error_occurred = pyqtSignal(str)     # 錯誤訊號
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.user_message = ""
        self.chat_history = []
        self.model = None
        self.chat_session = None
        
        # 初始化 Gemini
        self.init_gemini()
    
    def init_gemini(self):
        """初始化 Gemini API"""
        try:
            genai.configure(api_key=self.api_key)
            
            # 配置模型
            generation_config = {
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            self.model = genai.GenerativeModel(
                model_name="gemini-pro",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # 創建聊天會話
            self.chat_session = self.model.start_chat(history=[])
            
        except Exception as e:
            self.error_occurred.emit(f"初始化 Gemini 失敗: {str(e)}")
    
    def set_message(self, message: str):
        """設定要發送的訊息"""
        self.user_message = message
    
    def run(self):
        """執行 AI 請求"""
        try:
            if not self.chat_session:
                self.error_occurred.emit("聊天會話未初始化")
                return
            
            # 發送訊息並獲取回應
            response = self.chat_session.send_message(self.user_message)
            
            # 發射回應訊號
            self.response_received.emit(response.text)
            
        except Exception as e:
            self.error_occurred.emit(f"AI 回應錯誤: {str(e)}")


class AIManager:
    """AI 管理器 - 管理與 Gemini 的互動"""
    
    def __init__(self, api_key: str = None):
        """
        初始化 AI 管理器
        
        Args:
            api_key: Gemini API 金鑰，如果為 None 則從環境變數讀取
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.worker = None
        
        if not self.api_key:
            raise ValueError("請提供 Gemini API 金鑰或設定 GEMINI_API_KEY 環境變數")
        
        self.worker = AIWorker(self.api_key)
    
    def send_message(self, message: str, callback=None, error_callback=None):
        """
        發送訊息給 AI
        
        Args:
            message: 用戶訊息
            callback: 收到回應時的回調函數
            error_callback: 發生錯誤時的回調函數
        """
        if self.worker.isRunning():
            return  # 如果還在處理上一個請求，則忽略
        
        # 設定訊息
        self.worker.set_message(message)
        
        # 連接訊號
        if callback:
            self.worker.response_received.connect(callback)
        if error_callback:
            self.worker.error_occurred.connect(error_callback)
        
        # 啟動執行緒
        self.worker.start()
    
    def reset_chat(self):
        """重置聊天會話"""
        if self.worker:
            self.worker = AIWorker(self.api_key)


# 使用範例
if __name__ == "__main__":
    # 測試 AI 管理器
    def on_response(text):
        print(f"AI 回應: {text}")
    
    def on_error(error):
        print(f"錯誤: {error}")
    
    # 請將 'YOUR_API_KEY' 替換為實際的 API 金鑰
    ai_manager = AIManager(api_key='YOUR_API_KEY')
    ai_manager.send_message("你好！", callback=on_response, error_callback=on_error)
