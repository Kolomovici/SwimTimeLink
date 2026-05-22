<img width="1635" height="658" alt="e5130a438af568592dbfc70b84c9e21f" src="https://github.com/user-attachments/assets/51f99c00-19d0-4285-b211-628913f1d0a1" />



**Apologies**: Due to the "China University Swimming Championship Finals", the development team is unable to be on-site to support the Hunan University Swimming League. However, we have persisted in completing this project! Special thanks to the NJAU (Nanjing Agricultural University) front-end team for their support! Looking forward to meeting you at the China University Swimming Championship in Ordos!

**致歉**：因为"中国大学生游泳锦标赛 总决赛"的缘故，该项目开发团队无法到场支持湖南大学游泳校联赛，但是我们依然坚持将此项目开发完成！ 感谢NJAU(南京农业大学)前端的支持！期待与您们在中国大学生游泳锦标赛————鄂尔多斯相见！

---

This project is an electronic starting and timing system designed for swimming competitions, providing a complete solution from starting, timing, device management to data storage. It uses **ESP.py** as the backend timing hub, communicates with the Flask referee backend via WebSocket, supports automated starting process, MQTT device management, and a local timing window.

本项目是为游泳比赛设计的电子发令与计时系统，提供从发令、计时、设备管理到数据存储的完整解决方案。采用 **ESP.py** 作为后端统一时序中枢，通过 WebSocket 连接 Flask 后端裁判长系统，支持自动化发令流程、MQTT 设备管理和本地计时窗口。

## System Architecture

<img width="1280" height="719" alt="22ef454159ba8f5ec18295d6d0494e70_720" src="https://github.com/user-attachments/assets/7f88f1d2-f64e-4dca-adc7-7c2e0d88c1ba" />

## Requirements

## 环境要求

- **Python 3.10** (recommended, earlier versions may have issues)
- Operating System: Windows (some functions depend on Windows commands)

- **Python 3.10**（推荐，以下版本可能存在问题）
- 操作系统：Windows（部分功能依赖 Windows 命令）

## Installation

## 安装

### 1. Clone the repository

### 1. 克隆项目

```bash
git clone <repository url>
cd SwimTimeLink
```

```bash
git clone <项目地址>
cd SwimTimeLink
```

### 2. Install dependencies

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

```bash
pip install -r requirements.txt
```

Main dependencies:

- `pynput` – keyboard listening
- `pygame` – sound playback
- `paho-mqtt` – MQTT communication (optional, but required for device management)
- `python-socketio[client]` – WebSocket client (optional, if connecting to referee backend)
- `flask`, `flask-socketio` – backend service (only needed when running referee system)
- `openpyxl`, `pandas` – Excel processing
- `PyYAML` – configuration parsing

主要依赖：

- `pynput` – 键盘监听
- `pygame` – 音效播放
- `paho-mqtt` – MQTT 通信（可选，但设备管理需要）
- `python-socketio[client]` – WebSocket 客户端（可选，若需连接裁判长后端）
- `flask`, `flask-socketio` – 后端服务（仅当运行裁判长系统时需要）
- `openpyxl`, `pandas` – Excel 处理
- `PyYAML` – 配置解析

## Configuration

## 配置

### Configuration file paths

### 配置文件路径

- `config.py` – global configuration (Excel processing, UI, security, etc.), can be exported to YAML.
- In `ESP.py`, the sound path and Flask backend URL need to be modified according to your setup.

- `config.py` – 全局配置（Excel 处理、UI、安全等），可导出为 YAML。
- `ESP.py` 中的音效路径和 Flask 后端地址需要根据实际情况修改。

### Key configuration items

### 关键配置项

Modify in `ESP.py`:

在 `ESP.py` 中修改：

```python
FLASK_URL = "http://localhost:5000"          # Flask backend address
FLASK_WS_URL = "http://localhost:5000"        # WebSocket address

SOUND_DIR = os.path.join(os.path.dirname(__file__), "sound")  # sound folder
SOUND_FILES = {
    '1': 'first_whistle.wav',
    '2': 'second_whistle.wav',
    '3': 'take_your_mark.wav',
    '4': 'start.wav',
    '5': 'man.wav'
}
```

```python
FLASK_URL = "http://localhost:5000"          # Flask 后端地址
FLASK_WS_URL = "http://localhost:5000"        # WebSocket 地址

SOUND_DIR = os.path.join(os.path.dirname(__file__), "sound")  # 音效文件夹
SOUND_FILES = {
    '1': 'first_whistle.wav',
    '2': 'second_whistle.wav',
    '3': 'take_your_mark.wav',
    '4': 'start.wav',
    '5': 'man.wav'
}
```

