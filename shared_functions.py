#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享函数模块，用于在ESP.py和app.py之间传递函数引用
"""

# 存储函数引用的全局变量
start_timing_func = None
test_latency_func = None
stop_timing_func = None

def register_functions(start_func, test_func, stop_func=None):
    """注册函数"""
    global start_timing_func, test_latency_func, stop_timing_func
    
    start_timing_func = start_func
    test_latency_func = test_func
    stop_timing_func = stop_func
    
    print(f"[SHARED] 函数已注册")
    print(f"[SHARED] start_timing_func: {'已注册' if start_timing_func else '未注册'}")
    print(f"[SHARED] test_latency_func: {'已注册' if test_latency_func else '未注册'}")
    print(f"[SHARED] stop_timing_func: {'已注册' if stop_timing_func else '未注册'}")

def get_start_timing():
    """获取开始计时函数"""
    return start_timing_func

def get_test_latency():
    """获取测试延迟函数"""
    return test_latency_func

def get_stop_timing():
    """获取停止计时函数"""
    return stop_timing_func