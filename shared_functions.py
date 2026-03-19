"""
共享函数模块，用于在不同模块间传递函数引用
"""

# 全局变量存储函数引用
_registered_functions = {
    'start_timing': None,
    'test_latency': None,
    'stop_timing': None
}

def register_functions(start_timing_func, test_latency_func, stop_timing_func):
    """注册函数到共享模块"""
    global _registered_functions
    _registered_functions['start_timing'] = start_timing_func
    _registered_functions['test_latency'] = test_latency_func
    _registered_functions['stop_timing'] = stop_timing_func
    print(f"[DEBUG] shared_functions: 函数已注册")

def start_timing():
    """开始计时功能"""
    print("[INFO] 计时功能启动")
    # 这里可以添加实际的计时逻辑
    # 例如：记录开始时间
    start_time = time.time()
    print(f"[TIMER] 开始时间: {start_time}")
    return start_time


def test_latency():
    """测试延迟功能"""
    print("[INFO] 开始延迟测试")
    
    # 简单的延迟测试逻辑
    test_start = time.time()
    
    # 模拟一些操作
    for i in range(1000):
        pass  # 空操作测试
    
    test_end = time.time()
    latency = (test_end - test_start) * 1000  # 转换为毫秒
    
    print(f"[LATENCY] 延迟测试完成: {latency:.3f} ms")
    return latency

def get_stop_timing():
    """获取停止计时函数"""
    return _registered_functions['stop_timing']

def is_functions_registered():
    """检查函数是否已注册"""
    return all(func is not None for func in _registered_functions.values())

import time

class TimerManager:
    """计时器管理器"""
    def __init__(self):
        self.timers = {}
        self.active_timers = {}

    def start_timing(self, timer_id="default"):
        """开始计时"""
        self.active_timers[timer_id] = time.time()
        print(f"[TIMER] 计时器 '{timer_id}' 开始")
        return True

    def stop_timing(self, timer_id="default"):
        """停止计时并返回用时"""
        if timer_id in self.active_timers:
            elapsed = time.time() - self.active_timers[timer_id]
            print(f"[TIMER] 计时器 '{timer_id}' 停止，用时: {elapsed:.3f}秒")
            del self.active_timers[timer_id]
            return elapsed
        return 0

    def get_elapsed(self, timer_id="default"):
        """获取当前计时"""
        if timer_id in self.active_timers:
            return time.time() - self.active_timers[timer_id]
        return 0

# 创建全局实例
timer_manager = TimerManager()

# 提供便捷函数
def start_timing(timer_id="default"):
    """开始计时（便捷函数）"""
    return timer_manager.start_timing(timer_id)

def stop_timing(timer_id="default"):
    """停止计时（便捷函数）"""
    return timer_manager.stop_timing(timer_id)

def get_elapsed_time(timer_id="default"):
    """获取经过时间（便捷函数）"""
    return timer_manager.get_elapsed(timer_id)


