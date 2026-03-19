#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from pynput import keyboard
import pygame
import threading
import time
import json
import paho.mqtt.client as mqtt

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

# ==================== 设备管理类 ====================
class DeviceManager:
    def __init__(self):
        self.devices = {}  # 设备ID -> MQTT客户端
        self.broker = "localhost"
        self.port = 1883
        
    def add_device(self, device_id):
        """添加设备"""
        if device_id in self.devices:
            print(f"[设备管理] 设备 {device_id} 已存在")
            return False
            
        try:
            client = mqtt.Client(client_id=device_id)
            client.connect(self.broker, self.port, 60)
            client.loop_start()
            self.devices[device_id] = client
            print(f"[设备管理] 设备 {device_id} 已添加并连接到MQTT代理")
            return True
        except Exception as e:
            print(f"[设备管理] 添加设备 {device_id} 失败: {e}")
            return False
    
    def remove_device(self, device_id):
        """移除设备"""
        if device_id in self.devices:
            try:
                self.devices[device_id].loop_stop()
                self.devices[device_id].disconnect()
                del self.devices[device_id]
                print(f"[设备管理] 设备 {device_id} 已移除")
                return True
            except Exception as e:
                print(f"[设备管理] 移除设备 {device_id} 失败: {e}")
                return False
        else:
            print(f"[设备管理] 设备 {device_id} 不存在")
            return False
    
    def send_command_to_device(self, device_id, command, data=None):
        """向单个设备发送命令"""
        if device_id in self.devices:
            try:
                topic = f"devices/{device_id}/control"
                message = {"command": command}
                if data:
                    message["data"] = data
                
                self.devices[device_id].publish(topic, json.dumps(message))
                print(f"[设备管理] 向设备 {device_id} 发送命令: {command}")
                return True
            except Exception as e:
                print(f"[设备管理] 发送命令到设备 {device_id} 失败: {e}")
                return False
        else:
            print(f"[设备管理] 设备 {device_id} 不存在")
            return False
    
    def send_command_to_all(self, command, data=None):
        """向所有设备发送命令"""
        if not self.devices:
            print("[设备管理] 没有设备可控制")
            return False
            
        success_count = 0
        for device_id in list(self.devices.keys()):
            if self.send_command_to_device(device_id, command, data):
                success_count += 1
        
        print(f"[设备管理] 向 {len(self.devices)} 个设备发送命令，成功: {success_count}")
        return success_count > 0
    
    def list_devices(self):
        """列出所有设备"""
        if not self.devices:
            print("[设备管理] 当前没有设备")
            return []
        
        device_list = list(self.devices.keys())
        print(f"[设备管理] 当前设备: {', '.join(device_list)}")
        return device_list
    
    def cleanup(self):
        """清理所有设备连接"""
        for device_id in list(self.devices.keys()):
            self.remove_device(device_id)
        print("[设备管理] 所有设备连接已清理")

# 全局设备管理器
device_manager = DeviceManager()

def start_timer_sync():
    """同步启动计时器"""
    if TIMER_AVAILABLE and timer:
        try:
            # 先变绿
            timer.set_color("green")
            print("[计时器] 颜色: 绿色")
            
            # 立即开始计时
            timer.start_timer()
            print("[计时器] 开始计时")
            
            return True
        except Exception as e:
            print(f"[计时器] 启动失败: {e}")
            return False
    return False

