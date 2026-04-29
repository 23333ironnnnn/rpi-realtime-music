from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: str) -> int:
    return int(os.environ.get(name, default), 10)


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None or str(v).strip() == "":
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Config:
    port: int
    inbox_dir: str
    max_upload_bytes: int
    basic_user: str
    upload_web_password: str
    run_pipeline_on_upload: bool
    run_pipeline_script: str
    run_pipeline_spawn_log: str

    @staticmethod
    def from_env() -> Config:
        return Config(
            port=_env_int("PORT", "8080"),
            inbox_dir=os.environ.get(
                "INBOX_DIR", "/opt/rpi_realtime_music/inbox_mp3"
            ),
            max_upload_bytes=_env_int("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)),
            basic_user=os.environ.get("BASIC_USER", "pi"),
            upload_web_password=os.environ.get("UPLOAD_WEB_PASSWORD", "").strip(),
            run_pipeline_on_upload=_env_bool("RUN_PIPELINE_ON_UPLOAD", False),
            run_pipeline_script=os.environ.get(
                "RUN_PIPELINE_SCRIPT", "/home/pi/run_pipeline.sh"
            ).strip(),
            run_pipeline_spawn_log=os.environ.get(
                "RUN_PIPELINE_SPAWN_LOG",
                "/opt/rpi_realtime_music/logs/pipeline_spawn.log",
            ).strip(),
        )
