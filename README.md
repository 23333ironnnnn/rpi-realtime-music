# RPi Realtime Music System / 树莓派实时音乐系统

A Raspberry Pi 5 realtime music demo pipeline with mobile upload, AI music generation, and position-driven dual-speaker volume control.  
一个基于 Raspberry Pi 5 的实时音乐演示系统：支持手机上传、AI 生成音乐、以及基于位置的双声道音量联动。

---

## 1. Overview / 项目简介

**EN**  
This project connects sensor signals, music generation, and playback control into one end-to-end demo flow:
1. Upload MP3 from mobile browser
2. Auto trigger pipeline
3. Generate prompt from bio/audio features
4. Call MiniMax to generate new music
5. Play on dual USB sound cards with position-based left/right volume

**中文**  
本项目将传感器信号、音乐生成与播放控制串联成完整演示链路：
1. 手机网页上传 MP3  
2. 自动触发流水线  
3. 基于生理/音频特征生成提示词  
4. 调用 MiniMax 生成新音乐  
5. 在双 USB 声卡播放，并根据位置动态调节左右音量

---

## 2. Key Features / 核心功能

- **Mobile Upload / 手机上传**: HTTP Basic auth web upload
- **Auto Pipeline / 自动流水线**: run after upload
- **AI Generation / AI 生成**: MiniMax music generation
- **Realtime Position Decode / 实时位置解析**: R60AMP1 serial decode to JSON
- **Dual Sound Card Control / 双声卡控音**: left-right volume follows position
- **Preflight Check / 一键体检**: quick health check before demo

---

## 3. Architecture / 系统架构

Phone Browser
   -> upload_web (Flask)
   -> inbox_mp3
   -> run_pipeline.sh
      -> feature extraction + prompt build
      -> MiniMax API
      -> generated_mp3
      -> dual-card playback (ALSA)
R60AMP1 serial
   -> r60amp1_decode.py
   -> realtime_pos/current.json
   -> dual_volume_follow_xhint.py




4. Project Structure / 项目结构
app/
  scripts/
    r60amp1_decode.py
    dual_volume_follow_xhint.py
    play_mp3_ffmpeg_alsa.sh
    demo_preflight.sh
  upload_web/
    main.py
    routes/
    services/
deploy/
  music-upload-web.service
RUNBOOK.md
README.md

5. Requirements / 环境要求
Raspberry Pi 5
Python 3.9+
2 x USB sound cards
R60AMP1 sensor (serial)
MiniMax API key
Linux with systemd

6. Quick Start / 快速开始
6.1 Preflight / 演示前检查
/opt/rpi_realtime_music/app/scripts/demo_preflight.sh
6.2 Restart core services / 重启核心服务
sudo systemctl restart r60amp1-decode dual-volume music-upload-web
6.3 Open upload page / 打开上传页面
http://<RASPBERRY_PI_IP>:8080/
6.4 Watch pipeline log / 观察流水线日志
tail -f /opt/rpi_realtime_music/logs/pipeline_spawn.log
7. Configuration / 配置说明
Create /opt/rpi_realtime_music/app/.env:

# MiniMax
MINIMAX_API_KEY=your_api_key_here
# Upload web
UPLOAD_WEB_PASSWORD=your_password_here
RUN_PIPELINE_ON_UPLOAD=1
RUN_PIPELINE_SCRIPT=/home/pi/run_pipeline.sh
Do NOT commit .env to git.
不要把 .env 提交到 Git 仓库。

8. Service Management / 服务管理
systemctl status r60amp1-decode dual-volume music-upload-web --no-pager
sudo systemctl restart r60amp1-decode dual-volume music-upload-web
sudo systemctl enable r60amp1-decode dual-volume music-upload-web
9. Common Issues / 常见问题
9.1 invalid api key
EN: Check .env key value and restart related services.
中文：检查 .env 中 MINIMAX_API_KEY 是否正确，并重启服务。
9.2 Position file stale / 位置数据不更新
EN: Restart r60amp1-decode, check serial device /dev/ttyUSB0.
中文：重启 r60amp1-decode，检查串口设备 /dev/ttyUSB0。
9.3 SDL/ALSA playback error (524)
EN: Use ffmpeg with explicit ALSA device (plughw:2,0 / plughw:3,0).
中文：使用显式 ALSA 设备播放，避免默认 ffplay。
10. Demo Checklist / 演示检查清单

 Services active / 三服务运行中

 Position JSON updating / 位置 JSON 实时更新

 Both USB cards detected / 双 USB 声卡识别正常

 Upload page reachable / 上传页面可访问

 New MP3 generated / 新音频成功生成
