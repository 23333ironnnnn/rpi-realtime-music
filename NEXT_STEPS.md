# NEXT STEPS（从当前MVP升级）

## P0（优先）
1. 把 API Key 移到 `.env`，避免命令行泄露
2. 把当前脚本收敛到单入口 orchestrator（减少手动步骤）
3. 给每个阶段写 stage 更新：UPLOADED -> PROMPT_READY -> AUDIO_READY -> PLAYING
