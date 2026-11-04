# Lean metrics table (copy into the project's lean write-up, fill before and after)

## Scope
Project, commit hash, Unity version, date; commands used (script names and arguments).

## Before / after
| Metric | Before | After | Budget |
|---|---|---|---|
| Assets on disk (MB) | | | |
| First-party (MB) | | | <= 800 |
| Unreferenced first-party (MB, % of bytes) | | | <= 1% |
| Largest first-party asset (MB) | | | <= 20 |
| Text-serialized .asset above 5 MB (count) | | | 0 |
| Duplicate files (same name, size, sha1) count / MB | | | 0 |
| Binary-serialized scenes | | | 0 |
| Scenes above 5 MB | | | 0 |
| Resources folder (MB) | | | singleton assets only |
| Manifest packages (unused) | | | 0 |
| Tracked derived/generated paths | | | 0 |
| Textures above the folder cap (count) | | | 0 |
| SFX decompress-on-load above 200 KB (count) | | | 0 |
| git pack size | | | informational |
| Scripts / prefabs / scenes / materials counts | | | |
| EditMode PASS / SKIP | | | not worse |
| Missing scripts / references (scenes + prefabs) | | | 0 |
| Draw calls / SetPass / batches on the main scenes (Play) | | | not worse |
| Load time of main scenes (Editor Play, not a device) | | | not worse |

## Deleted (one row per batch)
Category | files | MB | proof file | commit | verified by (scenes opened, Console).

## Kept / needs owner decision
Rows from LIKELY-DEAD and UNKNOWN with the reason.

## Not measured
Device RAM, device load time, APK size, Android ASTC overrides, anything else skipped.