def on_press(key):
    """键盘按下事件回调"""
    try:
        # 处理数字键1~5（音效控制）
        if key.char in ('1', '2', '3', '4', '5'):
            print(f"[DEBUG] ESP.py: 检测到按键 {key.char}")
            
            # 按键1：四声短哨
            if key.char == '1':
                sounds[key.char].play()
                print(f"[DEBUG] ESP.py: 播放音效 {key.char}")
                return
            
            # 按键2：一声长哨
            elif key.char == '2':
                sounds[key.char].play()
                print(f"[DEBUG] ESP.py: 播放音效 {key.char}")
                return
            
            # 按键3：take your mark + 计时器变红
            elif key.char == '3':
                # 播放音效
                sounds[key.char].play()
                print(f"[DEBUG] ESP.py: 播放音效 {key.char}")
                
                # 计时器变红
                if TIMER_AVAILABLE and timer:
                    try:
                        timer.set_color("red")
                        print("[计时器] 颜色: 红色")
                    except Exception as e:
                        print(f"[计时器] 设置红色失败: {e}")
                return
            
            # 按键4：电笛声 + 启动计时 + 所有设备开始计时
            elif key.char == '4':
                print(f"[DEBUG] ESP.py: 按键4按下 - 启动计时")
                
                # 1. 播放音效
                sounds[key.char].play()
                print(f"[DEBUG] ESP.py: 播放音效 {key.char}")
                
                # 2. 启动本地计时器（同步）
                if start_timer_sync():
                    print("[计时器] 按键4: 本地计时器已启动")
                else:
                    print("[计时器] 按键4: 本地计时器启动失败")
                
                # 3. 向所有设备发送开始计时命令
                print("[设备管理] 向所有设备发送开始计时命令...")
                device_manager.send_command_to_all("start_timer")
                
                # 4. 原有的shared_functions调用
                try:
                    from shared_functions import start_timing
                    start_timing()
                    print("[shared_functions] start_timing已调用")
                except ImportError:
                    print("[DEBUG] ESP.py: 无法导入start_timing函数")
                except Exception as e:
                    print(f"[shared_functions] 调用失败: {e}")
                
                return
            
            # 按键5：延迟测试 + 所有设备延迟检测
            elif key.char == '5':
                print(f"[DEBUG] ESP.py: 按键5按下 - 延迟测试")
                
                # 1. 播放音效
                sounds[key.char].play()
                print(f"[DEBUG] ESP.py: 播放音效 {key.char}")
                
                # 2. 向所有设备发送延迟测试命令
                print("[设备管理] 向所有设备发送延迟测试命令...")
                device_manager.send_command_to_all("start_delay_test")
                
                # 3. 原有的延迟测试
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
                
                return
        
        # ==================== 设备管理按键 ====================
        # 按键 'a' 或 'A': 添加设备
        elif key.char in ('a', 'A'):
            device_id = input("\n[设备管理] 请输入设备ID: ").strip()
            if device_id:
                device_manager.add_device(device_id)
        
        # 按键 'l' 或 'L': 列出设备
        elif key.char in ('l', 'L'):
            device_manager.list_devices()
        
        # 按键 'r' 或 'R': 移除设备
        elif key.char in ('r', 'R'):
            device_id = input("\n[设备管理] 请输入要移除的设备ID: ").strip()
            if device_id:
                device_manager.remove_device(device_id)
        
        # ==================== 计时器控制按键 ====================
        # 按键 't' 或 'T': 计时器变红
        elif key.char in ('t', 'T'):
            if TIMER_AVAILABLE and timer:
                try:
                    timer.set_color("red")
                    print("[计时器] 颜色: 红色")
                except Exception as e:
                    print(f"[计时器] 设置红色失败: {e}")
        
        # 按键 'g' 或 'G': 计时器变绿并开始计时
        elif key.char in ('g', 'G'):
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
        
        # 按键 'z' 或 'Z': 重置计时器
        elif key.char in ('z', 'Z'):
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
            # 启动计时器
            if start_timer_sync():
                print("[计时器] 按键X: 计时器已启动")
            else:
                print("[计时器] 按键X: 计时器启动失败")
            
            # 原有的shared_functions调用
            try:
                from shared_functions import start_timing
                start_timing()
                print("[shared_functions] start_timing已调用")
            except ImportError:
                print("[DEBUG] ESP.py: 无法导入start_timing函数")
            except Exception as e:
                print(f"[shared_functions] 调用失败: {e}")
        
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
    print("  3 - take your mark (计时器变红)")
    print("  4 - 电笛声 (启动计时 + 所有设备开始计时)")
    print("  5 - 延迟测试 (所有设备延迟检测)")
    
    print("\n设备管理：")
    print("  a/A - 添加设备")
    print("  l/L - 列出设备")
    print("  r/R - 移除设备")
    
    print("\n计时器控制：")
    print("  t/T - 计时器变红")
    print("  g/G - 计时器变绿并开始计时")
    print("  s/S - 停止计时")
    print("  z/Z - 重置计时器")
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
        # 清理设备连接
        device_manager.cleanup()
    finally:
        pygame.mixer.quit()
        sys.exit(0)

if __name__ == "__main__":
    main()