| Key | Sound file | Description |
|------|----------|------------|
| 1 | `first_whistle.wav` | Four short whistles |
| 2 | `second_whistle.wav` | One long whistle |
| 3 | `take_your_mark.wav` | "Take your mark" |
| 4 | `start.wav` | Electric horn (start) |
| 5 | `man.wav` | Delay test sound |

| 按键 | 音效文件 | 说明 |
|------|----------|------|
| 1 | `first_whistle.wav` | 四声短哨 |
| 2 | `second_whistle.wav` | 一声长哨 |
| 3 | `take_your_mark.wav` | "Take your mark" |
| 4 | `start.wav` | 电笛声（发令） |
| 5 | `man.wav` | 延迟测试音 |

Place the corresponding WAV files into the `sound/` folder.

请将对应的 WAV 文件放入 `sound/` 文件夹。

### Data storage path

### 数据存储路径

All competition data is saved under the `data/` directory with the following structure:

所有比赛数据默认保存在 `data/` 目录下，目录结构：

```
data/
└─ YYYY-MM-DD/
   └─ session_{number}/
      └─ {event name}/
         └─ lane_{lane number}/
            ├─ info.json        # athlete info
            └─ results.json     # result records
```

```
data/
└─ YYYY-MM-DD/
   └─ session_{编号}/
      └─ {项目名称}/
         └─ lane_{泳道号}/
            ├─ info.json        # 选手信息
            └─ results.json     # 成绩记录
```

## Running

## 运行

### 1. Run ESP.py standalone (starting gun + timer + device management)

### 1. 独立运行 ESP.py（发令枪 + 计时器 + 设备管理）

```bash
python ESP.py
```

```bash
python ESP.py
```

### 2. Run Flask backend referee system

### 2. 运行 Flask 后端裁判长系统

If you need the referee interface (with WebSocket control of the starting gun), start the Flask server first:

若需要使用裁判长界面（含 WebSocket 控制发令），请先启动 Flask 服务器：

```bash
python app.py
```

```bash
python app.py
```

Then start `ESP.py`, which will automatically connect to the backend.

然后启动 `ESP.py`，它将自动连接后端。

### 3. Run tests

### 3. 运行测试

```bash
python test_main.py                          # all tests
python test_main.py --module=sf              # shared_functions only
python test_main.py --module=ex              # excel_writer only
python test_main.py --module=api             # API only (requires Flask server running)
```

```bash
python test_main.py                          # 全部测试
python test_main.py --module=sf              # 仅 shared_functions
python test_main.py --module=ex              # 仅 excel_writer
python test_main.py --module=api             # 仅 API（需启动 Flask 服务器）
```

## Detailed operation of ESP.py

## ESP.py 详细操作说明

After startup, the program enters keyboard listening mode. All operations are performed via keyboard keys.

启动后程序进入键盘监听模式，所有操作通过键盘按键完成。

### Sound control (number keys)

### 音效控制（数字键）

| Key | Function |
|------|----------|
| `1` | Play four short whistles |
| `2` | Play one long whistle |
| `3` | Play "Take your mark", **and set timer to red** (ready state) |
| `4` | **Manual emergency start**: play electric horn + notify backend of start time + start local timer + notify all MQTT devices to start timing |
| `5` | Play sound + send delay test command to all MQTT devices + run delay test in `shared_functions` |

| 按键 | 功能 |
|------|------|
| `1` | 播放四声短哨 |
| `2` | 播放一声长哨 |
| `3` | 播放 "Take your mark"，**同时将计时器设为红色**（准备状态） |
| `4` | **手动紧急发令**：播放电笛声 + 通知后端记录发令时间 + 启动本地计时器 + 通知所有 MQTT 设备开始计时 |
| `5` | 播放音效 + 向所有 MQTT 设备发送延迟测试命令 + 运行 `shared_functions` 中的延迟测试 |

### Device management (letter keys)

### 设备管理（字母键）

| Key | Function |
|------|----------|
| `a` / `A` | Add a device: enter device ID, create MQTT client and connect to broker |
| `l` / `L` | List all currently connected devices |
| `r` / `R` | Remove a device: enter device ID, disconnect its MQTT connection |

