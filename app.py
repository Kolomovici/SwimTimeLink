from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_socketio import SocketIO, emit
import threading
import time
import os
import csv
import json
from datetime import datetime
from collections import defaultdict
import subprocess
import sys

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# ==================== 计时器进程管理 ====================
timer_process = None

def start_timer_script():
    """启动ESP.py计时器脚本"""
    global timer_process
    try:
        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        timer_script = os.path.join(script_dir, "ESP.py")
        
        if os.path.exists(timer_script):
            print(f"[计时器] 正在启动计时器脚本: {timer_script}")
            # 在新进程中运行ESP.py
            timer_process = subprocess.Popen(
                [sys.executable, timer_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            print(f"[计时器] 计时器脚本已启动，PID: {timer_process.pid}")
            
            # 启动一个线程读取输出
            def read_output():
                for line in timer_process.stdout:
                    print(f"[计时器输出] {line.rstrip()}")
            
            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()
            
            return True
        else:
            print(f"[计时器] 找不到计时器脚本: {timer_script}")
            return False
    except Exception as e:
        print(f"[计时器] 启动计时器失败: {e}")
        return False

def stop_timer_script():
    """停止计时器脚本"""
    global timer_process
    if timer_process:
        try:
            timer_process.terminate()
            timer_process.wait(timeout=5)
            print("[计时器] 计时器脚本已停止")
        except:
            timer_process.kill()
            print("[计时器] 强制终止计时器脚本")
        timer_process = None

# ==================== 全局数据结构 ====================
# 比赛状态
current_race = {
    "active": False,
    "project_name": "",
    "segments": 0,
    "start_time": None,
    "start_timestamp": None
}

# 参赛选手信息: lane -> {name, number, team, ...}
participants = {}

# 成绩记录: lane -> [成绩列表] 每个成绩包含 {segment, time_ms, timestamp}
scores = defaultdict(lambda: [])

# 延迟补偿记录
latency_records = defaultdict(list)

# 线程锁
lock = threading.Lock()

# 比赛记录文件
RACE_DATA_FILE = "race_data.json"

def load_race_data():
    """加载历史比赛数据"""
    global participants, scores
    try:
        if os.path.exists(RACE_DATA_FILE):
            with open(RACE_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                participants = data.get('participants', {})
                scores = defaultdict(list, data.get('scores', {}))
            print(f"[数据加载] 已加载 {len(participants)} 名选手信息")
    except Exception as e:
        print(f"[数据加载] 加载失败: {e}")

def save_race_data():
    """保存比赛数据"""
    try:
        data = {
            'participants': dict(participants),
            'scores': dict(scores),
            'last_update': datetime.now().isoformat()
        }
        with open(RACE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[数据保存] 保存失败: {e}")

# 加载历史数据
load_race_data()

# ==================== 路由接口 ====================

@app.route('/')
def index():
    """首页"""
    return send_file('head_judgment.html')

@app.route('/judgment')
def judgment():
    """裁判手机端页面"""
    return send_file('judgment.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """静态文件服务"""
    if os.path.exists(filename):
        return send_file(filename)
    return jsonify({"error": "Not found"}), 404

@app.route('/sync', methods=['POST'])
def sync_time():
    """时间同步接口"""
    data = request.get_json()
    lane = data.get('lane')
    client_time = data.get('client_time')
    
    server_time = int(time.time() * 1000)
    
    # 计算RTT和时钟偏移
    if client_time:
        rtt = int((time.time() * 1000) - client_time)
    else:
        rtt = 0
    
    return jsonify({
        "status": "ok",
        "server_time": server_time,
        "rtt": rtt
    })

@app.route('/register_participant', methods=['POST'])
def register_participant():
    """注册参赛选手"""
    data = request.get_json()
    lane = data.get('lane')
    participant_info = data.get('participant', {})
    
    with lock:
        participants[lane] = {
            'lane': lane,
            'name': participant_info.get('name', ''),
            'number': participant_info.get('number', ''),
            'team': participant_info.get('team', ''),
            'register_time': datetime.now().isoformat(),
            'status': 'registered'
        }
        save_race_data()
    
    # 通知裁判长有新选手注册
    socketio.emit('participant_registered', {
        'lane': lane,
        'participant': participants[lane]
    })
    
    return jsonify({
        "status": "ok",
        "message": f"选手 {participant_info.get('name')} 已注册",
        "lane": lane
    })

@app.route('/start_race', methods=['POST'])
def start_race():
    """发令开始比赛"""
    global current_race
    data = request.get_json()
    
    project_name = data.get('project_name', '游泳比赛')
    segments = data.get('segments', 1)
    start_timestamp = int(time.time() * 1000)
    
    with lock:
        current_race = {
            "active": True,
            "project_name": project_name,
            "segments": segments,
            "start_time": start_timestamp,
            "start_timestamp": start_timestamp
        }
        
        # 清空当前比赛成绩
        scores.clear()
        
        # 更新所有已注册选手状态
        for lane in participants:
            participants[lane]['status'] = 'racing'
        
        save_race_data()
    
    # 广播发令信号
    socketio.emit('race_start', {
        "project_name": project_name,
        "segments": segments,
        "start_time": start_timestamp,
        "start_timestamp": start_timestamp
    })
    
    print(f"[发令] 比赛开始: {project_name}, 分段数: {segments}, 开始时间: {start_timestamp}")
    
    return jsonify({
        "status": "ok",
        "start_time": start_timestamp,
        "message": f"{project_name} 比赛已开始"
    })

@app.route('/record_time', methods=['POST'])
def record_time():
    """记录计时成绩（包含延迟补偿）"""
    data = request.get_json()
    
    lane = data.get('lane')
    segment = data.get('segment')
    click_time = data.get('click_time')  # 手机点击时的本地时间
    client_send_time = data.get('client_send_time')  # 手机发送时间
    device_info = data.get('device_info', {})
    
    with lock:
        if not current_race["active"]:
            return jsonify({
                "status": "error",
                "message": "比赛未开始"
            }), 400
        
        start_time = current_race["start_time"]
        if start_time is None:
            return jsonify({
                "status": "error",
                "message": "无发令时间"
            }), 400
        
        # 计算净成绩（考虑网络延迟补偿）
        server_receive_time = int(time.time() * 1000)
        
        # 估算网络延迟
        if client_send_time:
            network_delay = server_receive_time - client_send_time
        else:
            network_delay = 0
        
        # 净成绩 = 点击时间 - 发令时间
        raw_time = click_time - start_time
        
        # 补偿后的成绩（减去一半网络延迟作为补偿）
        compensated_time = max(0, raw_time - network_delay // 2)
        
        # 记录成绩
        score_record = {
            'segment': segment,
            'raw_time_ms': raw_time,
            'compensated_time_ms': compensated_time,
            'network_delay_ms': network_delay,
            'timestamp': datetime.now().isoformat(),
            'click_time': click_time,
            'server_receive_time': server_receive_time
        }
        
        scores[lane].append(score_record)
        
        # 记录延迟信息
        latency_records[lane].append({
            'segment': segment,
            'network_delay_ms': network_delay,
            'timestamp': datetime.now().isoformat()
        })
        
        save_race_data()
    
    # 实时推送成绩给裁判长
    socketio.emit('score_update', {
        'lane': lane,
        'segment': segment,
        'compensated_time_ms': compensated_time,
        'raw_time_ms': raw_time,
        'network_delay_ms': network_delay,
        'participant': participants.get(lane, {}),
        'timestamp': datetime.now().isoformat()
    })
    
    print(f"[成绩记录] 泳道{lane} 分段{segment} 原始:{raw_time}ms 补偿后:{compensated_time}ms 延迟:{network_delay}ms")
    
    return jsonify({
        "status": "ok",
        "compensated_time_ms": compensated_time,
        "raw_time_ms": raw_time,
        "network_delay_ms": network_delay,
        "message": "成绩已记录"
    })

@app.route('/get_race_status', methods=['GET'])
def get_race_status():
    """获取比赛状态"""
    with lock:
        return jsonify({
            "race_active": current_race["active"],
            "project_name": current_race["project_name"],
            "segments": current_race["segments"],
            "start_time": current_race["start_time"],
            "participants": participants,
            "scores": dict(scores)
        })

@app.route('/get_participants', methods=['GET'])
def get_participants():
    """获取所有参赛选手"""
    with lock:
        return jsonify({
            "participants": participants,
            "count": len(participants)
        })

@app.route('/get_scores', methods=['GET'])
def get_scores():
    """获取所有成绩"""
    lane = request.args.get('lane')
    
    with lock:
        if lane:
            lane = int(lane)
            return jsonify({
                "lane": lane,
                "scores": scores.get(lane, []),
                "participant": participants.get(lane, {})
            })
        else:
            # 格式化成绩输出
            formatted_scores = {}
            for lane_num, score_list in scores.items():
                formatted_scores[lane_num] = []
                for s in score_list:
                    formatted_scores[lane_num].append({
                        'segment': s['segment'],
                        'time_seconds': s['compensated_time_ms'] / 1000,
                        'time_ms': s['compensated_time_ms'],
                        'compensated_time_ms': s['compensated_time_ms'],
                        'network_delay_ms': s['network_delay_ms']
                    })
            
            return jsonify({
                "race": current_race,
                "participants": participants,
                "scores": formatted_scores,
                "latency_stats": get_latency_stats()
            })

def get_latency_stats():
    """获取延迟统计"""
    all_delays = []
    for lane_delays in latency_records.values():
        for record in lane_delays:
            all_delays.append(record['network_delay_ms'])
    
    if all_delays:
        return {
            "avg_delay_ms": sum(all_delays) / len(all_delays),
            "max_delay_ms": max(all_delays),
            "min_delay_ms": min(all_delays),
            "total_records": len(all_delays)
        }
    return {}

@app.route('/reset_race', methods=['POST'])
def reset_race():
    """重置比赛"""
    global current_race, scores, latency_records
    
    with lock:
        current_race = {
            "active": False,
            "project_name": "",
            "segments": 0,
            "start_time": None,
            "start_timestamp": None
        }
        
        # 重置成绩和延迟记录
        scores.clear()
        latency_records.clear()
        
        # 重置选手状态
        for lane in participants:
            participants[lane]['status'] = 'registered'
        
        save_race_data()
    
    socketio.emit('race_reset', {"message": "比赛已重置"})
    
    return jsonify({"status": "ok", "message": "比赛已重置"})

@app.route('/clear_participants', methods=['POST'])
def clear_participants():
    """清空所有选手"""
    global participants, scores
    
    with lock:
        participants.clear()
        scores.clear()
        latency_records.clear()
        save_race_data()
    
    return jsonify({"status": "ok", "message": "所有选手已清空"})

@app.route('/export_results', methods=['GET'])
def export_results():
    """导出比赛结果"""
    with lock:
        # 创建CSV内容
        csv_data = []
        
        # 表头
        headers = ['泳道', '姓名', '号码', '队伍', '分段', '成绩(秒)', '网络延迟(ms)', '记录时间']
        csv_data.append(headers)
        
        for lane, score_list in scores.items():
            participant = participants.get(lane, {})
            for score in score_list:
                csv_data.append([
                    lane,
                    participant.get('name', ''),
                    participant.get('number', ''),
                    participant.get('team', ''),
                    score['segment'],
                    f"{score['compensated_time_ms'] / 1000:.3f}",
                    score['network_delay_ms'],
                    score['timestamp']
                ])
        
        # 生成CSV文件
        filename = f"race_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
        
        return send_file(filename, as_attachment=True, download_name=filename)

# ==================== WebSocket事件处理 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print(f"[WebSocket] 客户端已连接: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print(f"[WebSocket] 客户端已断开: {request.sid}")

@socketio.on('register_judge')
def handle_register_judge(data):
    """裁判手机注册"""
    lane = data.get('lane')
    device_info = data.get('device_info', {})
    
    print(f"[裁判注册] 泳道{lane} 设备: {device_info}")
    
    # 发送当前比赛状态
    with lock:
        if current_race["active"]:
            emit('race_start', {
                "project_name": current_race["project_name"],
                "segments": current_race["segments"],
                "start_time": current_race["start_time"]
            })
    
    emit('registration_confirm', {
        "status": "ok",
        "lane": lane,
        "message": f"泳道{lane} 已注册成功"
    })

@socketio.on('ping')
def handle_ping(data):
    """心跳响应"""
    emit('pong', {"time": data.get('time', 0)})

# ==================== 启动服务器 ====================

if __name__ == '__main__':
    print("=" * 60)
    print("游泳比赛计时系统 - 服务器启动")
    print("=" * 60)
    print("裁判长控制台: http://localhost:5000")
    print("裁判手机端: http://localhost:5000/judgment")
    print("=" * 60)
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    # 启动计时器脚本
    print("\n[初始化] 正在启动计时器脚本...")
    start_timer_script()
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    finally:
        # 服务器停止时关闭计时器进程
        print("\n[清理] 正在停止计时器脚本...")
        stop_timer_script()