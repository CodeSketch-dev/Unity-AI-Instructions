---
name: unity-log-triage
description: Condense Editor.log/Console output into a short deduped list of real problems via a bundled script. Use whenever checking the Console after changes, on failed builds/Play Mode, or with long pasted logs.
---

# Unity log triage

Raw Unity logs are mostly repeats and engine noise. The script prints one row per distinct problem with its count and first `Assets/...:line` location, ordered by what to fix first.

## Use
```
python -I scripts/summarize_unity_log.py                # Editor.log of this machine, only the part since the last compile/reload
python -I scripts/summarize_unity_log.py <file> --top 15 --warnings
python -I scripts/summarize_unity_log.py --all-sessions # look further back than the last reload
cat console.txt | python -I scripts/summarize_unity_log.py -
```
Default log: Windows `%LOCALAPPDATA%\Unity\Editor\Editor.log`, macOS `~/Library/Logs/Unity/Editor.log`. The Editor log belongs to whichever project/instance wrote it last; confirm it is the project you are working on before trusting it.

## Read the result
1. **COMPILE-ERR first**: while any exist, the Editor runs old code; nothing else is meaningful. Fix them (the row gives file and line), refresh once, rerun.
2. **EXCEPTION** rows: the first location is the first `Assets/` frame of the stack, usually where to look. A `NullReferenceException` in `Awake`/`Start` usually means unassigned wiring (see `unity-debugging`).
3. **ERROR** rows: logged errors (missing config files, SDK init failures). Distinguish project bugs from environment noise (a missing optional SDK config).
4. Counts: a row with a large count is a per-frame error; fix it first because it also costs performance.

## Notes
- Use `--warnings` only when hunting warnings; by default they are excluded to save tokens.
- If the Console (not Editor.log) is what you have, read it through the editor tooling filtered to errors, or paste it into the script with `-`.
- The script is heuristic (patterns for `CSxxxx` compile errors, `*Exception`/`*Error:` lines, `[Error]`); if something important is not listed, read the relevant log lines directly with a targeted search around the time of the action.
- Do not paste the raw log into the chat; paste the summary table if you need to show it.