| 按键 | 功能 |
|------|------|
| `a` / `A` | 添加新设备：输入设备 ID，会创建 MQTT 客户端并连接到 broker |
| `l` / `L` | 列出当前所有已连接的设备 |
| `r` / `R` | 移除设备：输入设备 ID，断开其 MQTT 连接 |

### Timer control (individual keys)

### 计时器控制（独立按键）

| Key | Function |
|------|----------|
| `t` / `T` | Set timer to red (ready state) |
| `g` / `G` | Set timer to green and start timing (local only) |
| `s` / `S` | Stop timer |
| `z` / `Z` | Reset timer to zero, color returns to white |
| `w` / `W` | Show/hide timer window (toggle visibility) |
| `d` / `D` | Run delay test (without sound) |
| `x` / `X` | Local start timing (calls `shared_functions.start_timing`, usually for sync test) |

| 按键 | 功能 |
|------|------|
| `t` / `T` | 计时器显示为红色（准备状态） |
| `g` / `G` | 计时器显示为绿色并开始计时（仅本地） |
| `s` / `S` | 停止计时器 |
| `z` / `Z` | 重置计时器归零，颜色恢复白色 |
| `w` / `W` | 显示/隐藏计时窗口（切换窗口可见性） |
| `d` / `D` | 运行延迟测试（独立按键，不带音效） |
| `x` / `X` | 本地启动计时（调用 `shared_functions.start_timing`，通常用于同步测试） |

### Exit

### 退出程序

Press **`Ctrl+C`** to exit; the program will automatically clean up device connections and sound resources.

按 **`Ctrl+C`** 退出，程序会自动清理设备连接和音效资源。

## MQTT device management

## MQTT 设备管理

`ESP.py` includes a `DeviceManager` class that supports managing multiple MQTT devices.

`ESP.py` 内置了 `DeviceManager` 类，支持对多个 MQTT 设备进行管理。

### Device management commands

### 设备管理命令

| Command | Description |
|------|------------|
| `add_device(device_id)` | Add a device and connect to MQTT broker (default `localhost:1883`) |
| `remove_device(device_id)` | Disconnect and remove device |
| `send_command_to_device(device_id, command, data)` | Send command to a single device, published to topic `devices/{device_id}/control` |
| `send_command_to_all(command, data)` | Send the same command to all connected devices |
| `list_devices()` | List all devices |

| 命令 | 说明 |
|------|------|
| `add_device(device_id)` | 添加设备并连接 MQTT broker（默认 `localhost:1883`） |
| `remove_device(device_id)` | 断开并移除设备 |
| `send_command_to_device(device_id, command, data)` | 向单个设备发送命令，发布到 `devices/{device_id}/control` 主题 |
| `send_command_to_all(command, data)` | 向所有已连接的设备发送相同命令 |
| `list_devices()` | 列出所有设备 |

### Topic convention

### 主题约定

- Control topic: `devices/{device_id}/control`
- Message format: JSON containing `command` and optional `data`

- 控制主题：`devices/{device_id}/control`
- 消息格式：JSON，包含 `command` 和可选 `data`

Supported commands:

目前支持的命令：

- `start_timer` – start timing (includes `server_start_time` parameter)
- `start_delay_test` – delay test

- `start_timer` – 启动计时（含 `server_start_time` 参数）
- `start_delay_test` – 延迟测试

### Check MQTT status

### 检查 MQTT 状态

Use the standalone script `mqtt_test.py` to check MQTT broker status and configuration in ESP.py:

使用独立脚本 `mqtt_test.py` 检查 MQTT broker 运行状态和 ESP.py 中的配置：

```bash
python mqtt_test.py
```

```bash
python mqtt_test.py
```

This script will:

1. Check if port `1883` is open
2. Check if Windows Mosquitto service is running
3. Parse MQTT configuration from `ESP.py`
4. Use `netstat` to view port listening status
5. Test MQTT connection (if port is open)

该脚本会依次：

1. 检查端口 `1883` 是否开放
2. 检查 Windows Mosquitto 服务是否运行
3. 解析 `ESP.py` 中的 MQTT 配置
4. 使用 `netstat` 查看端口监听情况
5. 测试 MQTT 连接（如果端口开放）

## Data management module

## 数据管理模块

`data_manager.py` provides functions for creating sessions, registering participants, managing races, and recording results.

`data_manager.py` 提供了一系列函数用于创建场次、注册选手、管理比赛和记录成绩。

