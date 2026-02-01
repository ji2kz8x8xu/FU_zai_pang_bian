"""
福在旁邊 - 完整整合版
整合懸浮球、面板、AI 聊天和語音輸入
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer

# 匯入自定義模組
from floating_assistant import FloatingBall
from floating_panel import FloatingPanel
from ai_chat import AIManager
from voice_input import VoiceInput


class IntegratedFloatingPanel(FloatingPanel):
    """整合版主面板 - 添加 AI 和語音功能"""
    
    def __init__(self, parent_ball, ai_manager, voice_input):
        self.ai_manager = ai_manager
        self.voice_input = voice_input
        self.is_voice_recording = False
        
        super().__init__(parent_ball)
        
        # 連接語音輸入訊號
        self.setup_voice_callbacks()
    
    def setup_voice_callbacks(self):
        """設定語音輸入回調"""
        # 這些回調會在 toggle_voice_recording 中設定
        pass
    
    def process_ai_response(self, user_message):
        """處理 AI 回應 - 整合實際的 Gemini API"""
        def on_response(text):
            self.add_message(text, is_user=False)
        
        def on_error(error):
            self.add_message(f"❌ {error}", is_user=False)
        
        # 添加思考中的提示
        self.add_message("思考中...", is_user=False)
        
        # 發送到 AI
        self.ai_manager.send_message(user_message, callback=on_response, error_callback=on_error)
    
    def toggle_voice_recording(self):
        """切換語音錄製狀態 - 整合實際的語音輸入"""
        def on_transcription(text):
            # 將語音轉換的文字填入輸入框
            self.input_field.setText(text)
            # 自動發送
            self.send_message()
            # 恢復按鈕樣式
            self.voice_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(100, 200, 100, 180);
                    border-radius: 22px;
                    font-size: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(100, 200, 100, 220);
                }
            """)
        
        def on_error(error):
            self.add_message(f"🎤 語音錯誤: {error}", is_user=False)
            # 恢復按鈕樣式
            self.voice_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(100, 200, 100, 180);
                    border-radius: 22px;
                    font-size: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(100, 200, 100, 220);
                }
            """)
        
        def on_start():
            # 添加錄音中的訊息
            self.add_message("🎤 正在錄音...", is_user=False)
        
        def on_stop():
            # 添加處理中的訊息
            self.add_message("🎤 處理中...", is_user=False)
        
        # 切換錄音狀態
        is_recording = self.voice_input.toggle_recording(
            on_transcription=on_transcription,
            on_error=on_error,
            on_start=on_start,
            on_stop=on_stop
        )
        
        # 更新按鈕樣式
        if is_recording:
            self.voice_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 100, 100, 200);
                    border-radius: 22px;
                    font-size: 20px;
                    animation: pulse 1s infinite;
                }
            """)
        else:
            self.voice_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(100, 200, 100, 180);
                    border-radius: 22px;
                    font-size: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(100, 200, 100, 220);
                }
            """)


class IntegratedFloatingBall(FloatingBall):
    """整合版懸浮球"""
    
    def __init__(self, ai_manager, voice_input):
        self.ai_manager = ai_manager
        self.voice_input = voice_input
        super().__init__()
    
    def show_panel(self):
        """顯示整合版面板"""
        if hasattr(self, 'panel') and self.panel:
            self.panel.toggle_panel()
        else:
            # 創建整合版面板
            self.panel = IntegratedFloatingPanel(self, self.ai_manager, self.voice_input)
            self.panel.show()


class FuZaiPangBian(QWidget):
    """主應用程式"""
    
    def __init__(self, api_key=None):
        super().__init__()
        
        # 初始化 AI 管理器
        try:
            self.ai_manager = AIManager(api_key=api_key)
        except ValueError as e:
            print(f"警告: {e}")
            print("AI 功能將無法使用，請設定 GEMINI_API_KEY 環境變數或在啟動時提供 API 金鑰")
            self.ai_manager = None
        
        # 初始化語音輸入
        self.voice_input = VoiceInput()
        
        # 創建懸浮球
        self.floating_ball = IntegratedFloatingBall(self.ai_manager, self.voice_input)
        self.floating_ball.show()


def main():
    """主函數"""
    app = QApplication(sys.argv)
    
    # 設定應用程式資訊
    app.setApplicationName("福在旁邊")
    app.setOrganizationName("FuZaiPangBian")
    
    # 從環境變數或命令列參數獲取 API 金鑰
    api_key = os.getenv('GEMINI_API_KEY')
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    # 創建應用程式
    app_instance = FuZaiPangBian(api_key=api_key)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
