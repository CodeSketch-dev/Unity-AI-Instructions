#!/usr/bin/env bash
# Delegate a CODE-ONLY task to an external agent CLI (default Codex). Manager protocol (agent-agnostic):
#   1. start THIS script itself with the Bash tool's run_in_background (never wrap it in `( ... &)`: the launcher would exit at once and
#      the harness would report a fake "completed"). The harness notification then fires when the agent REALLY ends.
#   2. status file Temp/codex/<name>.status: RUNNING <pid> <start>  ->  DONE exit=<n> <end> files=<count changed>.  Read it, never guess.
#   3. result: Temp/codex/<name>.out.txt (last agent message), log Temp/codex/<name>.log.txt.
#   4. manager then: git status/diff, compile, run tests, review, commit.
#   Tools/codex/run_codex_task.sh <brief.md> [model] [agent]   (agent: codex (default) | any CLI reading the brief on stdin, set AGENT_CMD)
set -uo pipefail
BRIEF="${1:?brief file}"
MODEL="${2:-gpt-5.6-luna}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
NAME="$(basename "$BRIEF" .md)"
D="$ROOT/Temp/codex"; mkdir -p "$D"
OUT="$D/$NAME.out.txt"; LOG="$D/$NAME.log.txt"; ST="$D/$NAME.status"
rm -f "$OUT"
BEFORE="$(cd "$ROOT" && git status --porcelain 2>/dev/null | wc -l)"
echo "RUNNING pid=$$ start=$(date +%FT%T) model=$MODEL" > "$ST"
if [ -n "${AGENT_CMD:-}" ]; then
  # other agents (kimi etc.): AGENT_CMD reads the brief on stdin and prints its final message on stdout
  cat "$BRIEF" | bash -c "$AGENT_CMD" > "$OUT" 2> "$LOG"; RC=$?
else
  cat "$BRIEF" | codex exec --skip-git-repo-check -C "$ROOT" --dangerously-bypass-approvals-and-sandbox -m "$MODEL" \
    --disable hooks --disable codex_hooks -o "$OUT" - > "$LOG" 2>&1; RC=$?
fi
AFTER="$(cd "$ROOT" && git status --porcelain 2>/dev/null | wc -l)"
[ -s "$OUT" ] && HASOUT=yes || HASOUT=NO_FINAL_MESSAGE
[ "$HASOUT" = "NO_FINAL_MESSAGE" ] && grep -q "usage limit" "$LOG" 2>/dev/null && HASOUT="USAGE_LIMIT($(grep -o "try again at [0-9:]* [AP]M" "$LOG" | tail -1))"
echo "DONE exit=$RC end=$(date +%FT%T) final=$HASOUT dirty_delta=$((AFTER-BEFORE))" > "$ST"
echo "done: $ST"
