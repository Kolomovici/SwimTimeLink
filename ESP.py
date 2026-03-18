#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from pynput import keyboard
import pygame
import threading
import time

# 尝试导入共享模块
try:
    import shared_functions
    SHARED_MODULE_AVAILABLE = True
    print("[DEBUG] ESP.py: 成功导入shared_functions模块")
except ImportError:
    SHARED_MODULE_AVAILABLE = False
    print("[DEBUG] ESP.py: 无法导入shared_functions模块")

# 初始化pygame混音器
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# 音效文件路径（与脚本同目录下的sounds文件夹）
SOUND_DIR = os.path.join(os.path.dirname(__file__), "sound")
SOUND_FILES = {
    '1': 'first_whistle.wav',
    '2': 'second_whistle.wav',
    '3': 'take_your_mark.wav',
    '4': 'start.wav',
    '5': 'man.wav'
}

# 加载音效112355
sounds = {}
for key, filename in SOUND_FILES.items():
    filepath = os.path.join(SOUND_DIR, filename)
    if not os.path.isfile(filepath):
        print(f"错误：找不到音效文件 {filepath}")
        sys.exit(1)
    try:
        sounds[key] = pygame.mixer.Sound(filepath)
        print(f"已加载音效：键{key} -> {filename}")
    except pygame.error as e:
        print(f"无法加载 {filename}: {e}")
        sys.exit(1)

def on_press(key):
    """键盘按下事件回调"""
    try:
        # 只处理数字键1~5
        if key.char in ('1', '2', '3', '4', '5'):
            print(f"[DEBUG] ESP.py: 检测到按键 {key.char}")
            
            # 播放对应音效（非阻塞）
            sounds[key.char].play()
            print(f"[DEBUG] ESP.py: 播放音效 {key.char}")
            
            # 如果是按键4，尝试调用app函数
            if key.char == '4':
                print(f"[DEBUG] ESP.py: 按键4按下")
                if SHARED_MODULE_AVAILABLE:
                    start_func = shared_functions.get_start_timing()
                    if start_func:
                        print(f"[DEBUG] ESP.py: 从shared_functions获取到start_timing函数")
                        # 在新线程中执行，避免阻塞音效播放
                        threading.Thread(
                            target=start_func,
                            daemon=True
                        ).start()
                    else:
                        print(f"[DEBUG] ESP.py: shared_functions中没有start_timing函数")
                else:
                    print(f"[DEBUG] ESP.py: shared_functions模块不可用")
                
            # 如果是按键5，尝试调用app函数
            elif key.char == '5':
                print(f"[DEBUG] ESP.py: 按键5按下")
                if SHARED_MODULE_AVAILABLE:
                    test_func = shared_functions.get_test_latency()
                    if test_func:
                        print(f"[DEBUG] ESP.py: 从shared_functions获取到test_latency函数")
                        # 在新线程中执行，避免阻塞音效播放
                        threading.Thread(
                            target=test_func,
                            daemon=True
                        ).start()
                    else:
                        print(f"[DEBUG] ESP.py: shared_functions中没有test_latency函数")
                else:
                    print(f"[DEBUG] ESP.py: shared_functions模块不可用")
                
    except AttributeError:
        # 非字符键（如功能键）忽略
        pass
    except Exception as e:
        print(f"[DEBUG] ESP.py: on_press函数出错: {e}")

def start_keyboard_monitoring():
    """启动键盘监听（非阻塞）"""
    try:
        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
        print("[DEBUG] ESP.py: 键盘监听已启动")
        return listener
    except Exception as e:
        print(f"[DEBUG] ESP.py: 启动键盘监听失败: {e}")
        return None

def main():
    """独立运行时的主函数"""
    print("电子发令枪已启动。")
    print("请按数字键：1(四声短哨), 2(一声长哨), 3(take your mark), 4(电笛声), 5(延迟测试)")
    print("按 Ctrl+C 退出程序。")
    
    # 启动键盘监听
    listener = start_keyboard_monitoring()
    
    if not listener:
        print("无法启动键盘监听，程序退出")
        pygame.mixer.quit()
        sys.exit(1)
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n程序退出。")
    finally:
        pygame.mixer.quit()
        sys.exit(0)

if __name__ == "__main__":
    main()