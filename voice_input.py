"""
語音輸入模組 - 語音轉文字 (Speech-to-Text)
使用 Google Speech Recognition API
"""

import speech_recognition as sr
from PyQt6.QtCore import QThread, pyqtSignal
import sounddevice as sd
import numpy as np
import wave
import tempfile
import os


class VoiceRecorder(QThread):
    """語音錄製執行緒"""
    
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    transcription_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.recognizer = sr.Recognizer()
        self.audio_data = []
        self.sample_rate = 16000
        
    def start_recording(self):
        """開始錄音"""
        self.is_recording = True
        self.audio_data = []
        self.start()
    
    def stop_recording(self):
        """停止錄音"""
        self.is_recording = False
    
    def run(self):
        """執行錄音"""
        try:
            self.recording_started.emit()
            
            # 使用 sounddevice 錄音
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16') as stream:
                while self.is_recording:
                    audio_chunk, _ = stream.read(1024)
                    self.audio_data.append(audio_chunk)
            
            self.recording_stopped.emit()
            
            # 轉換為文字
            self.transcribe_audio()
            
        except Exception as e:
            self.error_occurred.emit(f"錄音錯誤: {str(e)}")
    
    def transcribe_audio(self):
        """將錄音轉換為文字"""
        try:
            if not self.audio_data:
                self.error_occurred.emit("沒有錄音數據")
                return
            
            # 合併音訊數據
            audio_array = np.concatenate(self.audio_data, axis=0)
            
            # 儲存為臨時 WAV 檔案
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_filename = temp_file.name
            temp_file.close()
            
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_array.tobytes())
            
            # 使用 Google Speech Recognition
            with sr.AudioFile(temp_filename) as source:
                audio = self.recognizer.record(source)
                
                # 嘗試識別（支援中文）
                try:
                    text = self.recognizer.recognize_google(audio, language='zh-TW')
                    self.transcription_ready.emit(text)
                except sr.UnknownValueError:
                    self.error_occurred.emit("無法識別語音內容")
                except sr.RequestError as e:
                    self.error_occurred.emit(f"無法連接到語音識別服務: {str(e)}")
            
            # 刪除臨時檔案
            os.unlink(temp_filename)
            
        except Exception as e:
            self.error_occurred.emit(f"轉換錯誤: {str(e)}")


class VoiceInput:
    """語音輸入管理器"""
    
    def __init__(self):
        self.recorder = VoiceRecorder()
        self.is_recording = False
    
    def toggle_recording(self, on_transcription=None, on_error=None, on_start=None, on_stop=None):
        """
        切換錄音狀態
        
        Args:
            on_transcription: 轉錄完成時的回調函數
            on_error: 錯誤時的回調函數
            on_start: 開始錄音時的回調函數
            on_stop: 停止錄音時的回調函數
        """
        if self.is_recording:
            # 停止錄音
            self.recorder.stop_recording()
            self.is_recording = False
        else:
            # 開始錄音
            # 連接訊號
            if on_transcription:
                self.recorder.transcription_ready.connect(on_transcription)
            if on_error:
                self.recorder.error_occurred.connect(on_error)
            if on_start:
                self.recorder.recording_started.connect(on_start)
            if on_stop:
                self.recorder.recording_stopped.connect(on_stop)
            
            self.recorder.start_recording()
            self.is_recording = True
        
        return self.is_recording
    
    def is_currently_recording(self):
        """檢查是否正在錄音"""
        return self.is_recording


# 使用範例
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
    
    class TestWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.voice_input = VoiceInput()
            
            layout = QVBoxLayout()
            
            self.status_label = QLabel("準備就緒")
            layout.addWidget(self.status_label)
            
            self.result_label = QLabel("")
            self.result_label.setWordWrap(True)
            layout.addWidget(self.result_label)
            
            btn = QPushButton("按住錄音")
            btn.clicked.connect(self.toggle_recording)
            layout.addWidget(btn)
            
            self.setLayout(layout)
            self.setWindowTitle("語音輸入測試")
            self.resize(400, 200)
        
        def toggle_recording(self):
            is_recording = self.voice_input.toggle_recording(
                on_transcription=self.on_text,
                on_error=self.on_error,
                on_start=lambda: self.status_label.setText("🎤 錄音中..."),
                on_stop=lambda: self.status_label.setText("處理中...")
            )
            
            if is_recording:
                self.status_label.setText("🎤 錄音中...")
            else:
                self.status_label.setText("處理中...")
        
        def on_text(self, text):
            self.result_label.setText(f"識別結果: {text}")
            self.status_label.setText("完成！")
        
        def on_error(self, error):
            self.result_label.setText(f"錯誤: {error}")
            self.status_label.setText("發生錯誤")
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
