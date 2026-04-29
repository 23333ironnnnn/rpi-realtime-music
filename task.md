---
name: 树莓派5 + 毫米波雷达 + USB声卡 MVP 分步计划（超细且可测试）
overview: 基于现有PRD与文档结构，并结合你实际硬件（树莓派5、毫米波位置雷达、毫米波呼吸心率雷达、USB声卡），输出超细粒度MVP实施计划，确保每个任务都可单独测试与验收。
todos:
  - id: A-baseline
    content: 完成硬件基线A1~A12并通过设备识别、串口别名与健康检查验收
    status: pending
  - id: B-input
    content: 完成输入链路B1~B12并通过上传触发、实时写入与断线重连验收
    status: pending
  - id: C-prompt
    content: 完成提示词链路C1~C10并通过窗口提取、Qwen输出与提示词落盘验收
    status: pending
  - id: D-minimax
    content: 完成生成链路D1~D10并通过下载落盘、重试超时与日志验收
    status: pending
  - id: E-playback
    content: 完成播放控音E1~E12并通过双声卡并发和坐标音量映射验收
    status: pending
  - id: F-orchestrator
    content: 完成编排守护F1~F10并通过端到端延迟与MVP最终验收
    status: pending
isProject: false
---

# 树莓派5 + 毫米波雷达 + USB声卡 MVP 分步计划（超细且可测试）

## 0. 硬件前提（按你当前设备）
- 主控：树莓派5
- 传感器A：毫米波呼吸心率雷达（USB/串口）
- 传感器B：毫米波位置雷达（USB/串口）
- 音频输出：USB 转音频模块（外置声卡）+ 树莓派本机声卡（或第二个 USB 声卡）
- 开发端：Mac（通过 `scp` 上传 MP3）

## 1. MVP目标（明确可验收）
- 上传 MP3 后自动触发任务
- 采集“上传时刻附近”的呼吸心率数据，生成动态提示词
- 动态提示词 + 固定提示词调用 MiniMax 生成 MP3
- 实时读取位置坐标，控制两个音频输出音量大小（靠近哪边哪边更大）

## 2. 目录约定（与PRD一致）
- `/opt/rpi_realtime_music/inbox_mp3`（文件夹1，上传入口）
- `/opt/rpi_realtime_music/realtime_bio/current.json`（当前呼吸心率）
- `/opt/rpi_realtime_music/realtime_bio/ringbuffer.jsonl`（短窗口缓冲）
- `/opt/rpi_realtime_music/realtime_pos/current.json`（当前坐标）
- `/opt/rpi_realtime_music/generated_mp3`（生成音频）
- `/opt/rpi_realtime_music/prompts`（提示词快照）
- `/opt/rpi_realtime_music/logs`（日志）

## 3. 超细任务拆分（每项可测试）

### Milestone A：硬件与系统基线（A1~A12）
A1. 树莓派系统更新完成
- 测试：`uname -a`、`python3 --version` 正常

A2. 插上两个雷达与声卡，确认设备被识别
- 测试：`lsusb` 能看到3个外设（2雷达+USB声卡）

A3. 确认串口设备节点
- 测试：`ls /dev/ttyUSB* /dev/ttyACM*` 至少出现2个可用串口

A4. 确认音频设备列表
- 测试：`aplay -l` 显示至少2个播放设备

A5. 为两个雷达建立稳定设备名（udev）
- 测试：出现 `/dev/radar_bio` 与 `/dev/radar_pos`

A6. 重插雷达后设备名不变
- 测试：再次检查别名仍正确

A7. 创建项目目录结构
- 测试：关键目录全部存在

A8. 创建 Python venv
- 测试：激活后 `which python` 指向 venv

A9. 安装依赖
- 测试：`pip list` 可看到核心包（serial/httpx/aiohttp等）

A10. 配置 `.env`
- 测试：程序启动时能加载配置（不报缺失）

A11. 建立日志目录与写权限
- 测试：可成功写入测试日志

A12. 建立健康检查空服务
- 测试：`/health` 返回 200

### Milestone B：输入链路（B1~B12）
B1. Mac 到树莓派 `scp` 上传单文件
- 测试：文件进入 `inbox_mp3`

B2. 上传同名文件覆盖策略确定（重命名或拒绝）
- 测试：行为符合预期且有日志

B3. watcher 仅监听 `.mp3`
- 测试：上传 `.txt` 不触发

B4. watcher 去抖（防重复触发）
- 测试：同一文件只触发1次

B5. watcher “写入完成”检测
- 测试：大文件上传中不提前触发

B6. 呼吸心率串口读取循环跑通
- 测试：每秒能收到数据帧

B7. 呼吸心率解析为标准结构
- 测试：得到字段 `ts/hr/rr/confidence`

B8. `realtime_bio/current.json` 覆盖写
- 测试：文件内容持续刷新，仅保留最新值

B9. `realtime_bio/ringbuffer.jsonl` 追加写
- 测试：有连续行，且时间递增

