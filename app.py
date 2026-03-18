from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import threading
import time
import os

import time
import threading
from datetime import datetime
import csv
import os

# 全局变量
is_timing = False
timing_thread = None
timing_data = []
start_time = None

def start_timing():
    """开始计时程序"""
    global is_timing, timing_data, start_time
    
    if is_timing:
        print("计时已经在进行中...")
        return
    
    is_timing = True
    timing_data = []
    start_time = time.time()
    
    print(f"开始计时 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[DEBUG] app.py: start_timing函数被调用，is_timing={is_timing}")
    
    # 创建计时线程
    timing_thread = threading.Thread(target=timing_loop)
    timing_thread.daemon = True
    timing_thread.start()

def timing_loop():
    """计时循环"""
    global is_timing, timing_data, start_time
    
    print(f"[DEBUG] app.py: 计时循环开始")
    
    while is_timing:
        current_time = time.time() - start_time
        timing_data.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'elapsed': round(current_time, 3)
        })
        
        # 每秒记录一次
        time.sleep(1)
        
        # 每10秒保存一次数据
        if len(timing_data) % 10 == 0:
            save_timing_data()
    
    print(f"[DEBUG] app.py: 计时循环结束")

def save_timing_data():
    """保存计时数据到CSV文件"""
    if not timing_data:
        return
    
    filename = f"timing_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'elapsed']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for data in timing_data:
            writer.writerow(data)
    
    print(f"数据已保存到: {filename}")

def stop_timing():
    """停止计时程序"""
    global is_timing, timing_thread
    
    if not is_timing:
        print("没有正在进行的计时")
        return
    
    is_timing = False
    
    # 保存最终数据
    save_timing_data()
    
    print(f"计时已停止 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总计时长: {len(timing_data)} 秒")
    print(f"[DEBUG] app.py: stop_timing函数被调用，is_timing={is_timing}")

def test_latency():
    """测试延迟程序"""
    print("开始延迟测试...")
    print(f"[DEBUG] app.py: test_latency函数被调用")
    
    test_results = []
    num_tests = 10
    
    for i in range(num_tests):
        start = time.time()
        # 模拟一些处理
        time.sleep(0.01)  # 10ms延迟模拟
        end = time.time()
        
        latency = (end - start) * 1000  # 转换为毫秒
        test_results.append(latency)
        
        print(f"测试 {i+1}/{num_tests}: {latency:.2f} ms")
    
    # 计算统计信息
    avg_latency = sum(test_results) / len(test_results)
    max_latency = max(test_results)
    min_latency = min(test_results)
    
    print(f"\n延迟测试结果:")
    print(f"平均延迟: {avg_latency:.2f} ms")
    print(f"最大延迟: {max_latency:.2f} ms")
    print(f"最小延迟: {min_latency:.2f} ms")
    
    # 保存测试结果
    save_latency_results(test_results, avg_latency, max_latency, min_latency)

def save_latency_results(results, avg, max_val, min_val):
    """保存延迟测试结果"""
    filename = f"latency_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['测试编号', '延迟(ms)'])
        
        for i, latency in enumerate(results, 1):
            writer.writerow([i, f"{latency:.2f}"])
        
        writer.writerow([])
        writer.writerow(['统计信息'])
        writer.writerow(['平均延迟', f"{avg:.2f}"])
        writer.writerow(['最大延迟', f"{max_val:.2f}"])
        writer.writerow(['最小延迟', f"{min_val:.2f}"])

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # 允许跨域，方便前端调试

# 全局数据结构（内存存储）
# 比赛状态
current_project = {
    "name": "",
    "segments": 0,
    "start_time": None,
    "active": False
}
# 各泳道成绩：lane -> [seg1, seg2, ...]
scores = {}
# 线程锁，保护共享数据
lock = threading.Lock()

@app.route('/sync', methods=['POST'])
def sync_time():
    data = request.get_json()
    lane = data.get('lane')
    # 可以记录手机发送的t1，但此接口只需返回服务器时间
    server_time = int(time.time() * 1000)  # 毫秒
    return jsonify({"status": "ok", "server_time": server_time})


