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
