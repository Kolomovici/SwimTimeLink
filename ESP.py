#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from pynput import keyboard
import pygame
import threading
import time

# 确保使用UTF-8编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 修改计时器导入 - 使用新的计时窗口版本
try:
    from timer_window import timer, init_timer_window
    TIMER_AVAILABLE = True
    print("[DEBUG] ESP.py: 成功导入timer_window_utf8模块")
except ImportError as e:
    print(f"[DEBUG] ESP.py: 无法导入timer_window_utf8模块: {e}")
    # 尝试导入旧版本
    try:
        from timer_window import timer, init_timer_window
        TIMER_AVAILABLE = True
        print("[DEBUG] ESP.py: 成功导入timer_window模块")
    except ImportError:
        TIMER_AVAILABLE = False
        timer = None
        print("[DEBUG] ESP.py: 无法导入任何计时器模块")

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

# 加载音效
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
        # 处理数字键1~5（音效控制）
        if key.char in ('1', '2', '3', '4', '5'):
            print(f"[DEBUG] ESP.py: 检测到按键 {key.char}")
            # 播放对应音效（非阻塞）
            sounds[key.char].play()
            print(f"[DEBUG] ESP.py: 播放音效 {key.char}")
            
            # 按键3的特殊处理：计时器变红
            if key.char == '3':
                print(f"[DEBUG] ESP.py: 按键3按下 - 计时器变红")
                if TIMER_AVAILABLE and timer:
                    try:
                        timer.set_color("red")
                        print("[计时器] 颜色: 红色")
                    except Exception as e:
                        print(f"[计时器] 设置红色失败: {e}")
            
            # 按键4的特殊处理：原有的shared_functions调用
            elif key.char == '4':
                print(f"[DEBUG] ESP.py: 按键4按下")
                # 原有的shared_functions调用
                try:
                    from shared_functions import start_timing
                    start_timing()
                except ImportError:
                    print("[DEBUG] ESP.py: 无法导入start_timing函数")
            
            # 按键5的特殊处理：延迟测试
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
        
        # ==================== 计时器控制按键（独立按键） ====================
        # 按键 't' 或 'T': 计时器变红
        elif key.char in ('t', 'T'):
            if TIMER_AVAILABLE and timer:
                try:
                    timer.set_color("red")
                    print("[计时器] 颜色: 红色")
                except Exception as e:
                    print(f"[计时器] 设置红色失败: {e}")
        
        # 按键 'g' 或 'G': 计时器变绿并开始计时
        elif key.char in ('4'):
            if TIMER_AVAILABLE and timer:
                try:
                    timer.set_color("green")
                    timer.start_timer()
                    print("[计时器] 颜色: 绿色，开始计时")
                except Exception as e:
                    print(f"[计时器] 开始计时失败: {e}")
        
        # 按键 's' 或 'S': 停止计时
        elif key.char in ('s', 'S'):
            if TIMER_AVAILABLE and timer:
                try:
                    timer.stop_timer()
                    print("[计时器] 停止计时")
                except Exception as e:
                    print(f"[计时器] 停止计时失败: {e}")
        
        # 按键 'r' 或 'R': 重置计时器
        elif key.char in ('r', 'R'):
            if TIMER_AVAILABLE and timer:
                try:
                    timer.reset_timer()
                    print("[计时器] 重置计时器")
                except Exception as e:
                    print(f"[计时器] 重置失败: {e}")
        
        # 按键 'w' 或 'W': 显示/隐藏计时窗口
        elif key.char in ('w', 'W'):
            if TIMER_AVAILABLE and timer:
                try:
                    # 检查窗口状态并切换
                    if hasattr(timer, 'root') and timer.root:
                        if timer.root.state() == 'withdrawn':
                            timer.show_window()
                            print("[计时器] 显示窗口")
                        else:
                            timer.hide_window()
                            print("[计时器] 隐藏窗口")
                    else:
                        print("[计时器] 窗口未初始化")
                except Exception as e:
                    print(f"[计时器] 切换窗口失败: {e}")
        
        # 按键 'd' 或 'D': 延迟测试（独立按键）
        elif key.char in ('d', 'D'):
            print(f"[DEBUG] ESP.py: 延迟测试按键按下")
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
        
        # 按键 'x' 或 'X': 启动计时（独立按键）
        elif key.char in ('x', 'X'):
            print(f"[DEBUG] ESP.py: 启动计时按键按下")
            # 原有的shared_functions调用
            try:
                from shared_functions import start_timing
                start_timing()
            except ImportError:
                print("[DEBUG] ESP.py: 无法导入start_timing函数")
        
        # ===================================================
        
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
    # 使用全局变量
    global TIMER_AVAILABLE, timer
    
    print("="*60)
    print("电子发令枪已启动。")
    print("="*60)
    print("音效控制：")
    print("  1 - 四声短哨")
    print("  2 - 一声长哨")
    print("  3 - take your mark (同时计时器变红)")
    print("  4 - 电笛声 (同时启动计时)")
    print("  5 - 延迟测试")
    
    print("\n计时器控制：")
    print("  t/T - 计时器变红")
    print("  g/G - 计时器变绿并开始计时")
    print("  s/S - 停止计时")
    print("  r/R - 重置计时器")
    print("  w/W - 显示/隐藏计时窗口")
    print("  d/D - 延迟测试 (独立按键)")
    print("  x/X - 启动计时 (独立按键)")
    
    print("\n按 Ctrl+C 退出程序。")
    print("="*60)
    
    # 启动计时窗口
    if TIMER_AVAILABLE:
        print("初始化计时窗口...")
        try:
            success = init_timer_window()
            if success:
                print("计时窗口初始化成功")
                # 等待窗口完全显示
                time.sleep(0.5)
                print("计时窗口已就绪")
            else:
                print("计时窗口初始化失败")
                TIMER_AVAILABLE = False
        except Exception as e:
            print(f"初始化计时窗口失败: {e}")
            TIMER_AVAILABLE = False
    else:
        print("计时器功能不可用")
    
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