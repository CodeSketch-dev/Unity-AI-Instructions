#!/usr/bin/env bash
# Manage the single Graphify watcher for this checkout's Unity project.
# Usage: bash docs/tools/graphify_ctl.sh start|stop|restart|status|update
# One watcher per checkout/worktree (the graph lives in <checkout>/break-and-steal-unity/graphify-out).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ="$(cd "$HERE/../../break-and-steal-unity" && pwd)"
OUT="$PROJ/graphify-out"
PID="$OUT/watcher.pid"
LOG="$OUT/watcher.log"
PY="${GRAPHIFY_PY:-$APPDATA/uv/tools/graphifyy/Scripts/python.exe}"
PYW="${PY%python.exe}pythonw.exe"

alive() { [ -f "$PID" ] && tasklist //FI "PID eq $(cat "$PID")" 2>/dev/null | grep -qi python; }

case "${1:-status}" in
  start)
    if alive; then echo "already running (pid $(cat "$PID"))"; exit 0; fi
    mkdir -p "$OUT"; rm -f "$PID"
    SCRIPT="$(cygpath -w "$HERE/graphify_watch.py")"
    powershell.exe -NoProfile -Command "Start-Process -WindowStyle Hidden -FilePath '$(cygpath -w "$PYW")' -ArgumentList '-I','-u','$SCRIPT','$(cygpath -w "$PROJ")' -RedirectStandardOutput '$(cygpath -w "$LOG")' -RedirectStandardError '$(cygpath -w "$LOG").err'" >/dev/null
    for _ in 1 2 3 4 5 6 7 8; do sleep 1; alive && break; done
    alive && echo "started (pid $(cat "$PID"))" || { echo "failed to start; see $LOG(.err)"; exit 1; } ;;
  stop)
    if alive; then taskkill //PID "$(cat "$PID")" //F >/dev/null && echo "stopped"; else echo "not running"; fi
    rm -f "$PID" ;;
  restart) bash "$0" stop; sleep 1; bash "$0" start ;;
  status)
    if alive; then echo "running (pid $(cat "$PID"))"; tail -n 3 "$LOG" 2>/dev/null; else echo "stopped"; fi
    [ -f "$OUT/graph.json" ] && ls -l "$OUT/graph.json" | awk '{print "graph.json", $5, "bytes", $6, $7, $8}' ;;
  update) (cd "$PROJ" && graphify update .) ;;
  *) echo "usage: $0 start|stop|restart|status|update"; exit 1 ;;
esac
