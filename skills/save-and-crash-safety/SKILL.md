---
name: save-and-crash-safety
description: "Save safety and crash basics: backup file rotation, checksum header, version migration chain, recovery events, safe-boot flag, crash reporting. Use when touching persistence or release readiness."
---

# Save and crash safety

Facts about the framework data layer come from `data-persistence-facts`; verify the installed version before assuming behavior.

- A failed load must not silently become a fresh save: keep `.bak` (and a daily second backup), wrap the payload with a version and checksum, and on failure try the backups, then a new save, logging `save_recovered` or `save_reset` and showing one non-blocking toast.
- Migrations: version int plus a migration chain run at load, not editor-time hooks.
- Never store important state in PlayerPrefs.
- Save on `OnApplicationPause(true)`; no blocking save on the main thread beyond what the framework does.
- Safe boot: set a flag before init and clear it after the first frame; two failed boots in a row skip optional systems.
- Crash tool in release builds (Crashlytics or Unity diagnostics) with a few custom keys; rate-limit duplicate exceptions.
- Tests: kill during write, truncated file, zero-byte file, wrong version (`playmode-script-testing`). Editor menu to corrupt and restore a save helps QA.

## Added from awesome-gamedev-agent-skills (2026-11-02)
Source: third-party example. Inspired by: gamedev-skills/awesome-gamedev-agent-skills skills/disciplines/save-systems.
- Save data and rebuild objects on load; never serialize scene object references or paths (renames break old saves).
- Stamp a version from v1 and keep migrations in an ordered chain; write temp then rename, keep a .bak.
- Treat the file as untrusted: validate, clamp, fall back to backup. Keep saves plain data (no object instantiation on load).
- Autosave on safe boundaries to its own slot; never mid-action. Use locale-invariant number serialization.
