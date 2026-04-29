from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


def spawn_run_pipeline(
    script_path: str,
    log_path: str | None,
) -> bool:
    """
    Start run_pipeline.sh in the background (non-blocking).
    Returns True if the process was started, False on configuration error.
    """
    script = Path(script_path)
    if not script.is_file():
        log.error("RUN_PIPELINE_SCRIPT not found: %s", script)
        return False
    try:
        if not os.access(script, os.X_OK):
            log.warning("RUN_PIPELINE_SCRIPT not executable, trying bash: %s", script)
    except OSError as e:
        log.error("RUN_PIPELINE_SCRIPT not accessible: %s: %s", script, e)
        return False

    env = os.environ.copy()
    argv = ["/bin/bash", str(script)]

    try:
        if log_path:
            lp = Path(log_path)
            lp.parent.mkdir(parents=True, exist_ok=True)
            with open(lp, "ab") as lf:
                proc = subprocess.Popen(
                    argv,
                    stdin=subprocess.DEVNULL,
                    stdout=lf,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    env=env,
                )
        else:
            proc = subprocess.Popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                env=env,
            )
    except OSError as e:
        log.error("failed to spawn pipeline: %s", e)
        return False

    log.info("pipeline_spawned pid=%s script=%s", proc.pid, script)
    return True
