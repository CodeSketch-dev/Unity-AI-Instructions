#!/usr/bin/env bash
# Show the real state of delegated tasks: Tools/codex/codex_status.sh [name]
D="$(cd "$(dirname "$0")/../.." && pwd)/Temp/codex"
for f in "$D"/${1:-*}.status; do [ -f "$f" ] && echo "$(basename "$f" .status): $(cat "$f")"; done
