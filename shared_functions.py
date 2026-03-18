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

def get_start_timing():
    """获取开始计时函数"""
    return _registered_functions['start_timing']

def get_test_latency():
    """获取测试延迟函数"""
    return _registered_functions['test_latency']

def get_stop_timing():
    """获取停止计时函数"""
    return _registered_functions['stop_timing']

def is_functions_registered():
    """检查函数是否已注册"""
    return all(func is not None for func in _registered_functions.values())