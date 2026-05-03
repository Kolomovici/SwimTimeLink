#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP.py - 电子发令枪（后端统一时序中枢版）

修改要点：
1. 添加 WebSocket 客户端连接到 Flask 后端
2. 按键4不再独立计时而是通过 HTTP 通知后端记录发令时间
3. 新增 fire_race() 函数，封装完整发令逻辑
4. 新增 WebSocket 事件监听：
   - esp_start_race: 接收裁判长的发令指令，自动执行发令流程
   - esp_reset: 接收重置指令
5. 按键4改为手动紧急发令直接触发完整发令流程
"""

import os
import sys
from pynput import keyboard
import pygame
import threading
import time
import json

# 确保使用UTF-8编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 修改计时器导入
try:
    from timer_window import timer, init_timer_window
    TIMER_AVAILABLE = True
    print("[DEBUG] ESP.py: 成功导入timer_window模块")
except ImportError as e:
    print(f"[DEBUG] ESP.py: 无法导入timer_window模块: {e}")
    TIMER_AVAILABLE = False
    timer = None

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

# ==================== Flask后端通信配置 ====================
FLASK_URL = "http://localhost:5000"
FLASK_WS_URL = "http://localhost:5000"

# WebSocket客户端（连接Flask后端）
flask_sio = None

def connect_flask_websocket():
    """连接到Flask后端的WebSocket"""
    global flask_sio
    try:
        import socketio as ws_client
        flask_sio = ws_client.Client()
        
        @flask_sio.event
        def connect():
            print("[ESP-WS] 已连接到Flask后端")
        
        @flask_sio.event
        def disconnect():
            print("[ESP-WS] 与Flask后端断开连接")
        
        @flask_sio.on('esp_start_race')
        def on_esp_start_race(data):
            """接收裁判长发令指令 → 自动执行发令流程"""
            print(f"[ESP-WS] 收到发令指令: {data}")
            project_name = data.get('project_name', '游泳比赛')
            segments = data.get('segments', 1)
            
            # 在新线程中执行发令流程（避免阻塞WebSocket）
            threading.Thread(
                target=auto_fire_sequence,
                args=(project_name, segments),
                daemon=True
            ).start()
        
        @flask_sio.on('esp_reset')
        def on_esp_reset(data):
            """接收重置指令"""
            print(f"[ESP-WS] 收到重置指令: {data}")
            # 重置计时器
            if TIMER_AVAILABLE and timer:
                try:
                    timer.reset_timer()
                    timer.set_color("white")
                    print("[ESP] 计时器已重置")
                except Exception as e:
                    print(f"[ESP] 重置计时器失败: {e}")
        
        flask_sio.connect(FLASK_WS_URL, transports=['websocket', 'polling'])
        print("[ESP-WS] WebSocket连接已建立")
        return True
    except ImportError:
        print("[ESP-WS] 无法导入socketio客户端库，WebSocket功能不可用")
        print("[ESP-WS] 请运行: pip install python-socketio[client]")
        return False
    except Exception as e:
        print(f"[ESP-WS] 连接Flask后端失败: {e}")
        print(f"[ESP-WS] 将使用独立模式运行（按键4为手动发令）")
        return False


def notify_backend_fire(project_name, segments):
    """通知后端记录发令时间（POST /esp_fire）"""
    try:
        import urllib.request
        req_data = json.dumps({
            "project_name": project_name,
            "segments": segments
        }).encode('utf-8')
        req = urllib.request.Request(
            f'{FLASK_URL}/esp_fire',
            data=req_data,
            headers={'Content-Type': 'application/json'}
        )
        resp = urllib.request.urlopen(req, timeout=5)
        result = json.loads(resp.read())
        server_start_time = result.get('start_time')
        print(f"[ESP] 后端已记录发令时间: {server_start_time}")
        return server_start_time
    except Exception as e:
        print(f"[ESP] 通知后端失败: {e}")
        return None


def auto_fire_sequence(project_name, segments):
    """
    自动发令流程（由裁判长触发）
    1. 播放 take your mark
    2. 计时器变红
    3. 等待约1.5秒
    4. 播放电笛声
    5. 通知后端记录发令时间
    6. 启动本地计时器
    7. 通知MQTT设备
    """
    print(f"[ESP] 开始自动发令流程: {project_name}")
    
    # 1. 播放 take your mark
    print("[ESP] 播放: take your mark")
    sounds['3'].play()
    
    # 2. 计时器变红
    if TIMER_AVAILABLE and timer:
        try:
            timer.set_color("red")
            print("[ESP] 计时器: 红色（准备）")
        except Exception as e:
            print(f"[ESP] 计时器设置红色失败: {e}")
    
    # 广播给裁判长：ESP状态更新
    if flask_sio and flask_sio.connected:
        flask_sio.emit('esp_status', {
            "stage": "take_your_mark",
            "timestamp": int(time.time() * 1000),
            "project_name": project_name
        })
    
    # 3. 等待约1.5秒（模拟裁判反应时间）
    time.sleep(1.5)
    
    # 4. 执行发令
    fire_race(project_name, segments)


def fire_race(project_name, segments):
    """
    真正的发令执行（电笛声 + 通知后端 + 启动计时器 + MQTT）
    可由裁判长触发（auto_fire_sequence）或手动按键4触发
    """
    print(f"[ESP] === 执行发令 === 项目: {project_name}")
    
    # 1. 播放电笛声
    sounds['4'].play()
    print("[ESP] 播放: 电笛声")
    
    # 2. 通知后端记录发令时间（这是真正的发令时刻）
    server_start_time = notify_backend_fire(project_name, segments)
    
    # 3. 启动本地计时器
    if TIMER_AVAILABLE and timer:
        try:
            timer.set_color("green")
            timer.start_timer()
            print("[ESP] 计时器: 绿色，开始计时")
        except Exception as e:
            print(f"[ESP] 计时器启动失败: {e}")
    
    # 4. 通知MQTT设备
    device_manager.send_command_to_all("start_timer", {
        "server_start_time": server_start_time or int(time.time() * 1000)
    })
    
    # 5. 广播给裁判长：ESP已完成发令
    if flask_sio and flask_sio.connected:
        flask_sio.emit('esp_status', {
            "stage": "fired",
            "timestamp": int(time.time() * 1000),
            "project_name": project_name,
            "start_time": server_start_time
        })
    
    print(f"[ESP] === 发令完成 === {project_name}")


# ==================== 设备管理类 ====================
class DeviceManager:
    def __init__(self):
        self.devices = {}  # 设备ID -> MQTT客户端
        self.broker = "localhost"
        self.port = 1883
        
    def get_mqtt_client(self):
        """按需获取 MQTT 客户端模块"""
        try:
            import paho.mqtt.client as mqtt_mod
            return mqtt_mod
        except ImportError:
            print("[设备管理] 错误: 未安装 paho-mqtt 库，无法使用 MQTT 功能")
            print("[设备管理] 请运行: pip install paho-mqtt")
            return None

    def add_device(self, device_id):
        """添加设备"""
        if device_id in self.devices:
            print(f"[设备管理] 设备 {device_id} 已存在")
            return False
            
        mqtt_mod = self.get_mqtt_client()
        if not mqtt_mod:
            return False

        try:
            client = mqtt_mod.Client(client_id=device_id)
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
                
                # 广播给裁判长：准备就绪
                if flask_sio and flask_sio.connected:
                    flask_sio.emit('esp_status', {
                        "stage": "take_your_mark",
                        "timestamp": int(time.time() * 1000)
                    })
                return
            
            # 按键4：手动紧急发令（直接触发完整发令流程）
            elif key.char == '4':
                print(f"[DEBUG] ESP.py: 按键4 - 手动紧急发令")
                # 在新线程中执行，避免阻塞键盘监听
                threading.Thread(
                    target=fire_race,
                    args=("手动发令", 1),
                    daemon=True
                ).start()
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
                    threading.Thread(
                        target=test_func,
                        daemon=True
                    ).start()
                else:
                    print(f"[DEBUG] ESP.py: shared_functions中没有test_latency函数")
            else:
                print(f"[DEBUG] ESP.py: shared_functions模块不可用")
        
        # 按键 'x' 或 'X': 启动计时（独立按键，仅本地）
        elif key.char in ('x', 'X'):
            print(f"[DEBUG] ESP.py: 启动计时按键按下")
            if start_timer_sync():
                print("[计时器] 按键X: 计时器已启动")
            else:
                print("[计时器] 按键X: 计时器启动失败")
            
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


def start_timer_sync():
    """同步启动计时器（仅本地）"""
    if TIMER_AVAILABLE and timer:
        try:
            timer.set_color("green")
            timer.start_timer()
            print("[计时器] 开始计时")
            return True
        except Exception as e:
            print(f"[计时器] 启动失败: {e}")
            return False
    return False


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
    global TIMER_AVAILABLE, timer
    
    print("="*60)
    print("电子发令枪 - 后端统一时序中枢版")
    print("="*60)
    print("音效控制：")
    print("  1 - 四声短哨")
    print("  2 - 一声长哨")
    print("  3 - take your mark (计时器变红 + 通知后端)")
    print("  4 - 紧急手动发令 (直接电笛声 + 通知后端)")
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
    print("  x/X - 本地启动计时 (独立按键)")
    
    print("\n发令流程说明：")
    print("  [自动模式] 裁判长点击发令 → ESP自动播放take your mark")
    print("            → 等待1.5秒 → 电笛声 → 通知后端记录时间")
    print("  [手动模式] 按4直接发令（紧急情况使用）")
    
    print("\n按 Ctrl+C 退出程序。")
    print("="*60)
    
    # 连接到Flask后端WebSocket
    print("\n[初始化] 正在连接Flask后端...")
    ws_connected = connect_flask_websocket()
    if ws_connected:
        print("[初始化] Flask后端连接成功")
    else:
        print("[初始化] Flask后端连接失败，将使用独立模式")
    
    # 启动计时窗口
    if TIMER_AVAILABLE:
        print("初始化计时窗口...")
        try:
            success = init_timer_window()
            if success:
                print("计时窗口初始化成功")
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
        device_manager.cleanup()
        if flask_sio and flask_sio.connected:
            flask_sio.disconnect()
    finally:
        pygame.mixer.quit()
        sys.exit(0)

if __name__ == "__main__":
    main()
