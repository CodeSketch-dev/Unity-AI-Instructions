#!/usr/bin/env bash
# Single-writer Editor lock: FIFO tickets + atomic mkdir lock + heartbeat.
#   editor_lock.sh acquire <agent> [max-wait-sec]   blocks until the Editor is yours (default 3600)
#   editor_lock.sh touch|release <agent>            touch at least every 2 min while holding; always release
#   editor_lock.sh status
# Env: LOCK=<dir> (default Temp/agent-lock/lock.d)  Q=<dir> (default Temp/agent-lock/queue)
# Held lock with no heartbeat for 5 min is stale (taken over); a waiter that stops polling for 2 min leaves the queue.
LOCK="${LOCK:-Temp/agent-lock/lock.d}"; Q="${Q:-Temp/agent-lock/queue}"; STALE=300; QSTALE=120
cmd=$1; who=${2:-unknown}
now() { date +%s; }
mt() { stat -c %Y "$1" 2>/dev/null || echo 0; }
age() { [ -f "$LOCK/beat" ] && echo $(( $(now) - $(cat "$LOCK/beat") )) || echo 999999; }
names() { ls "$Q" 2>/dev/null | sort | sed 's/^[0-9]*-//' | tr '\n' ' '; }
mkdir -p "$Q" "$(dirname "$LOCK")"
case "$cmd" in
  acquire)
    max=${3:-3600}; start=$(now); ticket="$Q/$(date +%s%N)-$who"; : > "$ticket"
    trap 'rm -f "$ticket"' EXIT
    while true; do
      touch "$ticket"
      for t in "$Q"/*; do [ -e "$t" ] && [ $(( $(now) - $(mt "$t") )) -gt $QSTALE ] && rm -f "$t"; done
      first=$(ls "$Q" 2>/dev/null | sort | head -1)
      if [ "$first" = "$(basename "$ticket")" ]; then
        if [ -d "$LOCK" ] && [ "$(age)" -gt "$STALE" ]; then echo "stale lock of $(cat "$LOCK/owner" 2>/dev/null) taken over by $who"; rm -rf "$LOCK"; fi
        if mkdir "$LOCK" 2>/dev/null; then echo "$who" > "$LOCK/owner"; now > "$LOCK/beat"; rm -f "$ticket"; trap - EXIT; echo "ACQUIRED by $who"; exit 0; fi
      fi
      if [ $(( $(now) - start )) -gt "$max" ]; then echo "TIMEOUT (holder $(cat "$LOCK/owner" 2>/dev/null), queue $(names))"; exit 1; fi
      echo "waiting: held by $(cat "$LOCK/owner" 2>/dev/null) (beat $(age)s ago), queue: $(names)"; sleep 10
    done ;;
  touch) [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$who" ] && now > "$LOCK/beat" && echo ok || { echo "you do not hold the lock"; exit 1; } ;;
  release) [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$who" ] && rm -rf "$LOCK" && echo RELEASED || echo "not held by $who" ;;
  status) [ -d "$LOCK" ] && echo "HELD by $(cat "$LOCK/owner") beat $(age)s ago; queue: $(names)" || echo "FREE; queue: $(names)" ;;
  *) echo "usage: acquire|touch|release|status"; exit 2 ;;
esac
