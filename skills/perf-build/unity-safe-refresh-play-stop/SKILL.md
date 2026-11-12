---
name: unity-safe-refresh-play-stop
description: "Use when any agent refreshes assets, waits for compile, edits prefabs/scenes or runs tests through Unity MCP: always stop Play Mode first, use the project's own MCP, and know the unfocused-editor pause. Prevents stuck MCP tasks."
triggers: refresh asset, stop play mode, mcp stuck, ket task, unity khong compile, assets-refresh, play mode, tat play, compile cho xong
---

# Unity: stop Play Mode before refresh (mandatory)

- BEFORE `assets-refresh`, a compile wait, a prefab/scene edit, a package change or an EditMode test run: stop Play Mode and wait until `IsPlaying == false` (and `IsPlayingOrWillChangePlaymode == false`). A refresh issued during Play blocks and the MCP task gets stuck.
- Never call `assets-refresh` raw. Keep a helper in the project (`tools/qa-mcp/safe_refresh.py`): get state -> stop Play -> wait -> refresh -> wait until `!IsCompiling && !IsUpdating` -> print distinct compile errors (filter MCP's own `[AI]` log noise).
- The session MCP can point at ANOTHER Unity project. Verify once per session with `Application.dataPath`; if wrong, call the right project's MCP over HTTP (`mcpcall.py`, port in `.mcp.json`) and never mutate the wrong one.
- The player loop barely ticks when the Editor window is not focused (frameCount stays 1-2, `Time.time` ~0): positions never move. Play-time checks need the window in the foreground; otherwise step headless (`KinematicCharacterSystem.Simulate` in a script-execute loop, AutoSimulation off) or use EditMode tests, and say which.
- After a package/manifest change the MCP drops for a minute (domain reload + resolve): poll `editor-application-get-state` instead of retrying the call.
- Do not commit or push project work unless the owner asks.
