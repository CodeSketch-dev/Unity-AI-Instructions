#!/usr/bin/env bash
# Generic FIFO Editor lock with heartbeat. Usage:
#   editor_lock.sh acquire <agent> <task>   (blocks until it is your turn; max wait 20 min)
#   editor_lock.sh touch | release | status
# State lives in <project>/Temp/agent-lock (outside Assets). mkdir is atomic on all platforms.
D="${LOCK_DIR:-Temp/agent-lock}"; HOLD="$D/holder"; Q="$D/queue"; STALE="${STALE_SEC:-300}"
mkdir -p "$Q"
now() { date +%s; }
age() { echo $(( $(now) - $(cat "$HOLD/beat" 2>/dev/null || echo 0) )); }
case "$1" in
acquire)
  T="$Q/$(date +%s%N)_$2"; echo "$3" > "$T"; end=$(( $(now) + 1200 ))
  while [ "$(now)" -lt "$end" ]; do
    if [ -d "$HOLD" ] && [ "$(age)" -gt "$STALE" ]; then echo "stale holder $(cat $HOLD/who): taking over" >&2; rm -rf "$HOLD"; fi
    first=$(ls "$Q" | sort | head -1)
    if [ "$first" = "$(basename "$T")" ] && mkdir "$HOLD" 2>/dev/null; then
      echo "$2 $3" > "$HOLD/who"; now > "$HOLD/beat"; rm -f "$T"; echo "LOCK ACQUIRED"; exit 0
    fi
    sleep 5
  done
  rm -f "$T"; echo "BLOCKED: held by $(cat $HOLD/who 2>/dev/null)"; exit 2 ;;
touch) now > "$HOLD/beat" ;;
release) rm -rf "$HOLD"; echo released ;;
status) [ -d "$HOLD" ] && echo "held by $(cat $HOLD/who), beat $(age)s ago; queue: $(ls $Q | wc -l)" || echo free ;;
*) echo "usage: acquire|touch|release|status"; exit 1 ;;
esac