### Session management

### 场次管理

```python
from data_manager import create_session, get_session, list_dates, list_sessions

create_session("2025-03-21", 1)                # create session
session = get_session("2025-03-21", 1)         # get session info
dates = list_dates()                            # list all dates with data
sessions = list_sessions("2025-03-21")          # list all sessions for a date
```

```python
from data_manager import create_session, get_session, list_dates, list_sessions

create_session("2025-03-21", 1)                # 创建场次
session = get_session("2025-03-21", 1)         # 获取场次信息
dates = list_dates()                            # 列出所有有数据的日期
sessions = list_sessions("2025-03-21")          # 列出某日期的所有场次
```

### Participant registration

### 选手注册

```python
from data_manager import register_participant, get_participant, get_all_participants

register_participant("2025-03-21", 1, "Men's 100m Freestyle", 1, "Zhang San", "101", "Hunan University")
info = get_participant("2025-03-21", 1, "Men's 100m Freestyle", 1)
all = get_all_participants("2025-03-21", 1, "Men's 100m Freestyle")
```

```python
from data_manager import register_participant, get_participant, get_all_participants

register_participant("2025-03-21", 1, "男子100米自由泳", 1, "张三", "101", "湖南大学")
info = get_participant("2025-03-21", 1, "男子100米自由泳", 1)
all = get_all_participants("2025-03-21", 1, "男子100米自由泳")
```

### Race management

### 比赛管理

```python
from data_manager import create_race, start_race, complete_race, get_race

race = create_race("2025-03-21", 1, "Men's 100m Freestyle", 2)   # create race (segments=2)
start_race(...)                                          # start (record actual start time)
complete_race(...)                                       # complete race
```

```python
from data_manager import create_race, start_race, complete_race, get_race

race = create_race("2025-03-21", 1, "男子100米自由泳", 2)   # 创建比赛（segments=2）
start_race(...)                                          # 发令（记录实际开始时间）
complete_race(...)                                       # 完成比赛
```

### Result recording

### 成绩记录

```python
from data_manager import record_score, get_scores

record_score("2025-03-21", 1, "Men's 100m Freestyle", 1, 1, 52000, 10)
scores = get_scores("2025-03-21", 1, "Men's 100m Freestyle", lane=1)
```

```python
from data_manager import record_score, get_scores

record_score("2025-03-21", 1, "男子100米自由泳", 1, 1, 52000, 10)
scores = get_scores("2025-03-21", 1, "男子100米自由泳", lane=1)
```

Data is stored as JSON under the `data/` directory for easy viewing and export.

数据以 JSON 格式保存在 `data/` 目录下，方便查看和导出。

## Auxiliary modules

## 辅助模块

- `shared_functions.py` – shared utility functions (e.g., delay test)
- `excel_writer.py` – Excel export
- `timer_window.py` – timer UI window (based on Tkinter)
- `config.py` – configuration definitions, can be exported/loaded as YAML

- `shared_functions.py` – 共享工具函数（如延迟测试）
- `excel_writer.py` – Excel 导出功能
- `timer_window.py` – 计时器 UI 窗口（基于 Tkinter）
- `config.py` – 配置定义，可导出/加载 YAML

## Common issues

## 常见问题

### Q1: "Sound file not found" error on startup

### Q1: 启动时提示 "找不到音效文件"

Make sure the five required WAV files exist in the `sound/` folder (see table above). You can place your own sound files and modify the `SOUND_FILES` dictionary accordingly.

确保 `sound/` 文件夹中存在所需的五个 WAV 文件（见上表）。可以将自己的音效文件放进去并修改 `SOUND_FILES` 字典中的文件名。

### Q2: Cannot connect to MQTT broker

### Q2: 无法连接 MQTT Broker

- Ensure broker is running (default `localhost:1883`).
- Use `mqtt_test.py` to check port and service status.
- Install Mosquitto (Windows) or use Docker: `docker run -d -p 1883:1883 eclipse-mosquitto`

- 确保 broker 正在运行（默认 `localhost:1883`）。
- 使用 `mqtt_test.py` 检查端口和服务状态。
- 安装 Mosquitto（Windows）或使用 Docker：`docker run -d -p 1883:1883 eclipse-mosquitto`

### Q3: WebSocket connection fails

### Q3: WebSocket 连接失败

- Start the Flask backend first (`python app.py`).
- Install `python-socketio[client]`: `pip install python-socketio[client]`
- If the referee backend is not needed, ESP.py will run in standalone mode and WebSocket functionality will be unavailable.

