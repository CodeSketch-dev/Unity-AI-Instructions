---
name: data-persistence-facts
description: Facts about how DataBlock saves and loads (triggers, path, key, failure behavior, serializer). Use when debugging lost saves, save timing, migrations or a data change that did not persist.
triggers: save data, save lost, luu du lieu, mat save
---

# Data persistence facts

Reference facts, mostly VERIFIED from package source (report 01). Confirm against the installed package version before relying on exact numbers.

## When a save happens
- Both versions: on app pause and quit (hooked in the base `Init`). Android `OnApplicationPause(true)` is the reliable point; do not use `OnApplicationFocus` (ad overlays and permission dialogs fire it).
- v2 only: also 2 s after any `DataValue.Value` change (debounced, unscaled time). Collection mutation alone does not trigger it.
- v1 `Save()` writes synchronously on every call (hash dedupe only skips unchanged bytes): never call it in a loop.

## Where and how
- File under `Application.persistentDataPath/<Root>/<full type name>` (full name includes namespace, e.g. `Game.Data_Currency`). v1 root name not read (INFERRED).
- v2: atomic write (tmp -> bak -> final), `.bak` crash recovery, FNV-1a hash skip, background writer thread. Serializer: Odin binary with 4-byte `SKO1` header, legacy BinaryFormatter fallback for old saves. v1: BinaryFormatter unless a define selects MemoryPack or Odin.
- First access of `Instance`/`INSTANCE`: load; if null, `Activator.CreateInstance` (field initializers run); then `Init()` once.

## Failure modes
- Load error or changed field layout -> returns null -> fresh block (silent progress loss). Test migrations with an old save file.
- Namespace or class rename changes the file key: old save is orphaned.
- `DataBlock<T>.Delete()` nulls the instance but other holders keep the stale reference.
- v2 `Save()` skips blocks that were never instantiated.

## Debugging checklist
1. Is `base.Init()` called? 2. Did the change go through `DataValue.Value`? 3. Was the app killed before pause/quit (v1)? 4. Did a rename change the key? 5. Look at the file under persistentDataPath, not the Editor's cached object.
