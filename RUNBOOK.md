# RPi5 毫米波音乐系统 RUNBOOK（当前可复现版）

## 0. 前提
- 树莓派5
- 呼吸心率雷达可输出串口数据
- MiniMax API Key 可用
- 已有目录：`/opt/rpi_realtime_music`

## 网页上传（手机浏览器，无需 scp、无需写代码）

适合：手机与树莓派在同一热点 / 同一局域网；树莓派上已安装并启用 `music-upload-web` 服务（见工程 `deploy/music-upload-web.service`）。

### 一步步怎么做

1. **让手机和树莓派连同一个 WiFi**（例如手机开热点，树莓派连该热点）。
2. **查树莓派的 IP**：在电脑上用 SSH 登录树莓派，执行 `hostname -I`，记下**第一段数字**（例如 `192.168.43.206`）。树莓派重启后 IP 可能变化，每次演示前可重新查一次。
3. **手机打开浏览器**（Safari / Chrome 均可），在地址栏输入：`http://<上面记下的IP>:8080/`  
   - 必须是 **http**（不是 https）；端口 **8080** 若改过，以树莓派 `app/.env` 里 `PORT` 为准。
4. **出现登录框时**：用户名一般为 `pi`（若在 `.env` 里改过 `BASIC_USER` 则用改后的）；密码为 `.env` 中的 `UPLOAD_WEB_PASSWORD`（可与 SSH 密码不同）。
5. **进入页面后**：选择本地 `.mp3` 文件并上传；页面提示成功即表示文件已落到 `inbox_mp3`。
6. **上传后是否自动跑一遍流水线**：在树莓派 `app/.env` 中设置 `RUN_PIPELINE_ON_UPLOAD=1`，并保证 `RUN_PIPELINE_SCRIPT` 指向可执行的 `run_pipeline.sh`（默认 `/home/pi/run_pipeline.sh`），且 **同一 `.env` 里已配置 `MINIMAX_API_KEY`**（上传服务通过 systemd 读 `.env` 后，子进程会继承该环境）。上传接口返回 JSON 里会有 `pipeline_spawned: true/false`；详细日志见 `RUN_PIPELINE_SPAWN_LOG`（默认 `logs/pipeline_spawn.log`）。若设为 `0`，则需像以往一样在 SSH 里手动执行 `~/run_pipeline.sh`。
7. **若打不开网页**：确认手机与树莓派在同一网络；确认 IP 未变；在树莓派上执行 `systemctl status music-upload-web` 是否为 `active`；若开了防火墙需放行端口（如 `ufw allow 8080/tcp`）。

### 安全说明（必读）

- 当前为 **HTTP 明文**，仅适合**内网演示 / 可信环境**；同热点内存在被嗅探密码的理论风险。
- **勿将** `.env` 真实密码**提交到 Git**；协作时各自在树莓派本地配置。

## 1. 启动采集（bio/pos）
python3 /opt/rpi_realtime_music/app/scripts/dual_serial_raw_to_json.py

## 2. 上传音频（Mac）
scp /path/to/demo.mp3 pi@<PI_IP>:/opt/rpi_realtime_music/inbox_mp3/

## 本次成功记录（YYYY-MM-DD）

- 一键脚本：`~/run_pipeline.sh`
- 成功执行命令：
  - `chmod +x ~/run_pipeline.sh`
  - `export MINIMAX_API_KEY='***'`
  - `~/run_pipeline.sh`
- 成功结果：
  - 任务状态更新到 `AUDIO_READY`
  - 生成文件：`/opt/rpi_realtime_music/generated_mp3/<task_id>.mp3`
  - 可正常播放
- 备注：
  - 当前控音演示采用单声卡与模拟 `x_hint`
  - 真实 R60AMP1 轨迹解析作为下一阶段

  ## 本次成功记录（2026-04-14）

### 环境
- 设备：Raspberry Pi 5
- 传感器：R60ABD1（呼吸心率）、R60AMP1（轨迹）
- 声卡：USB Audio（当前单声卡演示）
- 目录：`/opt/rpi_realtime_music`

### 已跑通链路
1. MP3 上传触发任务创建
2. 生理窗口提取（`sample_count > 0`）
3. 音频特征提取（duration/sample_rate/channels/bit_rate）
4. 固定提示词 + 生理 + 音频特征融合生成 `qwen_input`
5. 生成 `prompt_final`
6. MiniMax 调用成功并落盘：
   - `base_resp.status_code = 0`
   - 输出文件：`/opt/rpi_realtime_music/generated_mp3/e46d9ed9-b864-4eff-94d8-7c0285d2bd81.mp3`
   - 大小约：2.4MB
7. 单声卡播放成功
8. 使用模拟 `x_hint` 完成“位置驱动音量变化”演示

### 一键脚本
- 运行脚本：`~/run_pipeline.sh`
- 运行方式：
  ```bash
  chmod +x ~/run_pipeline.sh
  export MINIMAX_API_KEY='***'
  ~/run_pipeline.sh

  备份
树莓派备份包：
/home/pi/backup_mvp_20260414_190807.tar.gz
Mac 备份包：
/Users/a1234/Desktop/未命名文件夹/pi music/backups/backup_mvp_20260414_190807.tar.gz


CENTER=50000.0 

# RPi5 毫米波联动音乐系统 RUNBOOK（最终版）

## 1. 功能目标
- Mac 上传 MP3 -> 树莓派自动触发
- 呼吸心率 + 音频特征生成提示词
- 调用 MiniMax 生成新音频
- 双声卡播放（左/右）
- 位置雷达驱动左右音量（靠近哪边哪边大）

---

## 2. 关键路径
- 上传目录：`/opt/rpi_realtime_music/inbox_mp3`
- 任务目录：`/opt/rpi_realtime_music/logs/tasks`
- 生成音频：`/opt/rpi_realtime_music/generated_mp3`
- 位置实时：`/opt/rpi_realtime_music/realtime_pos/current.json`
- 位置解码脚本：`/opt/rpi_realtime_music/app/scripts/r60amp1_decode.py`
- 双声卡控音脚本：`/opt/rpi_realtime_music/app/scripts/dual_volume_follow_xhint.py`
- 流水线脚本：`/opt/rpi_realtime_music/app/scripts/run_pipeline.sh`

---

## 3. 启动顺序（演示标准流程）

### 3.1 清场
```bash
/opt/rpi_realtime_music/app/scripts/stop_all.sh
pkill -f run_pipeline.sh || true