- 先启动 Flask 后端（`python app.py`）。
- 安装 `python-socketio[client]`：`pip install python-socketio[client]`
- 如果不需要裁判长控制，ESP.py 会以独立模式运行，WebSocket 功能不可用。

### Q4: Timer window does not appear

### Q4: 计时窗口不显示

- Tkinter is required (usually included with Windows).
- If still not showing, check for errors in `timer_window.py`.
- Press `w` to toggle window visibility.

- 需要安装 Tkinter（Windows 一般自带）。
- 若仍不显示，检查 `timer_window.py` 是否报错。
- 按 `w` 键切换窗口可见性。

### Q5: No response to key presses

### Q5: 按键无反应

- Ensure the console window running ESP.py is active (focused).
- Some software (e.g., other processes with admin privileges) may intercept keyboard events.
- Try running the command line as administrator.

- 确保运行 ESP.py 的控制台窗口是激活的（焦点在窗口上）。
- 某些软件（如管理员权限其他进程）可能抢占键盘事件。
- 尝试以管理员身份运行命令行。

## Developer notes

## 开发者说明

### Project directory structure

### 项目目录结构

```
SwimTimeLink/
├── app.py                     # Flask backend (referee UI)
├── config.py                  # global configuration class
├── data_manager.py            # data storage management
├── ESP.py                     # electronic starting gun main program
├── excel_writer.py            # Excel output
├── head_judgment.html         # referee HTML template (optional)
├── judgment.html              # judge HTML template
├── mqtt_test.py               # MQTT status check script
├── race_data.json             # race data (older format)
├── README.md                  # this file
├── requirements.txt           # Python dependencies
├── shared_functions.py        # shared functions
├── test.py / test_independent.py / test_main.py  # test scripts
├── timer_window.py            # timer window
├── sound/                     # sound effects folder
│   ├── first_whistle.wav
│   ├── second_whistle.wav
│   ├── take_your_mark.wav
│   ├── start.wav
│   └── man.wav
├── data/                      # runtime data storage (by date/session/event/lane)
└── src/                       # other source code (optional)
```

```
SwimTimeLink/
├── app.py                     # Flask 后端（裁判长界面）
├── config.py                  # 全局配置类
├── data_manager.py            # 数据存储管理
├── ESP.py                     # 电子发令枪主程序
├── excel_writer.py            # Excel 输出
├── head_judgment.html         # 裁判长 HTML 模板（可能）
├── judgment.html              # 裁判员 HTML 模板
├── mqtt_test.py               # MQTT 状态检查脚本
├── race_data.json             # 比赛数据（可能旧格式）
├── README.md                  # 本文件
├── requirements.txt           # Python 依赖
├── shared_functions.py        # 共享函数
├── test.py / test_independent.py / test_main.py  # 测试脚本
├── timer_window.py            # 计时器窗口
├── sound/                     # 音效文件夹
│   ├── first_whistle.wav
│   ├── second_whistle.wav
│   ├── take_your_mark.wav
│   ├── start.wav
│   └── man.wav
├── data/                      # 运行时数据存储（按日期/场次/项目/泳道）
└── src/                       # 其他源码（可选）
```

### Configuration persistence

### 配置持久化

`config.py` supports saving configuration to a YAML file and reloading:

`config.py` 支持将配置保存为 YAML 文件并重新加载：

```python
config.save_to_yaml("config.yaml")          # export current config
config.load_from_yaml("config.yaml")        # load config
```

```python
config.save_to_yaml("config.yaml")          # 导出当前配置
config.load_from_yaml("config.yaml")        # 加载配置
```

### 参与名单
Kolomovici(backend) 湖南大学物理与微电子科学学院

ssrszyrf(web)南京农业大学园艺学院

---

**Acknowledgements**  
Thanks to the NJAU (Nanjing Agricultural University) front-end team for their support! Looking forward to meeting you at the China University Swimming Championship in Ordos!  
The development team was unable to support the Hunan University Swimming League due to participation in the "China University Swimming Championship Finals", but persisted in completing the project.

**致谢**  
感谢 NJAU（南京农业大学）前端支持，期待在中国大学生游泳锦标赛鄂尔多斯相见！  
开发团队因参与"中国大学生游泳锦标赛 总决赛"未能到场支持湖南大学游泳校联赛，但坚持完成了项目开发。
```
