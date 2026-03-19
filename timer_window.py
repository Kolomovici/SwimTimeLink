# -*- coding: utf-8 -*-
"""
计时窗口 - UTF-8编码版本
"""
import tkinter as tk
from tkinter import font
import threading
import time
import sys

# 确保使用UTF-8编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

class TimerWindow:
    def __init__(self):
        print("[DEBUG] TimerWindow初始化开始")
        self.root = None
        self.timer_label = None
        self.running = False
        self.start_time = 0
        self.window_ready = threading.Event()
        self.thread = None
        
    def _create_window(self):
        """在独立线程中创建窗口"""
        try:
            print("[DEBUG] 开始创建Tkinter窗口...")
            self.root = tk.Tk()
            print("[DEBUG] Tkinter根窗口创建成功")
            
            self.root.title("ESP Timer")
            self.root.geometry("400x200+100+100")
            self.root.configure(bg='black')
            self.root.attributes('-topmost', True)
            
            # 设置协议，关闭窗口时隐藏而不是销毁
            self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
            
            custom_font = font.Font(family="Courier", size=48, weight="bold")
            
            self.timer_label = tk.Label(
                self.root,
                text="00:00:000",
                font=custom_font,
                fg="white",
                bg="black"
            )
            self.timer_label.pack(expand=True, fill='both')
            
            print("[DEBUG] 窗口组件创建完成")
            self.window_ready.set()  # 标记窗口就绪
            
            # 启动Tkinter主循环
            print("[DEBUG] 启动Tkinter主循环")
            self.root.mainloop()
            print("[DEBUG] Tkinter主循环结束")
            
        except Exception as e:
            print(f"[ERROR] 创建窗口失败: {e}")
            import traceback
            traceback.print_exc()
            self.window_ready.set()  # 即使失败也设置事件，避免死锁
    
    def start(self):
        """启动计时窗口"""
        print("[DEBUG] 启动计时窗口线程")
        self.thread = threading.Thread(target=self._create_window, daemon=True)
        self.thread.start()
        
        # 等待窗口初始化完成
        if self.window_ready.wait(timeout=5):
            print("[DEBUG] 窗口初始化完成")
            # 短暂延迟确保窗口完全创建
            time.sleep(0.5)
            return True
        else:
            print("[ERROR] 窗口初始化超时")
            return False
    
    def show_window(self):
        """显示窗口"""
        if self.root and self.window_ready.is_set():
            print("[DEBUG] 显示窗口")
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            return True
        return False
    
    def hide_window(self):
        """隐藏窗口"""
        if self.root:
            print("[DEBUG] 隐藏窗口")
            self.root.withdraw()
            return True
        return False
    
    def set_color(self, color):
        """设置颜色"""
        if self.timer_label and self.window_ready.is_set():
            self.root.after(0, lambda: self.timer_label.config(fg=color))
            print(f"[DEBUG] 设置颜色为: {color}")
            return True
        return False
    
    def start_timer(self):
        """开始计时"""
        if not self.running and self.window_ready.is_set():
            print("[DEBUG] 开始计时")
            self.running = True
            self.start_time = time.time()
            self._update_timer()
            return True
        return False
    
    def _update_timer(self):
        """更新计时器显示"""
        if self.running and self.timer_label:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            milliseconds = int((elapsed % 1) * 1000)
            
            time_str = f"{minutes:02d}:{seconds:02d}:{milliseconds:03d}"
            
            # 在主线程中更新UI
            if self.root:
                self.root.after(0, lambda t=time_str: self.timer_label.config(text=t))
            
            # 安排下一次更新
            if self.running:
                self.root.after(10, self._update_timer)
    
    def stop_timer(self):
        """停止计时"""
        print("[DEBUG] 停止计时")
        self.running = False
    
    def reset_timer(self):
        """重置计时器"""
        print("[DEBUG] 重置计时器")
        self.running = False
        if self.timer_label and self.window_ready.is_set():
            self.root.after(0, lambda: self.timer_label.config(text="00:00:000"))

# 全局实例
timer = TimerWindow()

def init_timer_window():
    """初始化计时窗口"""
    print("初始化计时窗口...")
    success = timer.start()
    if success:
        print("计时窗口初始化成功")
        # 显示窗口
        timer.show_window()
    else:
        print("计时窗口初始化失败")
    return success