@app.route('/start', methods=['POST'])
def start_race():
    global current_project
    data = request.get_json()
    project_name = data.get('project')
    segments = data.get('segments')
    with lock:
        current_project = {
            "name": project_name,
            "segments": segments,
            "start_time": int(time.time() * 1000),
            "active": True
        }
        # 重置成绩表（假设泳道1-8，可根据实际情况动态）
        global scores
        scores = {lane: [None] * segments for lane in range(1, 9)}
    # 广播发令消息给所有连接的手机
    socketio.emit('start', {
        "project": project_name,
        "start_time": current_project["start_time"]
    })
    return jsonify({"status": "ok", "start_time": current_project["start_time"]})

@app.route('/record', methods=['POST'])
def record_time():
    data = request.get_json()
    lane = data.get('lane')
    segment = data.get('segment')
    corrected_click_time = data.get('corrected_click_time')  # 手机校正后的时间戳

    with lock:
        if not current_project["active"]:
            return jsonify({"status": "error", "message": "比赛未开始"}), 400
        start = current_project["start_time"]
        if start is None:
            return jsonify({"status": "error", "message": "无发令时间"}), 400

        net_time = corrected_click_time - start  # 净成绩（毫秒）
        # 存储成绩
        if lane in scores:
            if 1 <= segment <= len(scores[lane]):
                scores[lane][segment-1] = net_time
            else:
                return jsonify({"status": "error", "message": "分段序号错误"}), 400
        else:
            return jsonify({"status": "error", "message": "无效泳道"}), 400

    # 可选：通过WebSocket推送给裁判长PC实时更新
    socketio.emit('score_update', {
        "lane": lane,
        "segment": segment,
        "time": net_time
    })

    return jsonify({"status": "ok", "corrected_time": net_time})

@app.route('/project', methods=['POST'])
def set_project():
    data = request.get_json()
    with lock:
        current_project["name"] = data.get('project')
        current_project["segments"] = data.get('segments')
        # 不改变 active 和 start_time
    return jsonify({"status": "ok"})

@app.route('/scores', methods=['GET'])
def get_scores():
    with lock:
        return jsonify({
            "project": current_project["name"],
            "start_time": current_project["start_time"],
            "scores": scores
        })
    
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('register')
def handle_register(data):
    lane = data.get('lane')
    # 可以将客户端的sid与泳道关联，后续可定向广播
    print(f'Lane {lane} registered with sid {request.sid}')

def get_test_latency():
    """获取测试延迟函数"""
    return test_latency

def get_stop_timing():
    """获取停止计时函数"""
    return stop_timing

def main():
    """主程序"""
    print("程序已启动")
    print(f"[DEBUG] app.py: main函数开始")
    
    try:
        # 导入共享模块并注册函数
        import shared_functions
        print(f"[DEBUG] app.py: 成功导入shared_functions模块")
        
        # 注册函数到共享模块
        shared_functions.register_functions(start_timing, test_latency, stop_timing)
        print(f"[DEBUG] app.py: 函数已注册到shared_functions")
        
        # 检查函数是否成功注册
        if shared_functions.is_functions_registered():
            print("[DEBUG] app.py: 所有函数已成功注册")
        else:
            print("[DEBUG] app.py: 警告：部分函数未成功注册")
        
        # 导入ESP模块
        import ESP
        print(f"[DEBUG] app.py: 成功导入ESP模块")
        
        # 启动键盘监听
        ESP.start_keyboard_monitoring()
        print("等待按键输入...")
        print("按下1键: 播放音效1")
        print("按下2键: 播放音效2")
        print("按下3键: 播放音效3")
        print("按下4键: 播放音效 + 开始计时")
        print("按下5键: 播放音效 + 测试延迟")
        print("按下Ctrl+C退出程序")
        
        # 保持主线程运行
        while True:
            time.sleep(1)
            
    except ImportError as e:
        print(f"警告：无法导入模块: {e}")
        print("将使用键盘输入模拟")
        
        # 使用原有的键盘输入方式
        print("程序已启动，等待按键输入...")
        print("按下4键: 开始计时")
        print("按下5键: 测试延迟")
        print("按下q键退出")
        
        try:
            while True:
                key = input("请输入按键(4/5/q退出): ").strip()
                if key == '4':
                    start_timing()
                elif key == '5':
                    test_latency()
                elif key.lower() == 'q':
                    stop_timing()
                    break
                else:
                    print("无效输入，请按4、5或q")
        except KeyboardInterrupt:
            stop_timing()
            print("\n程序已退出")
            
    except KeyboardInterrupt:
        print("\n正在停止程序...")
    finally:
        # 停止计时（如果正在运行）
        stop_timing()
        print("程序已退出")


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)