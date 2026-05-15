# SwimTimeLink 

朋友们非常抱歉，因为"中国大学生游泳锦标赛 总决赛"的缘故,该项目开发团队无法到场支持湖南大学游泳校联赛，但是我们依然坚持将此项目开发完成！
感谢NJAU(南京农业大学)前端的支持！期待与您们在中国大学生游泳锦标赛————鄂尔多斯相见！


#Still under development!
![169bf32a324d35644874aba760ec36a9_720](https://github.com/user-attachments/assets/e6684343-0612-425f-9cb4-7b8ba412de89)

This project aims to provide simple timing without an electronic timing board
Please run this in 'python3.10'

*First change the paths in config.

*Put your WAV files in a folder, also change the paths in ESP.py

Then run ./ESP.py (press'4',start the game;press '5' test the time relay)

GenShin niubi


# 🏊 泳池发令计时系统 (SwimTimeLink)

> **电子发令枪 + 裁判端计时 + 裁判长控制台** 三位一体游泳比赛计时解决方案

---

## 📋 项目概述

本项目是一套面向游泳比赛的**低成本、高精度、多终端**电子计时系统。无需昂贵的专业计时板，通过 Web 技术实现比赛全流程数字化管理。

### 核心工作流程

```
裁判长控制台 ──发令──► 后端服务器 ──广播──► ESP电子发令枪 (音效+计时)
                                         ──广播──► 裁判手机端 (分段计时)
                         │
                         ◄── 成绩上报 ── 裁判手机端 (8个泳道独立)
                         │
                         ── 实时推送 ──► 裁判长控制台 (成绩汇总展示)
```

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        裁判长控制台 (Web)                            │
│  head_judgment.html                                                  │
│  - 赛事导入: 配置日期/场次/比赛项目/分段数                           │
│  - 比赛控制: 选择比赛 → 一键发令 → 实时进度                         │
│  - 实时成绩: 8泳道 × N分段 动态表格                                  │
│  - 连接管理: HTTP健康检查 + WebSocket双向通信                        │
│  - 数据持久化: localStorage 保存赛事配置                             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP (REST) + WebSocket (Socket.IO)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     后端服务器 (Flask + SocketIO)                     │
│  app.py - 系统中枢                                                    │
│                                                                       │
│  HTTP API 路由:                                                       │
│  ├── /sync (POST/GET)       - 时间同步 + 连通性检测                  │
│  ├── /start_race (POST)     - 裁判长发令 → 通知ESP执行流程            │
│  ├── /esp_fire (POST)       - ESP实际发令时刻 → 记录start_time        │
│  ├── /record_time (POST)    - 裁判端成绩上报 (含网络延迟补偿)         │
│  ├── /get_scores (GET)      - 获取所有泳道/分段成绩                   │
│  ├── /get_race_status (GET) - 获取当前比赛状态                        │
│  ├── /register_participant  - 选手注册                                │
│  ├── /reset_race (POST)     - 重置当前比赛                            │
│  ├── /clear_participants    - 清空所有数据                            │
│  ├── /export_results (GET)  - 导出CSV成绩文件                         │
│  └── /judgment              - 裁判手机端页面                          │
│                                                                       │
│  WebSocket 事件:                                                      │
│  ├── score_update  - 成绩变更 → 实时推送所有客户端                    │
│  ├── race_start    - 发令成功 → 广播给所有裁判端                      │
│  ├── esp_status    - ESP状态更新 → 通知裁判长                         │
│  ├── race_reset    - 比赛重置 → 通知所有终端                          │
│  ├── judge_connected - 裁判端连接通知                                 │
│  └── ping/pong     - 心跳检测                                         │
│                                                                       │
│  进程管理: 自动启动/停止 ESP.py 子进程                                │
│  数据持久化: race_data.json (JSON文件存储)                            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ WebSocket (python-socketio)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ESP电子发令枪 (Python)                          │
│  ESP.py - 发令流程控制 + 音效播放 + 设备管理                        │
│                                                                       │
│  键盘快捷键:                                                          │
│  ├── 1: 四声短哨 (提示音)                                            │
│  ├── 2: 一声长哨 (预备音)                                            │
│  ├── 3: Take Your Mark (预备指令 + 计时器变红)                       │
│  ├── 4: 🔴 紧急手动发令 (直接电笛声 + 通知后端)                     │
│  ├── 5: 延迟测试 (检测所有设备延迟)                                  │
│  ├── a/A: 添加MQTT设备                                               │
│  ├── l/L: 列出所有设备                                               │
│  ├── t/T: 计时器变红                                                 │
│  ├── g/G: 计时器变绿 + 开始计时                                      │
│  ├── s/S: 停止计时                                                   │
│  ├── z/Z: 重置计时器                                                 │
│  ├── w/W: 显示/隐藏计时窗口                                          │
│  └── d/D: 独立延迟测试                                               │
│                                                                       │
│  自动发令流程 (由裁判长触发):                                         │
│  ① 接收 esp_start_race 事件                                          │
│  ② 播放 "Take Your Mark" 音效                                       │
│  ③ 计时器变为红色                                                   │
│  ④ 等待 1.5秒 (模拟裁判反应时间)                                    │
│  ⑤ 播放电笛声 (真正的发令时刻)                                      │
│  ⑥ POST /esp_fire 通知后端记录 start_time                           │
│  ⑦ 计时器变为绿色 + 开始计时                                        │
│  ⑧ 通过MQTT通知外围设备                                             │
│  ⑨ WebSocket广播 esp_status (fired)                                 │
│                                                                       │
│  MQTT管理: 支持动态添加/移除/控制外围计时设备                        │
│  计时窗口: Tkinter全屏计时器 (红/绿状态指示)                         │
│  音效: pygame.mixer 播放 WAV 音效文件                                │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP + WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   裁判手机端 (Web - 响应式)                          │
│  judgment.html - 泳道计时专用                                        │
│                                                                       │
│  功能:                                                               │
│  ├── 连接服务器 (IP/端口/泳道号配置)                                 │
│  ├── 时间同步 (NTP风格时钟偏移校准)                                  │
│  ├── 自动接收发令信号 (WebSocket监听)                                │
│  ├── 分段计时按钮 (自动生成N个分段)                                  │
│  ├── 成绩上报 (含网络延迟补偿)                                       │
│  ├── 连接状态指示 (HTTP + WebSocket 双协议)                         │
│  ├── 自动重连 (指数退避, 最多5次)                                    │
│  └── 心跳检测 (5秒间隔)                                              │
└─────────────────────────────────────────────────────────────────────┘
                           │ 存储
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     数据存储层                                        │
│                                                                       │
│  运行时: 内存字典 (scores, participants, current_race)               │
│  持久化: ┌─ race_data.json   - 选手信息 + 成绩记录                  │
│          ├─ data/ 目录       - 层级化文件存储 (可选)                 │
│          │   └─ {日期}/session_{场次}/{项目名}/lane_{泳道}/         │
│          │       ├── info.json     - 选手信息                        │
│          │       ├── results.json  - 分段成绩                        │
│          │       └── race.json     - 比赛元数据                      │
│          └─ CSV导出           - 成绩报表 (UTF-8 BOM编码)             │
└─────────────────────────────────────────────────────────────────────┘
```

### 📐 架构特点

| 特性 | 说明 |
|------|------|
| **星型拓扑** | 后端服务器是唯一的中枢，所有模块通过后端互联 |
| **双协议通信** | HTTP (REST API) + WebSocket (实时推送) |
| **延迟补偿** | 客户端上报click_time + client_send_time，服务器计算网络延迟并补偿 |
| **时序统一** | ESP的电笛声时刻 = 真正的 start_time (通过 /esp_fire 接口) |
| **多终端协同** | 1个裁判长台 + 8个裁判手机端 + 1个ESP发令枪 |

---

## 📁 项目文件结构

```
├── app.py                 # 🚀 后端服务器主程序 (Flask + SocketIO)
├── ESP.py                 # 🔫 电子发令枪 (音效/计时/设备管理)
├── head_judgment.html     # 👑 裁判长控制台 (Web界面)
├── judgment.html          # 📱 裁判手机端 (泳道计时)
├── data_manager.py        # 📂 层级化文件存储管理
├── shared_functions.py    # 🔗 共享函数模块 (函数引用传递)
├── timer_window.py        # ⏱️ Tkinter计时窗口 (红/绿状态)
├── excel_writer.py        # 📊 Excel数据处理工具 (辅助模块)
├── config.py              # ⚙️ 应用配置 (YAML)
├── mqtt_test.py           # 📡 MQTT状态检测工具
├── requirements.txt       # 📦 Python依赖清单
│
├── sound/                 # 🔊 音效文件
│   ├── first_whistle.wav  #   第一声哨
│   ├── second_whistle.wav #   第二声哨
│   ├── take_your_mark.wav #   预备指令
│   ├── start.wav          #   电笛声 (发令)
│   ├── man.wav            #   男声提示
│   └── no.wav             #   错误提示
│
├── data/                  # 💾 层级化数据存储
│   └── (自动生成)
│
├── test_result/           # 🧪 测试报告
│
└── .vscode/               # 🔧 VSCode配置
```

---

## 🚀 快速开始

### 环境要求

- **Python 3.10+** (推荐 3.10)
- 支持 WebSocket 的现代浏览器 (Chrome/Edge/Firefox)

### 安装

```bash
# 1. 克隆项目
git clone <项目地址>
cd SwimTimeLink

# 2. 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
# 启动后端服务器 (将自动启动ESP.py)
python app.py

# 访问:
# 裁判长控制台: http://localhost:5000
# 裁判手机端:   http://localhost:5000/judgment
```

### 使用流程

```
1️⃣ 启动服务器 → 打开裁判长控制台

2️⃣ 连接服务器
   ├── 填写 IP/端口 (默认 localhost:5000)
   └── 点击"连接" → 状态变为"已连接"

3️⃣ 配置赛事
   ├── 选择日期、输入赛事名称
   ├── 设置大场数 (场次数量)
   ├── 添加比赛 (选择性别/项目/类型)
   │   └── 项目分段数自动映射:
   │       50米=1段, 100米=2段, 200米=4段
   │       400米=8段, 800米=16段, 1500米=30段
   └── 保存赛事配置

4️⃣ 比赛控制
   ├── 选择当前大场 → 选择当前比赛
   ├── 确认比赛信息 (性别/项目/分段数)
   └── 点击"发令开始比赛"
       └── ESP自动执行: Take Your Mark → 1.5秒 → 电笛声

5️⃣ 裁判手机端
   ├── 连接同一服务器 → 输入泳道号
   ├── 自动接收发令信号
   ├── 逐段点击按钮上报成绩
   └── 按钮变绿色表示该分段已完成

6️⃣ 实时监控
   ├── 裁判长控制台自动刷新成绩表格
   ├── 支持手动刷新/清空/导出CSV
   └── 底部状态栏显示连接状态/发令时间
```

---

## 📡 通信协议

### HTTP API 接口

| 方法 | 路径 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/` | 裁判长控制台 | - | head_judgment.html |
| GET | `/judgment` | 裁判手机端 | - | judgment.html |
| GET | `/sync` | 连通性检测 | - | `{server_time, status}` |
| POST | `/sync` | 时间同步 | `{lane, client_time}` | `{server_time, rtt}` |
| POST | `/start_race` | 裁判长发令 | `{project_name, segments}` | `{status, message}` |
| POST | `/esp_fire` | ESP发令确认 | `{project_name, segments}` | `{start_time}` |
| POST | `/record_time` | 成绩上报 | `{lane, segment, click_time, client_send_time}` | `{compensated_time_ms}` |
| GET | `/get_scores` | 获取成绩 | `?lane=N` | `{scores, participants}` |
| GET | `/get_race_status` | 比赛状态 | - | `{race_active, project_name, ...}` |
| POST | `/register_participant` | 选手注册 | `{lane, participant}` | `{status}` |
| POST | `/reset_race` | 重置比赛 | - | `{status}` |
| POST | `/clear_participants` | 清空数据 | - | `{status}` |
| GET | `/export_results` | 导出CSV | - | 文件下载 |

### WebSocket 事件

| 事件 | 方向 | 描述 | 数据 |
|------|------|------|------|
| `esp_start_race` | 后端 → ESP | 裁判长发令 | `{project_name, segments}` |
| `esp_fire` | ESP → 后端 | 发令确认 | `{project_name, segments}` |
| `race_start` | 后端 → 所有 | 比赛开始 | `{project_name, segments, start_time}` |
| `score_update` | 后端 → 所有 | 成绩更新 | `{lane, segment, compensated_time_ms}` |
| `esp_status` | ESP → 后端 | 状态更新 | `{stage, timestamp}` |
| `race_reset` | 后端 → 所有 | 比赛重置 | `{message}` |
| `register_judge` | 裁判端 → 后端 | 注册泳道 | `{lane, device_info}` |
| `judge_connected` | 后端 → 裁判长 | 新裁判端接入 | `{lane, sid, timestamp}` |
| `ping/pong` | 双向 | 心跳检测 | `{time}` |

---

## ⏱️ 计时精度设计

### 发令时序

```
裁判长点击 [发令]
    │
    ▼
POST /start_race ──► 后端 ──► WebSocket → ESP
    │                              │
    │                      ESP播放 "Take Your Mark"
    │                      ESP计时器 → 红色
    │                      (等待 1.5 秒)
    │                              │
    │                      ESP播放 电笛声 ←── 真正的发令时刻
    │                              │
    │                      POST /esp_fire ──► 后端记录 start_time
    │                                         │
    │                                 WebSocket 广播 race_start
    │                                         │
    ◄────────── 所有裁判端收到发令信号 ──────────►
```

### 成绩补偿算法

```
click_time     = 裁判点击时的本地时间 (经时钟偏移校正)
client_send_time = 裁判端发送请求的本地时间
server_receive_time = 服务器接收时间

network_delay  = server_receive_time - client_send_time
raw_time       = click_time - start_time
compensated    = max(0, raw_time - network_delay / 2)
```

---

## 🔧 配置说明

### 后端配置 (app.py)

- **端口**: 默认 `5000`
- **CORS**: 已允许所有来源 (`cors_allowed_origins="*"`)
- **SocketIO**: eventlet异步模式, ping超时60s, 间隔25s
- **数据持久化**: `race_data.json` (自动加载/保存)

### ESP发令枪 (ESP.py)

- **Flask后端地址**: `http://localhost:5000` (可修改)
- **音效目录**: `./sound/` (需放置WAV文件)
- **MQTT Broker**: `localhost:1883` (可选, 用于扩展设备)
- **计时窗口**: Tkinter, 全屏显示, 支持隐藏/显示

### 裁判端 (judgment.html)

- **时间同步间隔**: 5秒
- **WebSocket超时**: 15秒
- **重连策略**: 指数退避 (3s, 6s, 9s, 12s, 15s), 最多5次
- **心跳间隔**: 5秒 (前台), 15秒 (后台)

---

## ⚠️ 常见问题

### 1. WebSocket 连接失败
```bash
# 检查服务器是否运行
curl http://localhost:5000/sync

# 检查端口占用
netstat -ano | findstr :5000
```

### 2. 音效不播放
```bash
# 检查音效文件是否存在
ls sound/
# 确保包含: first_whistle.wav, second_whistle.wav, 
#           take_your_mark.wav, start.wav, man.wav
```

### 3. MQTT 设备控制不可用
```bash
# MQTT是可选功能, 不影响核心计时
# 如需使用, 安装Mosquitto并启动服务:
#   net start mosquitto
# 或 Docker:
#   docker run -d -p 1883:1883 eclipse-mosquitto
```

### 4. 成绩数据丢失
- 服务器重启后会自动加载 `race_data.json`
- 如需备份, 可在服务器运行时通过 `/export_results` 导出CSV
- 层级文件存储 (data_manager.py) 提供结构化的文件备份方案

---

## 📌 关键技术点

| 技术 | 用途 |
|------|------|
| **Flask** | HTTP REST API 服务 |
| **Flask-SocketIO** | WebSocket 实时双向通信 |
| **eventlet** | 异步并发 (保证WebSocket稳定) |
| **python-socketio** | ESP端WebSocket客户端 |
| **pygame** | 音效播放 (WAV) |
| **pynput** | 键盘监听 (ESP物理按键) |
| **Tkinter** | 计时窗口UI |
| **paho-mqtt** | MQTT设备管理 (可选) |
| **pandas/openpyxl** | Excel成绩导出 |

---

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发建议

- 核心逻辑在 `app.py` (后端) 和 `ESP.py` (发令枪)
- 前端逻辑集中在 `head_judgment.html` 和 `judgment.html`
- 计时精度相关的修改需谨慎测试
- 新增API路由请同时在README和 `head_judgment.html` 中更新

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

---

## 🙏 致谢

- 南京农业大学 (NJAU) 前端技术支持
- 所有参与测试的裁判和运动员们

---
## 制作团队：
Kolomovici 湖南大学物理与微电子科学学院 （后端）
上善若水 自由如风~ 南京农业大学园艺学院 （前端）

YSYeleven 华东师范大学通信与电子工程学院 （测试）
YiCheng Han 湖南大学土木工程学院 （测试）
xinyicheng92 湖南大学电气工程学院（测试）

*Made with ❤️ for swimming competitions everywhere*
