#!/usr/bin/env bash
set -u

# Demo preflight for Raspberry Pi realtime music stack.
# Checks service status, position file freshness, sound cards, and latest output.
#
# Position JSON may not touch mtime every sub-second; default max age is relaxed.
# Tight check: POS_MAX_AGE_SECONDS=5 /opt/rpi_realtime_music/app/scripts/demo_preflight.sh

PASS=0
FAIL=0

ok() {
  echo "PASS: $1"
  PASS=$((PASS + 1))
}

ng() {
  echo "FAIL: $1"
  FAIL=$((FAIL + 1))
}

check_service() {
  local svc="$1"
  local st
  st="$(systemctl is-active "$svc" 2>/dev/null || true)"
  if [[ "$st" == "active" ]]; then
    ok "service $svc is active"
  else
    ng "service $svc is $st"
  fi
}

echo "== Demo Preflight =="
echo "time: $(date '+%F %T')"
echo

echo "-- Services --"
check_service "r60amp1-decode"
check_service "dual-volume"
check_service "music-upload-web"
echo

POS_FILE="/opt/rpi_realtime_music/realtime_pos/current.json"
POS_MAX_AGE="${POS_MAX_AGE_SECONDS:-20}"
echo "-- Position Feed --"
if [[ -f "$POS_FILE" ]]; then
  now_ts="$(date +%s)"
  mod_ts="$(date -r "$POS_FILE" +%s 2>/dev/null || echo 0)"
  age=$((now_ts - mod_ts))
  if [[ "$age" -le "$POS_MAX_AGE" ]]; then
    ok "position file exists and is fresh (${age}s, max ${POS_MAX_AGE}s)"
  else
    ng "position file exists but stale (${age}s, max ${POS_MAX_AGE}s)"
  fi
else
  ng "position file missing: $POS_FILE"
fi
echo

echo "-- Playback Cards --"
if aplay -l 2>/dev/null | grep -q "card 2:"; then
  ok "found card 2"
else
  ng "card 2 not found"
fi
if aplay -l 2>/dev/null | grep -q "card 3:"; then
  ok "found card 3"
else
  ng "card 3 not found"
fi
echo

GEN_DIR="/opt/rpi_realtime_music/generated_mp3"
echo "-- Generated Audio --"
if [[ -d "$GEN_DIR" ]]; then
  latest="$(ls -1t "$GEN_DIR"/*.mp3 2>/dev/null | head -n 1 || true)"
  if [[ -n "$latest" && -f "$latest" ]]; then
    size="$(wc -c < "$latest" | tr -d ' ')"
    if [[ "$size" -gt 0 ]]; then
      ok "latest mp3: $latest (${size} bytes)"
    else
      ng "latest mp3 is empty: $latest"
    fi
  else
    ng "no mp3 found in $GEN_DIR"
  fi
else
  ng "directory missing: $GEN_DIR"
fi
echo

echo "== Result =="
echo "PASS: $PASS"
echo "FAIL: $FAIL"
if [[ "$FAIL" -eq 0 ]]; then
  echo "OVERALL: PASS"
  exit 0
else
  echo "OVERALL: FAIL"
  echo "Hint: systemctl status r60amp1-decode dual-volume music-upload-web --no-pager"
  echo "Hint: if only position is stale, sudo systemctl restart r60amp1-decode"
  exit 1
fi