11. Security / 安全建议
Rotate leaked API keys/tokens immediately
若密钥泄露请立刻轮换
Keep repository secret-free (.env, logs, generated files)
仓库中不要包含 .env、日志和生成音频

12. License / 许可
For demo and research use.
用于演示与研究目的。


——————————————————————————————————————————————————————————————————————————————————


## Hardware Requirements / 硬件清单

### A. Required Hardware / 必需硬件

| Item | Minimum Spec | Qty | Notes |
|---|---|---:|---|
| Raspberry Pi | Raspberry Pi 5 (recommended 4GB/8GB RAM) | 1 | Main controller / 主控 |
| Power Adapter | Official 5V 5A USB-C PSU | 1 | Stable power is critical / 建议官方电源 |
| microSD Card | 32GB+ (Class 10/UHS-I) | 1 | OS + project files / 系统与项目存储 |
| mmWave Sensor | R60AMP1 (UART output) | 1 | Realtime position data / 实时位置 |
| USB-to-Serial Adapter | CH340/CP2102/FTDI (3.3V TTL) | 1 | Sensor UART to Pi USB |
| USB Sound Card | Plug-and-play USB audio | 2 | Left/Right channel routing / 左右声道 |
| Speakers / Amplifier | Active speakers or amp+speakers | 2 channels | For dual output demo / 双通道播放 |
| Audio Cables | 3.5mm / RCA as needed | 2+ | Match your sound cards / 按声卡接口选 |

### B. Optional but Recommended / 可选但推荐

| Item | Purpose |
|---|---|
| Ethernet cable | More stable network during setup / 调试更稳定 |
| USB powered hub | Avoid power drop on multiple USB devices / 多设备供电更稳 |
| Cooling fan/case | Keep Pi 5 stable under long runs / 长时间运行更稳定 |
| HDMI display + keyboard | Local debug convenience / 本地调试方便 |

### C. Mobile Upload Side / 手机上传侧

| Item | Requirement |
|---|---|
| Smartphone | iOS or Android, modern browser |
| Network | Same hotspot/LAN as Raspberry Pi |
| Browser | Safari/Chrome access to `http://<PI_IP>:8080/` |

---

## Hardware Connection / 硬件连接说明

### 1) Sensor Wiring / 雷达接线
- **R60AMP1 TX -> USB-UART RX**
- **R60AMP1 RX -> USB-UART TX**
- **GND -> GND**
- **VCC -> Correct supply voltage per module datasheet**  
  (Do not guess voltage; confirm from vendor docs.)  
  （供电电压请按模块资料确认，勿凭经验乱接）

### 2) USB Topology / USB 设备拓扑
- USB Sound Card #1 -> playback left path  
- USB Sound Card #2 -> playback right path  
- USB-UART adapter (sensor) -> `/dev/ttyUSB*`

### 3) Device Check Commands / 设备自检命令

# Sound cards
aplay -l

# Serial devices
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null

# Full demo preflight
/opt/rpi_realtime_music/app/scripts/demo_preflight.sh

Minimum Working Set / 最小可运行组合
If you only want to verify upload + generation first:
若你只想先验证“上传+生成”链路，最低配置：

Raspberry Pi 5 + power + microSD
Network connection
One USB sound card (or no playback for pipeline-only test)
MiniMax API key configured
For full demo (position-driven dual-volume):
若要完整演示“位置驱动双声道控音”：

Add R60AMP1 + USB-UART adapter
Use two USB sound cards
Keep r60amp1-decode and dual-volume services active

