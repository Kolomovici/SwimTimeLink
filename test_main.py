#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一测试模块
============

覆盖范围：
  1. shared_functions.py  — 计时管理、函数注册、延迟测试
  2. excel_writer.py      — Excel 数据读取、处理、生成
  3. app.py               — Flask 后端全部 API 接口

运行方式：
  python test_main.py              # 运行全部测试
  python test_main.py --module=sf  # 只测 shared_functions
  python test_main.py --module=ex  # 只测 excel_writer
  python test_main.py --module=api # 只测 app API（需先启动服务器）
"""

import sys
import os
import io
import json
import time
import threading
import traceback
from datetime import datetime

# ================================================================
# 环境准备
# ================================================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 全局测试结果收集
TEST_RESULTS = {
    "passed": 0,
    "failed": 0,
    "errors": [],
    "start_time": None,
    "end_time": None,
}


def _run_test(name, func):
    """运行单个测试用例并统计结果"""
    print(f"\n  ▶ {name} ... ", end="", flush=True)
    try:
        func()
        print("✅ 通过")
        TEST_RESULTS["passed"] += 1
    except AssertionError as e:
        print("❌ 失败")
        msg = f"[{name}] {e}"
        print(f"      {msg}")
        TEST_RESULTS["failed"] += 1
        TEST_RESULTS["errors"].append(msg)
    except Exception as e:
        print("💥 异常")
        msg = f"[{name}] {type(e).__name__}: {e}"
        traceback.print_exc()
        TEST_RESULTS["failed"] += 1
        TEST_RESULTS["errors"].append(msg)


# ================================================================
# 1️⃣  shared_functions.py 测试
# ================================================================

def test_shared_functions():
    """测试 shared_functions 模块"""
    print("\n" + "=" * 60)
    print("📦 模块：shared_functions.py")
    print("=" * 60)

    import shared_functions as sf

    # ---- TimerManager 基本操作 ----
    def _test_timer_manager_create():
        mgr = sf.TimerManager()
        assert hasattr(mgr, "timers"), "缺少 timers 属性"
        assert hasattr(mgr, "active_timers"), "缺少 active_timers 属性"
        assert isinstance(mgr.timers, dict), "timers 应为 dict"
        assert isinstance(mgr.active_timers, dict), "active_timers 应为 dict"

    def _test_start_timing():
        result = sf.start_timing("test_race_1")
        assert result is True, "start_timing 应返回 True"
        assert "test_race_1" in sf.timer_manager.active_timers, "计时器应被记录"

    def _test_get_elapsed():
        sf.start_timing("test_elapsed")
        time.sleep(0.05)
        elapsed = sf.get_elapsed_time("test_elapsed")
        assert elapsed > 0, f"经过时间应 > 0，实际: {elapsed}"
        assert elapsed < 1, f"经过时间应 < 1秒，实际: {elapsed}"

    def _test_stop_timing():
        sf.start_timing("test_stop")
        time.sleep(0.02)
        elapsed = sf.stop_timing("test_stop")
        assert elapsed > 0, f"停止计时返回值应 > 0，实际: {elapsed}"
        assert "test_stop" not in sf.timer_manager.active_timers, "计时器应从 active_timers 移除"

    def _test_stop_nonexistent():
        result = sf.stop_timing("nonexistent_timer")
        assert result == 0, "不存在的计时器应返回 0"

    def _test_latency():
        result = sf.test_latency()
        assert result is not None, "test_latency 应返回数值"
        assert isinstance(result, float), f"返回值应为 float，实际: {type(result)}"

    def _test_register_and_get():
        def dummy_stop():
            return 0.5
        sf.register_functions(
            start_timing_func=lambda tid: True,
            test_latency_func=lambda: 0.1,
            stop_timing_func=dummy_stop
        )
        assert sf.is_functions_registered(), "函数注册后 is_functions_registered() 应返回 True"
        stop_func = sf.get_stop_timing()
        assert stop_func is not None, "get_stop_timing() 不应返回 None"
        assert stop_func() == 0.5, "get_stop_timing 返回的应是被注册的函数"

    def _test_convenience_consistency():
        sf.start_timing("consistency_check")
        e1 = sf.get_elapsed_time("consistency_check")
        time.sleep(0.01)
        e2 = sf.get_elapsed_time("consistency_check")
        assert e2 > e1, "两次获取的经过时间应递增"
        sf.stop_timing("consistency_check")

    # ---- 执行测试 ----
    tests = [
        ("TimerManager 创建", _test_timer_manager_create),
        ("start_timing 开始计时", _test_start_timing),
        ("get_elapsed_time 获取经过时间", _test_get_elapsed),
        ("stop_timing 停止计时", _test_stop_timing),
        ("stop_timing 不存在的计时器", _test_stop_nonexistent),
        ("test_latency 延迟测试", _test_latency),
        ("register_functions / get_stop_timing", _test_register_and_get),
        ("全局便捷函数一致性", _test_convenience_consistency),
    ]
    for name, func in tests:
        _run_test(name, func)


# ================================================================
# 2️⃣  excel_writer.py 测试
# ================================================================

def test_excel_writer():
    """测试 excel_writer 模块"""
    print("\n" + "=" * 60)
    print("📦 模块：excel_writer.py")
    print("=" * 60)

    import pandas as pd
    import numpy as np
    from excel_writer import process_data, generate_test_data

    # ---- 测试用例 ----
    def _test_generate_default():
        df = generate_test_data()
        assert len(df) == 50, f"默认应生成 50 行，实际: {len(df)}"
        assert "员工ID" in df.columns, "应包含 '员工ID' 列"
        assert "总工资" in df.columns, "应包含 '总工资' 列"
        assert "绩效评级" in df.columns, "应包含 '绩效评级' 列"

    def _test_generate_custom():
        df = generate_test_data(rows=10)
        assert len(df) == 10, f"应生成 10 行，实际: {len(df)}"

    def _test_process_normal():
        df_in = pd.DataFrame({
            "姓名": ["张三", "李四", "王五"],
            "分数": [85, 92, 78],
        })
        buf = io.BytesIO()
        df_in.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        df_out = process_data(buf.read())
        assert df_out is not None, "process_data 应返回 DataFrame"
        assert len(df_out) == 3, f"行数应为 3，实际: {len(df_out)}"
        assert "处理时间" in df_out.columns, "应包含 '处理时间' 列"
        assert "数据源" in df_out.columns, "应包含 '数据源' 列"

    def _test_process_debug():
        df_in = pd.DataFrame({"A": [1, 2, 3]})
        buf = io.BytesIO()
        df_in.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        df_out = process_data(buf.read(), debug=True)
        assert df_out is not None

    def _test_process_empty():
        df_in = pd.DataFrame()
        buf = io.BytesIO()
        df_in.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        df_out = process_data(buf.read())
        assert df_out is not None
        assert len(df_out) == 0, "空数据应返回 0 行"

    def _test_process_numeric():
        np.random.seed(42)
        df_in = pd.DataFrame({
            "数值1": np.random.randn(20),
            "数值2": np.random.randint(1, 100, 20),
            "文本": ["A"] * 20,
        })
        buf = io.BytesIO()
        df_in.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        df_out = process_data(buf.read())
        assert len(df_out) == 20

    def _test_process_invalid():
        try:
            process_data(b"not an excel file")
            print("(未抛异常，可接受)")
        except Exception:
            print("(合理抛异常)")

    # ---- 执行测试 ----
    tests = [
        ("generate_test_data 默认行数", _test_generate_default),
        ("generate_test_data 指定行数", _test_generate_custom),
        ("process_data — 正常数据", _test_process_normal),
        ("process_data — 带调试模式", _test_process_debug),
        ("process_data — 空数据", _test_process_empty),
        ("process_data — 数值列统计", _test_process_numeric),
        ("process_data — 异常数据", _test_process_invalid),
    ]
    for name, func in tests:
        _run_test(name, func)


# ================================================================
# 3️⃣  app.py API 测试（需要 Flask 服务器运行）
# ================================================================

def test_app_api(base_url="http://localhost:5000"):
    """测试 app.py 的 Flask API 接口"""
    print("\n" + "=" * 60)
    print("📦 模块：app.py — Flask API 测试")
    print("=" * 60)
    print(f"  服务器地址: {base_url}")
    print("  ⚠️  请确保服务器已在运行: python app.py")
    print("=" * 60)

    import urllib.request
    import urllib.error

    def _req(method, path, body=None):
        """发送 HTTP 请求的辅助函数"""
        url = f"{base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        try:
            resp = urllib.request.urlopen(req, timeout=5)
            return json.loads(resp.read().decode("utf-8")), resp.status
        except urllib.error.HTTPError as e:
            return json.loads(e.read().decode("utf-8")), e.code
        except urllib.error.URLError:
            print("\n  ⚠️  无法连接到服务器，跳过 API 测试。")
            print("     请先运行: python app.py")
            return None, 0

        # API 测试函数定义
    def _test_index():
        url = f"{base_url}/"
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=5)
        html = resp.read().decode("utf-8")
        assert resp.status == 200, f"状态码应为 200，实际: {resp.status}"
        assert "裁判长控制台" in html or "head_judgment" in html, "页面应包含裁判长控制台相关内容"
        print(f"  状态码: {resp.status}, 页面大小: {len(html)} 字节")

    def _test_judgment():
        url = f"{base_url}/judgment"
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=5)
        html = resp.read().decode("utf-8")
        assert resp.status == 200, f"状态码应为 200，实际: {resp.status}"
        assert "泳道计时器" in html or "judgment" in html, "页面应包含泳道计时器相关内容"
        print(f"  状态码: {resp.status}, 页面大小: {len(html)} 字节")

    def _test_sync():
        data, status = _req("POST", "/sync", {"lane": 1, "client_time": int(time.time() * 1000)})
        assert data is not None, "response is None"
        assert data["status"] == "ok", f"status 应为 'ok'，实际: {data.get('status')}"
        assert "server_time" in data, "应包含 server_time"
        assert isinstance(data["server_time"], int), "server_time 应为 int"
        print(f"  server_time={data['server_time']}, rtt={data.get('rtt')}ms")

    def _test_register():
        data, status = _req("POST", "/register_participant", {
            "lane": 1,
            "participant": {"name": "测试选手", "number": "001", "team": "测试队"}
        })
        assert data is not None
        assert data["status"] == "ok", f"状态应为 ok，实际: {data}"
        assert "已注册" in data.get("message", ""), "应返回注册成功信息"

    def _test_get_participants():
        data, status = _req("GET", "/get_participants")
        assert data is not None
        assert "participants" in data, "应包含 participants 字段"
        assert "count" in data, "应包含 count 字段"
        print(f"  选手总数: {data['count']}")

    def _test_start_race():
        data, status = _req("POST", "/start_race", {
            "project_name": "测试-100米蛙泳",
            "segments": 2
        })
        assert data is not None
        assert data["status"] == "ok", f"状态应为 ok，实际: {data}"

    def _test_esp_fire():
        data, status = _req("POST", "/esp_fire", {
            "project_name": "测试-100米蛙泳",
            "segments": 2
        })
        assert data is not None
        assert data["status"] == "ok", f"状态应为 ok，实际: {data}"
        assert "start_time" in data, "应包含 start_time"
        assert data["start_time"] > 0, "start_time 应 > 0"
        print(f"  发令时间戳: {data['start_time']}")

    def _test_record_time():
        _req("POST", "/esp_fire", {"project_name": "测试-100米蛙泳", "segments": 2})
        now = int(time.time() * 1000)
        data, status = _req("POST", "/record_time", {
            "lane": 1,
            "segment": 1,
            "click_time": now + 28500,
            "client_send_time": now,
            "device_info": {"userAgent": "test"}
        })
        assert data is not None
        if data["status"] == "ok":
            assert "compensated_time_ms" in data
            ct = data["compensated_time_ms"]
            assert 20000 < ct < 40000, f"成绩应在合理范围 (20000~40000ms)，实际: {ct}"
            print(f"  原始:{data['raw_time_ms']}ms → 补偿后:{ct}ms  延迟:{data['network_delay_ms']}ms")
        else:
            print(f"  status={data['status']}, msg={data.get('message')}")

    def _test_get_race_status():
        data, status = _req("GET", "/get_race_status")
        assert data is not None
        assert "race_active" in data
        assert "project_name" in data
        assert "participants" in data
        assert "scores" in data
        print(f"  比赛进行中: {data['race_active']}, 项目: {data['project_name']}")

    def _test_get_scores():
        data, status = _req("GET", "/get_scores")
        assert data is not None
        assert "race" in data, "应包含 race 字段"
        assert "participants" in data, "应包含 participants 字段"
        assert "scores" in data, "应包含 scores 字段"
        print(f"  项目: {data['race']['project_name']}")

    def _test_get_scores_lane():
        data, status = _req("GET", "/get_scores?lane=1")
        assert data is not None
        assert "lane" in data
        assert data["lane"] == 1
        print(f"  泳道1 成绩条目数: {len(data.get('scores', []))}")

    def _test_clear_participants():
        data, status = _req("POST", "/clear_participants")
        assert data is not None
        assert data["status"] == "ok"
        check, _ = _req("GET", "/get_participants")
        assert check["count"] == 0, f"选手数应为 0，实际: {check['count']}"

    def _test_reset_race():
        data, status = _req("POST", "/reset_race")
        assert data is not None
        assert data["status"] == "ok"

    def _test_export():
        url = f"{base_url}/export_results"
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=5)
        assert resp.status == 200, f"状态码应为 200，实际: {resp.status}"
        content = resp.read()
        assert len(content) > 50, f"CSV 内容过短: {len(content)} 字节"
        print(f"  CSV 大小: {len(content)} 字节")

    # 先检查服务器连接
    try:
        _run_test("GET / — 裁判长首页", _test_index)
    except Exception:
        print("\n  ⚠️  服务器连接失败，跳过全部 API 测试。")
        print("     请先启动服务器: python app.py")
        return

    # 按依赖顺序执行测试
    api_tests = [
        ("GET /judgment — 裁判手机端", _test_judgment),
        ("POST /sync — 时间同步", _test_sync),
        ("POST /register_participant — 注册选手", _test_register),
        ("GET /get_participants — 获取选手列表", _test_get_participants),
        ("POST /start_race — 发令", _test_start_race),
        ("POST /esp_fire — ESP 实际发令", _test_esp_fire),
        ("POST /record_time — 记录成绩", _test_record_time),
        ("GET /get_race_status — 比赛状态", _test_get_race_status),
        ("GET /get_scores — 获取成绩", _test_get_scores),
        ("GET /get_scores?lane=1 — 单道成绩", _test_get_scores_lane),
        ("POST /clear_participants — 清空选手", _test_clear_participants),
        ("POST /reset_race — 重置比赛", _test_reset_race),
        ("GET /export_results — 导出成绩", _test_export),
    ]
    for name, func in api_tests:
        _run_test(name, func)


# ================================================================
# 报告输出
# ================================================================

def print_report():
    """打印最终测试报告"""
    TEST_RESULTS["end_time"] = datetime.now()
    total = TEST_RESULTS["passed"] + TEST_RESULTS["failed"]

    print("\n\n" + "=" * 60)
    print("📋  最终测试报告")
    print("=" * 60)
    print(f"  总用例: {total}")
    print(f"  ✅ 通过: {TEST_RESULTS['passed']}")
    print(f"  ❌ 失败: {TEST_RESULTS['failed']}")
    if total > 0:
        rate = TEST_RESULTS["passed"] / total * 100
        print(f"  📊 成功率: {rate:.1f}%")

    if TEST_RESULTS["errors"]:
        print("\n  失败详情:")
        for err in TEST_RESULTS["errors"]:
            print(f"    • {err}")

    print("=" * 60)

    # 生成报告文件
    report_dir = os.path.join(PROJECT_ROOT, "test_result")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("游泳计时系统 - 测试报告\n")
        f.write(f"测试时间: {TEST_RESULTS['start_time']}\n")
        f.write(f"完成时间: {TEST_RESULTS['end_time']}\n")
        f.write(f"总用例: {total}\n")
        f.write(f"通过: {TEST_RESULTS['passed']}\n")
        f.write(f"失败: {TEST_RESULTS['failed']}\n")
        f.write(f"成功率: {(TEST_RESULTS['passed'] / total * 100) if total > 0 else 0:.1f}%\n\n")
        if TEST_RESULTS["errors"]:
            f.write("失败详情:\n")
            for err in TEST_RESULTS["errors"]:
                f.write(f"  - {err}\n")
    print(f"\n📄 报告已保存: {report_path}")


# ================================================================
# 主入口
# ================================================================

def main():
    TEST_RESULTS["start_time"] = datetime.now()

    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="游泳计时系统 — 统一测试")
    parser.add_argument("--module", "-m", choices=["all", "sf", "ex", "api"],
                        default="all", help="测试模块: all(全部), sf(shared_functions), ex(excel_writer), api(Flask API)")
    parser.add_argument("--url", default="http://localhost:5000",
                        help="Flask 服务器地址（仅 API 测试用）")
    args = parser.parse_args()

    print("=" * 60)
    print("🏊  游泳比赛计时系统 — 统一测试套件")
    print("=" * 60)
    print(f"  Python: {sys.version}")
    print(f"  时间: {TEST_RESULTS['start_time']}")
    print(f"  模块: {args.module}")
    print(f"  工作目录: {PROJECT_ROOT}")
    print("=" * 60)

    if args.module in ("all", "sf"):
        test_shared_functions()

    if args.module in ("all", "ex"):
        test_excel_writer()

    if args.module in ("all", "api"):
        test_app_api(base_url=args.url)

    print_report()

    # 返回退出码
    return 0 if TEST_RESULTS["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