B10. 位置雷达串口读取循环跑通
- 测试：可收到坐标帧

B11. 位置解析并写 `realtime_pos/current.json`
- 测试：左右移动时 `x` 值有连续变化

B12. 断开传感器后的异常处理
- 测试：日志有错误，进程不中断且自动重连

### Milestone C：提示词链路（C1~C10）
C1. 任务ID生成
- 测试：每次触发生成唯一 `task_id`

C2. 记录上传时间戳 `T_upload`
- 测试：任务日志有精确时间

C3. 提取 `T_upload ± N秒` 生理窗口
- 测试：返回样本数量 > 0（有数据时）

C4. 生理特征聚合（均值/方差/峰值）
- 测试：固定输入得到固定输出

C5. 固定提示词模板文件化
- 测试：模板可单独加载

C6. 本地Qwen服务最小可用（可先stub）
- 测试：POST 请求返回文本

C7. 动态提示词生成
- 测试：内容非空，长度在设定范围

C8. 固定+动态提示词合并
- 测试：结果包含两部分内容

C9. 提示词快照落盘
- 测试：`prompts/<task_id>.prompt.txt` 存在

C10. 无生理数据时降级策略
- 测试：仍能生成默认提示词

### Milestone D：MiniMax 生成链路（D1~D10）
D1. 请求参数构建
- 测试：字段完整（model/prompt/format）

D2. 提交请求
- 测试：收到可解析响应

D3. 异步任务轮询（如需）
- 测试：状态迁移正常

D4. 下载音频文件
- 测试：`generated_mp3/<task_id>.mp3` 存在且>0字节

D5. 音频格式校验
- 测试：`ffprobe` 能识别为音频流

D6. 网络超时处理
- 测试：超时时任务状态为失败并可重试

D7. 401/5xx重试策略
- 测试：按配置次数重试后给出最终状态

D8. 失败任务日志
- 测试：`logs/tasks/<task_id>.json` 含错误信息

D9. 成功任务日志
- 测试：记录耗时、提示词摘要、输出路径

D10. 速率限制保护（MVP简版）
- 测试：短时间多任务不会压垮API

### Milestone E：播放与坐标控音（E1~E12）
E1. 声卡A独立播放测试
- 测试：声卡A有声音

E2. 声卡B独立播放测试
- 测试：声卡B有声音

E3. 两声卡并发播放同文件
- 测试：两侧同步可听

E4. 位置 `x` 映射左右音量函数
- 测试：`x=-1` 左大右小；`x=1` 右大左小

E5. 音量上下限裁剪
- 测试：音量始终在设定范围内

E6. 音量平滑（EMA）
- 测试：快速移动时无明显突变

E7. 坐标更新周期 50~100ms
- 测试：定时循环周期在目标范围

E8. 坐标抖动抑制
- 测试：静止时音量稳定不抖动

E9. 坐标丢失回退到中值
- 测试：断开位置流后音量回中间值

E10. 播放中切换新任务
- 测试：旧播放可停，新播放可起

E11. 生成失败时播放降级策略
- 测试：失败不崩溃，可保持待机或播放提示音

E12. 声卡断开异常处理
- 测试：日志可见且主进程不崩溃

### Milestone F：编排、守护、验收（F1~F10）
F1. 状态机接入全链路
- 测试：`WAIT_UPLOAD -> ANALYZE -> GENERATE -> PLAY -> DONE`

F2. 单任务全链路日志追踪
- 测试：通过 `task_id` 可串起所有阶段

F3. 队列串行处理
- 测试：连续上传3个文件按顺序执行

F4. 健康检查加入关键依赖状态
- 测试：传感器/音频异常时健康状态变化

F5. systemd 服务安装
- 测试：`systemctl status` 正常

F6. 开机自启验证
- 测试：重启后服务自动运行

F7. 崩溃自动拉起验证
- 测试：手动kill后自动重启

F8. 端到端延迟统计
- 测试：记录10次上传的P50/P90

F9. 听感验收（左中右移动）
- 测试：靠近哪边哪边明显更大

F10. MVP验收报告
- 测试：输出通过/失败项与后续优化清单

## 4. 7天执行安排（可直接照做）
- Day1：A1~A12
- Day2：B1~B12
- Day3：C1~C10
- Day4：D1~D10
- Day5：E1~E8
- Day6：E9~E12 + F1~F6
- Day7：F7~F10

## 5. 每日最小交付物（必须落盘）
- `docs/daily/dayX_checklist.md`：当天任务通过记录
- `docs/daily/dayX_issues.md`：问题与修复
- `logs/tasks/*.json`：任务证据

## 6. MVP通过标准（最终）
- 能从 Mac 上传 mp3 并自动触发完整流程
- 能结合呼吸心率生成动态提示词并成功调用 MiniMax
- 能依据位置坐标稳定控制双声卡音量
- 系统异常可恢复，日志可追踪