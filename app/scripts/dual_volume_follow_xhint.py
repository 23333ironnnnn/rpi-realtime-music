#!/usr/bin/env python3
"""
双 USB 声卡：根据 realtime_pos/current.json 里的 x_raw 相对 CENTER 左右分配音量。

默认：x < CENTER -> 左大声；x >= CENTER -> 右大声（与旧版一致，便于听感对比）。

环境变量（可选）：
  LEFT_CARD=2 RIGHT_CARD=3          # amixer 卡号，默认 2 / 3
  ALSA_CONTROL=Speaker              # 控件名；若无效可改为 PCM、Master 等
  CENTER=32768                      # 与 uint16 量级一致；若仍总偏一侧可改用 USE_X_NORM=1
  USE_X_NORM=0                      # 设为 1 时用 current.json 的 x_norm（0~1），以 0.5 分左右
  VOL_LO=15 VOL_HI=90               # 两侧音量 %
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

POS_FILE = Path(os.environ.get("POS_FILE", "/opt/rpi_realtime_music/realtime_pos/current.json"))

LEFT_CARD = os.environ.get("LEFT_CARD", "2")
RIGHT_CARD = os.environ.get("RIGHT_CARD", "3")
CONTROL = os.environ.get("ALSA_CONTROL", "Speaker")

CENTER = float(os.environ.get("CENTER", "32768.0"))
USE_X_NORM = os.environ.get("USE_X_NORM", "0").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)
VOL_LO = float(os.environ.get("VOL_LO", "15"))
VOL_HI = float(os.environ.get("VOL_HI", "90"))


def setv(card: str, pct: float) -> bool:
    r = subprocess.run(
        ["amixer", "-c", str(card), "sset", CONTROL, f"{int(pct)}%"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(f"amixer failed card={card} pct={pct}: {r.stderr or r.stdout}", file=sys.stderr)
        return False
    return True


def read_position() -> tuple[float, str] | None:
    """返回 (比较用标量, 模式说明)；失败返回 None。"""
    try:
        o = json.loads(POS_FILE.read_text(encoding="utf-8"))
        if USE_X_NORM:
            v = float(o.get("x_norm", 0.5))
            return v, "x_norm"
        return float(o.get("x_raw", 0.0)), "x_raw"
    except Exception:
        return None


def main() -> None:
    print(
        f"dual_volume: POS_FILE={POS_FILE} cards L={LEFT_CARD} R={RIGHT_CARD} "
        f"control={CONTROL} use_x_norm={USE_X_NORM} center={CENTER} lo/hi={VOL_LO}/{VOL_HI}",
        flush=True,
    )

    while True:
        got = read_position()
        if got is None:
            time.sleep(0.1)
            continue
        x, mode = got

        if USE_X_NORM:
            # 左半空间 -> 左大声；右半 -> 右大声
            left_loud = x < 0.5
        else:
            left_loud = x < CENTER

        if left_loud:
            L, R = VOL_HI, VOL_LO
        else:
            L, R = VOL_LO, VOL_HI

        setv(LEFT_CARD, L)
        setv(RIGHT_CARD, R)
        if USE_X_NORM:
            print(f"{mode}={x:.4f} (split=0.5) -> L={L:.0f} R={R:.0f}", flush=True)
        else:
            print(f"{mode}={x:.1f} center={CENTER:.1f} -> L={L:.0f} R={R:.0f}", flush=True)
        time.sleep(0.1)


if __name__ == "__main__":
    main()
