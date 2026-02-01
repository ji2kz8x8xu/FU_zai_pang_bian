"""
主互動面板 (含離開程式功能版)
新增：標題列的電源按鈕，可完全關閉程式
"""

import sys
import os
import google.generativeai as genai
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                              QPushButton, QScrollArea, QLabel, QFrame, QSizeGrip,
                              QApplication) # [新增] QApplication
from PyQt6.QtCore import (Qt, QPropertyAnimation, QPoint, pyqtSignal, 
                          QTimer, QThread, QSize)
from PyQt6.QtGui import QPainter, QColor, QPainterPath
from dotenv import load_dotenv

# 1. 載入 .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# 初始化 Gemini
model = None
if not API_KEY:
    print("❌ 錯誤：找不到 API Key！")
elif "AIza" not in API_KEY:
    print("❌ 警告：API Key 格式錯誤。")
else:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash') 
        print("✅ Gemini 初始化成功！")
    except Exception as e:
        print(f"API 設定錯誤: {e}")

class AIWorker(QThread):
    """後台 AI 執行緒"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, user_text):
        super().__init__()
        self.user_text = user_text

    def run(self):
        if not model:
            self.error.emit("❌ API Key 無效，請檢查 .env 設定。")
            return
        try:
            response = model.generate_content(self.user_text)
            if response.text:
                self.finished.emit(response.text)
            else:
                self.error.emit("⚠️ AI 回傳了空訊息")
        except Exception as e:
            self.error.emit(f"❌ 連線錯誤: {str(e)}")

class ChatMessage(QFrame):
    """聊天氣泡"""
    def __init__(self, text, is_user=True):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        label = QLabel(text)
        label.setWordWrap(True)
        label.setMaximumWidth(260)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        bg = '#dcf8c6' if is_user else '#ffffff'
        
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: black;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 14px;
            }}
        """)
        
        if is_user:
            layout.addStretch()
            layout.addWidget(label)
        else:
            layout.addWidget(label)
            layout.addStretch()
            
        self.setLayout(layout)

class FloatingPanel(QWidget):
    """主聊天視窗"""
    def __init__(self, parent_ball):
        super().__init__()
        self.parent_ball = parent_ball
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.resize(350, 500)
        self.setMinimumSize(300, 400)
        
        self.init_ui()
        
    def init_ui(self):
        # 1. 主佈局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 2. 內容容器
        self.container = QWidget()
        self.container.setObjectName("Container")
        self.container.setStyleSheet("""
            QWidget#Container {
                background-color: rgba(245, 245, 245, 245);
                border: 1px solid #ccc;
                border-radius: 15px;
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- 3. [修改] 標題列 (增加離開按鈕) ---
        header = QHBoxLayout()
        title = QLabel("福在旁邊 AI")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #555;")
        
        # [新功能] 完全離開程式按鈕 (電源圖示)
        exit_btn = QPushButton("⏻") 
        exit_btn.setFixedSize(25, 25)
        exit_btn.setToolTip("完全結束程式")
        # 按下後呼叫 QApplication.instance().quit() 來關閉整個 APP
        exit_btn.clicked.connect(QApplication.instance().quit)
        exit_btn.setStyleSheet("""
            QPushButton { border: none; font-size: 16px; color: #aaa; }
            QPushButton:hover { color: #d9534f; font-weight: bold; }
        """)

        # 原本的關閉(隱藏)按鈕
        close_btn = QPushButton("×")
        close_btn.setFixedSize(25, 25)
        close_btn.setToolTip("隱藏視窗 (程式繼續執行)")
        close_btn.clicked.connect(self.hide_panel)
        close_btn.setStyleSheet("""
            QPushButton { border: none; font-size: 20px; color: #888; }
            QPushButton:hover { color: #555; }
        """)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(exit_btn)  # 先放離開
        header.addWidget(close_btn) # 再放隱藏
        container_layout.addLayout(header)
        
        # 4. 聊天捲動區
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.chat_widget)
        container_layout.addWidget(self.scroll_area)
        
        # 5. 輸入區
        input_box = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("輸入訊息...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 15px;
                padding: 5px 10px;
                background: white;
            }
        """)
        
        send_btn = QPushButton("送出")
        send_btn.clicked.connect(self.send_message)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff; color: white;
                border-radius: 15px; padding: 5px 15px;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        
        input_box.addWidget(self.input_field)
        input_box.addWidget(send_btn)
        container_layout.addLayout(input_box)
        
        self.main_layout.addWidget(self.container)
        
        # 6. 右下角調整大小的手柄
        self.sizegrip = QSizeGrip(self)
        self.sizegrip.setStyleSheet("width: 15px; height: 15px; background: transparent;")
        
    def resizeEvent(self, event):
        if hasattr(self, 'sizegrip'):
            self.sizegrip.move(self.width() - 15, self.height() - 15)
        super().resizeEvent(event)

    def show_panel(self):
        """顯示面板並定位"""
        self.show()
        # 第一次顯示時若父物件存在，進行定位
        if self.parent_ball:
            self.follow_ball(self.parent_ball.pos())
        self.raise_()
        self.activateWindow()
        self.input_field.setFocus()
        
    def hide_panel(self):
        self.hide()
        
    def follow_ball(self, ball_pos):
        """簡單跟隨邏輯，主程式的 toggle_panel 會覆蓋這裡的定位，但保留它是為了 resize 時不跑掉"""
        screen = self.screen().geometry()
        x = ball_pos.x() - self.width() - 10
        if x < 0: x = ball_pos.x() + 60 + 10
        
        y = ball_pos.y()
        if y + self.height() > screen.height():
            y = screen.height() - self.height() - 10
            
        self.move(int(x), int(y))

    def send_message(self):
        text = self.input_field.text().strip()
        if not text: return
        
        self.add_message(text, True)
        self.input_field.clear()
        self.input_field.setPlaceholderText("思考中...")
        self.input_field.setDisabled(True)
        
        self.worker = AIWorker(text)
        self.worker.finished.connect(self.on_reply)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        
    def on_reply(self, text):
        self.add_message(text, False)
        self.reset_input()
        
    def on_error(self, text):
        self.add_message(text, False)
        self.reset_input()
        
    def reset_input(self):
        self.input_field.setDisabled(False)
        self.input_field.setPlaceholderText("輸入訊息...")
        self.input_field.setFocus()
        
    def add_message(self, text, is_user):
        self.chat_layout.addWidget(ChatMessage(text, is_user))
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))