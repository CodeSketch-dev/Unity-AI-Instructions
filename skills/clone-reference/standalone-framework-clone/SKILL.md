---
name: standalone-framework-clone
description: "Use when a game must stop depending on a shared git framework package (e.g. before merging into another engine): clone only the used APIs into the game's Scripts/Core with GUIDs preserved, then remove the package."
triggers: clone framework, standalone, doc lap, remove package, sketchengine, merge engine, gui, guid, vendoring
---

# Make a game standalone from a framework package

1. Grep what the game really uses (namespaces + type names) before copying anything; list it in a report.
2. Clone only those types into `Assets/_Game/Scripts/Core/Framework/<Area>/`, one type per file, game namespace, trimmed and optimized (no per-call allocs/LINQ/reflection).
3. Components that live inside prefabs/scenes MUST keep their script GUID: copy the original `.cs.meta` next to the clone (same file name) and keep serialized field names. Check by scanning all package script GUIDs against `*.prefab/*.unity/*.asset`.
4. `[RuntimeInitializeOnLoadMethod]` cannot sit in a generic class: use a non-generic registry (clears registered statics) instead.
5. Keep ScriptableObject singleton resource paths/names unchanged so existing assets still load.
6. Only then remove the package from `manifest.json` AND `packages-lock.json`, refresh with Play stopped, expect the MCP to drop for a minute.
7. Settings/Data features used once may be replaced by PlayerPrefs; tell the owner saved values are lost.
8. VERIFY, never trust a report: after the refresh, count Missing scripts in every prefab/scene (`GameObjectUtility.GetMonoBehavioursWithMissingScriptCount`) and read each cloned `.meta` guid against the GUID the prefabs reference. A subagent claimed GUIDs were preserved while Unity had regenerated them (4 touch detectors + 4 press tweens missing, serialized refs null, NullReference at start). Fix: put the original guid back in the clone `.meta`, refresh, re-save prefabs whose refs were lost, re-instance scene copies.
