#!/usr/bin/env python3
"""
R60AMP1 轨迹协议（82 02）二进制解析，持续写入 realtime_pos/current.json。

对话里约定：持续写入 realtime_pos/current.json，供控音与排查（watch current.json）。

注意：雷达输出为二进制帧，不是「按行文本」。旧版用 UTF-8 + \\n 切行会导致永远调不到 write_current。
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SERIAL_PORT = os.environ.get("R60AMP1_SERIAL", "/dev/ttyUSB0")
BAUD = int(os.environ.get("R60AMP1_BAUD", "115200"), 10)
OUT_PATH = Path(os.environ.get("R60AMP1_OUT", "/opt/rpi_realtime_music/realtime_pos/current.json"))
# 与控音脚本一致的中间位置（毫米波坐标系，按你的资料可改）
CENTER = float(os.environ.get("CENTER", "50000.0"))
# 轨迹帧尾部长度（示例帧以 3 字节结尾，若解析错位可改为 0 试）
FOOTER_LEN = int(os.environ.get("R60AMP1_FOOTER_LEN", "3"), 10)

HDR = b"\x53\x59"
TRAJ = b"\x82\x02"


def write_current(
    x_raw: float,
    y_raw: float,
    x_hint: float,
    *,
    raw_hex: str,
    payload_hex: str,
    target_id: int | None,
    sub: int,
    x_norm: float,
) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": "pos",
        "port": SERIAL_PORT,
        "raw_hex": raw_hex,
        "payload_hex": payload_hex,
        "target_id": target_id,
        "sub": sub,
        "x_raw": x_raw,
        "y_raw": y_raw,
        "x_hint": x_hint,
        "x_norm": x_norm,
    }
    tmp = OUT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(OUT_PATH)


def x_hint_from_raw(x_raw: float) -> float:
    """
    以 CENTER 为「中点」映射到 ~0..1：x_raw << CENTER 时接近 0（偏左），>> CENTER 时接近 1（偏右）。
    当 x_raw 只有 1、2 而 CENTER=50000 时，x_hint 会压在 0 附近，这是正常现象。
    若希望「小范围也能拉开左右」，可减小环境变量 X_HINT_SPAN（默认 65535）。
    """
    span = float(os.environ.get("X_HINT_SPAN", "65535.0"))
    if span <= 0:
        span = 65535.0
    return max(0.0, min(1.0, (x_raw - CENTER) / span + 0.5))


def x_norm_from_raw(x_raw: float) -> float:
    """把 X 直接按 0..65535 归一化，便于控音脚本用「相对位置」而非 CENTER。"""
    return max(0.0, min(1.0, x_raw / 65535.0))


def parse_one_frame(buf: bytes) -> tuple[int, dict] | tuple[int, None]:
    """
    从 buf 开头尝试解析一帧；成功返回 (消耗字节数, 字段)，失败返回 (1, None) 用于丢一字节重新同步。
    格式：53 59 | 82 02 | len_hi len_lo | payload(len) | footer(FOOTER_LEN)
    len 为 big-endian 16 位（与资料「00 0b」一致）。
    """
    if len(buf) < 6 + FOOTER_LEN:
        return 0, None
    if buf[:2] != HDR or buf[2:4] != TRAJ:
        return 1, None
    ln = int.from_bytes(buf[4:6], "big")
    total = 6 + ln + FOOTER_LEN
    if len(buf) < total:
        return 0, None
    frame = buf[:total]
    payload = buf[6 : 6 + ln]

    # 资料示例：payload 前 2 字节常为「目标/类型」如 01 64（不是 uint16 LE 的 target_id）
    # X/Y 为 payload[2:4]、[4:6] 小端 uint16（与资料「X 坐标 / Y 坐标」一致）
    if len(payload) < 6:
        return total, None
    target_id = int(payload[0])
    sub = int(payload[1])
    x_raw = float(int.from_bytes(payload[2:4], "little"))
    y_raw = float(int.from_bytes(payload[4:6], "little"))
    xh = x_hint_from_raw(x_raw)
    xn = x_norm_from_raw(x_raw)
    data = {
        "raw_hex": frame.hex(),
        "payload_hex": payload.hex(),
        "target_id": target_id,
        "sub": sub,
        "x_raw": x_raw,
        "y_raw": y_raw,
        "x_hint": xh,
        "x_norm": xn,
    }
    return total, data


def main() -> None:
    try:
        import serial
    except ImportError:
        print("需要安装: pip install pyserial 或 apt install python3-serial", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(SERIAL_PORT):
        print(f"串口不存在: {SERIAL_PORT}（检查接线与设备名 /dev/ttyUSB*）", file=sys.stderr)
        sys.exit(1)

    print(
        f"r60amp1_decode: {SERIAL_PORT} @ {BAUD} -> {OUT_PATH} (binary 82 02), CENTER={CENTER}",
        flush=True,
    )
    ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0.2)
    buf = bytearray()
    try:
        while True:
            chunk = ser.read(4096)
            if not chunk:
                time.sleep(0.01)
                continue
            buf.extend(chunk)

            while True:
                i = buf.find(HDR)
                if i < 0:
                    # 保留尾部，避免帧头 53 59 被切到两次 read 之间
                    if len(buf) > 4096:
                        del buf[:-2000]
                    break
                if i > 0:
                    del buf[:i]
                if len(buf) < 6:
                    break
                consumed, data = parse_one_frame(bytes(buf))
                if consumed == 0:
                    break
                if data is None:
                    del buf[0:1]
                    continue
                del buf[:consumed]
                write_current(
                    data["x_raw"],
                    data["y_raw"],
                    data["x_hint"],
                    raw_hex=data["raw_hex"],
                    payload_hex=data["payload_hex"],
                    target_id=data["target_id"],
                    sub=data["sub"],
                    x_norm=data["x_norm"],
                )
                print(
                    f"x_raw={data['x_raw']:.1f} y_raw={data['y_raw']:.1f} "
                    f"x_hint={data['x_hint']:.3f} x_norm={data['x_norm']:.3f} sub={data['sub']}",
                    flush=True,
                )
    finally:
        ser.close()


if __name__ == "__main__":
    main()
