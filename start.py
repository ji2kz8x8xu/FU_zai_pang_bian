#!/usr/bin/env python3
"""
福在旁邊 - 快速啟動腳本
提供友善的啟動介面和配置選項
"""

import sys
import os
from pathlib import Path


def check_dependencies():
    """檢查必要的依賴套件"""
    missing_packages = []
    
    try:
        import PyQt6
    except ImportError:
        missing_packages.append('PyQt6')
    
    try:
        import google.generativeai
    except ImportError:
        missing_packages.append('google-generativeai')
    
    try:
        import speech_recognition
    except ImportError:
        missing_packages.append('SpeechRecognition')
    
    try:
        import sounddevice
    except ImportError:
        missing_packages.append('sounddevice')
    
    if missing_packages:
        print("❌ 缺少以下套件:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n請執行以下命令安裝:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True


def check_api_key():
    """檢查 API 金鑰配置"""
    # api_key = os.getenv('GEMINI_API_KEY')
    
    # if not api_key:
    #     print("⚠️  未設定 GEMINI_API_KEY")
    #     print("\n有兩種方式設定 API 金鑰:")
    #     print("1. 環境變數:")
    #     print("   export GEMINI_API_KEY='your_api_key_here'")
    #     print("\n2. 命令列參數:")
    #     print("   python start.py YOUR_API_KEY")
    #     print("\n繼續執行將無法使用 AI 聊天功能。")
        
    #     response = input("\n是否仍要繼續？(y/n): ")
    #     if response.lower() != 'y':
    #         return False
    # else:
    #     print("✅ 已偵測到 API 金鑰")
    
    return True


def print_welcome():
    """顯示歡迎訊息"""
    print("""
╔══════════════════════════════════════════╗
║                                          ║
║         福在旁邊 AI 助手 v1.0             ║
║     Desktop Floating AI Assistant        ║
║                                          ║
╚══════════════════════════════════════════╝

✨ 特色功能:
  🎯 水滴吸附動畫
  🤖 AI 聊天 (Gemini)
  🎤 語音輸入
  🎨 毛玻璃設計

正在啟動...
""")


def main():
    """主啟動函數"""
    print_welcome()
    
    # 檢查依賴
    print("📦 檢查依賴套件...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ 所有依賴套件已就緒\n")
    
    # 檢查 API 金鑰
    print("🔑 檢查 API 金鑰...")
    if not check_api_key():
        sys.exit(1)
    print()
    
    # 匯入主程式
    try:
        from main import main as run_app
        print("🚀 啟動應用程式...\n")
        run_app()
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()