"""

数据管理模块 - 层级化文件存储
路径: data/{date}/session_{session_id}/{project_name}/lane_{lane}/
"""
import os
import json
import time
import threading
from datetime import datetime
from collections import defaultdict

DATA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
lock = threading.Lock()


def _ensure_dir(path):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def _write_json(filepath, data):
    """写入JSON文件（线程安全）"""
    with lock:
        _ensure_dir(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def _read_json(filepath, default=None):
    """读取JSON文件"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[DataManager] 读取失败 {filepath}: {e}")
    return default if default is not None else {}


# ==================== 场次管理 ====================

def create_session(date_str, session_id):
    """创建场次目录和session.json"""
    session_dir = os.path.join(DATA_ROOT, date_str, f"session_{session_id}")
    session_file = os.path.join(session_dir, "session.json")
    
    if os.path.exists(session_file):
        return {"status": "exists", "session_id": session_id}
    
    session_data = {
        "session_id": session_id,
        "date": date_str,
        "created_at": int(time.time() * 1000),
        "status": "active"
    }
    _write_json(session_file, session_data)
    print(f"[DataManager] 场次已创建: {date_str}/session_{session_id}")
    return {"status": "ok", "session_id": session_id}


def get_session(date_str, session_id):
    """获取场次信息"""
    session_file = os.path.join(DATA_ROOT, date_str, f"session_{session_id}", "session.json")
    return _read_json(session_file)


# ==================== 选手管理 ====================

def register_participant(date_str, session_id, project_name, lane, name, number, team):
    """注册选手信息"""
    lane_dir = os.path.join(DATA_ROOT, date_str, f"session_{session_id}", 
                            project_name, f"lane_{lane}")
    info_file = os.path.join(lane_dir, "info.json")
    
    participant_data = {
        "name": name,
        "number": number,
        "team": team,
        "lane": lane,
        "registered_at": datetime.now().isoformat()
    }
    _write_json(info_file, participant_data)
    print(f"[DataManager] 选手已注册: {project_name}/lane_{lane} - {name}")
    return participant_data


def get_participant(date_str, session_id, project_name, lane):
    """获取选手信息"""
    info_file = os.path.join(DATA_ROOT, date_str, f"session_{session_id}",
                             project_name, f"lane_{lane}", "info.json")
    return _read_json(info_file)


def get_all_participants(date_str, session_id, project_name):
    """获取某项目所有选手"""
    project_dir = os.path.join(DATA_ROOT, date_str, f"session_{session_id}", project_name)
    if not os.path.exists(project_dir):
        return {}
    
    participants = {}
    for item in os.listdir(project_dir):
        if item.startswith("lane_"):
            lane = int(item.split("_")[1])
            info = _read_json(os.path.join(project_dir, item, "info.json"))
            if info:
                participants[lane] = info
    return participants


# ==================== 比赛管理 ====================

def create_race(date_str, session_id, project_name, segments):
    """创建比赛（发令前准备）"""
    race_file = os.path.join(DATA_ROOT, date_str, f"session_{session_id}",
                             project_name, "race.json")
    
    race_data = {
        "race_id": f"{date_str.replace('-','')}_s{session_id}_{project_name}",
        "project_name": project_name,
        "session": session_id,
        "date": date_str,
        "segments": segments,
        "start_time": None,
        "status": "preparing",
        "created_at": int(time.time() * 1000)
    }
    _write_json(race_file, race_data)
    return race_data


def start_race(date_str, session_id, project_name, segments):
    """发令（记录真正的开始时间）"""
    race_file = os.path.join(DATA_ROOT, date_str, f"session_{session_id}",
                             project_name, "race.json")
    
    start_timestamp = int(time.time() * 1000)
    
    race_data = {
        "race_id": f"{date_str.replace('-','')}_s{session_id}_{project_name}",
        "project_name": project_name,
        "session": session_id,
        "date": date_str,
        "segments": segments,
        "start_time": start_timestamp,
        "status": "racing",
        "created_at": int(time.time() * 1000)
    }
    _write_json(race_file, race_data)
    
    # 为8条泳道准备空results.json
    for lane in range(1, 9):
        results_file = os.path.join(DATA_ROOT, date_str, f"session_{session_id}",
                                    project_name, f"lane_{lane}", "results.json")
        if not os.path.exists(results_file):
            _write_json(results_file, [])
    
    print(f"[DataManager] 比赛开始: {project_name} @ {start_timestamp}")
    return race_data


def get_race(date_str, session_id, project_name):
    """获取比赛信息"""
    race_file = os.path.join(DATA_ROOT, date_str, f"session_{session_id}",
                             project_name, "race.json")
    return _read_json(race_file)


def complete_race(date_str, session_id, project_name):
    """完成比赛"""
    race_file = os.path.join(DATA_ROOT, date_str, f"session_{session_id}",
                             project_name, "race.json")
    race_data = _read_json(race_file)
    if race_data:
        race_data["status"] = "completed"
        _write_json(race_file, race_data)
    
    # 更新session状态
    session_file = os.path.join(DATA_ROOT, date_str, f"session_{session_id}", "session.json")
    session_data = _read_json(session_file)
    if session_data:
        session_data["status"] = "completed"
        _write_json(session_file, session_data)


# ==================== 成绩管理 ====================

def record_score(date_str, session_id, project_name, lane, segment, 
                 compensated_time_ms, network_delay_ms):
    """记录分段成绩"""
    results_file = os.path.join(DATA_ROOT, date_str, f"session_{session_id}",
                                project_name, f"lane_{lane}", "results.json")
    
    results = _read_json(results_file, [])
    
    score_record = {
        "segment": segment,
        "time_ms": compensated_time_ms,
        "network_delay_ms": network_delay_ms
    }
    results.append(score_record)
    _write_json(results_file, results)
    
    # 检查是否所有分段已记录完成
    race_data = get_race(date_str, session_id, project_name)
    if race_data and len(results) >= race_data.get("segments", 0):
        # 检查该泳道是否已完成所有分段
        pass  # 由外部逻辑判断全场是否完成
    
    print(f"[DataManager] 成绩记录: {project_name}/lane_{lane} seg{segment} = {compensated_time_ms}ms")
    return score_record


def get_scores(date_str, session_id, project_name, lane=None):
    """获取成绩"""
    if lane is not None:
        results_file = os.path.join(DATA_ROOT, date_str, f"session_{session_id}",
                                    project_name, f"lane_{lane}", "results.json")
        return _read_json(results_file, [])
    else:
        project_dir = os.path.join(DATA_ROOT, date_str, f"session_{session_id}", project_name)
        if not os.path.exists(project_dir):
            return {}
        
        all_scores = {}
        for item in os.listdir(project_dir):
            if item.startswith("lane_"):
                l = int(item.split("_")[1])
                results = _read_json(os.path.join(project_dir, item, "results.json"), [])
                if results:
                    all_scores[l] = results
        return all_scores


def clear_race_data(date_str, session_id, project_name):
    """清空某比赛数据"""
    project_dir = os.path.join(DATA_ROOT, date_str, f"session_{session_id}", project_name)
    if os.path.exists(project_dir):
        import shutil
        shutil.rmtree(project_dir)
        print(f"[DataManager] 已删除: {project_dir}")


# ==================== 目录浏览 ====================

def list_dates():
    """列出所有有数据的日期"""
    if not os.path.exists(DATA_ROOT):
        return []
    return sorted([d for d in os.listdir(DATA_ROOT) 
                   if os.path.isdir(os.path.join(DATA_ROOT, d))], reverse=True)


def list_sessions(date_str):
    """列出某日期的场次"""
    date_dir = os.path.join(DATA_ROOT, date_str)
    if not os.path.exists(date_dir):
        return []
    sessions = []
    for item in os.listdir(date_dir):
        if item.startswith("session_"):
            sid = int(item.split("_")[1])
            sessions.append({
                "session_id": sid,
                "data": _read_json(os.path.join(date_dir, item, "session.json"), {})
            })
    return sorted(sessions, key=lambda x: x["session_id"])


def list_projects(date_str, session_id):
    """列出某场次的所有项目"""
    session_dir = os.path.join(DATA_ROOT, date_str, f"session_{session_id}")
    if not os.path.exists(session_dir):
        return []
    projects = []
    for item in os.listdir(session_dir):
        if item != "session.json" and os.path.isdir(os.path.join(session_dir, item)):
            race_data = get_race(date_str, session_id, item)
            projects.append({
                "name": item,
                "race": race_data
            })
    return projects


def export_data(date_str=None, session_id=None, project_name=None):
    """按路径导出数据"""
    if date_str:
        if session_id:
            if project_name:
                # 返回特定项目完整数据
                race = get_race(date_str, session_id, project_name)
                participants = get_all_participants(date_str, session_id, project_name)
                scores = get_scores(date_str, session_id, project_name)
                return {
                    "race": race,
                    "participants": participants,
                    "scores": scores
                }
            else:
                # 返回某场次所有项目
                projects = list_projects(date_str, session_id)
                return {"date": date_str, "session": session_id, "projects": projects}
        else:
            # 返回某日期所有场次
            sessions = list_sessions(date_str)
            return {"date": date_str, "sessions": sessions}
    else:
        # 返回所有日期列表
        return {"dates": list_dates()}
