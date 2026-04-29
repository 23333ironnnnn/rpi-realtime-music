#!/usr/bin/env bash
# Play MP3 via ALSA without SDL/ffplay (avoids "Unknown error 524" on Pi + PipeWire).
# Usage: play_mp3_ffmpeg_alsa.sh <file.mp3>
# Optional: PLAY_ALSA_DEVICE=plughw:3,0 play_mp3_ffmpeg_alsa.sh file.mp3
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "usage: $0 <path-to.mp3>" >&2
  exit 1
fi
MP3="$1"
DEV="${PLAY_ALSA_DEVICE:-plughw:2,0}"
exec ffmpeg -nostdin -hide_banner -loglevel error -i "$MP3" -f alsa "$DEV"
