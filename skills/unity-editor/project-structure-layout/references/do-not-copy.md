# What NOT to copy from the reference (it is not tidy everywhere)

The reference project is the model for architecture, not for housekeeping. A refactor target is the leaner version:

| Reference trait | Do instead |
|---|---|
| Two art roots (`_Art`, `_ARTs`), `Material`/`Materials`, `__Resource` next to `Resources` | one root per concern, fixed spelling |
| Test and scratch scenes in the repo (`test`, `New Scene`), stray screenshot in `Assets/` | keep only Build Settings scenes; ignore the screenshot output folder |
| Stale baked world copies next to their sources | one source + one bake step; if a baked scene must exist keep it text-serialized and paired |
| Two tween libraries (DOTween and PrimeTween) | PrimeTween only; migrate the rest in a staged batch |
| Two navigation stacks | one |
| 26 runtime files with `using UnityEditor` | `#if UNITY_EDITOR` guards or move to Editor folders |
| Zero tests | EditMode + PlayMode asmdefs and a regression gate |
| 2000-line classes | split below ~400 lines along responsibilities |
| Vietnamese comments in code | English only |
| `catch { }` in a central Update | log or handle; never swallow |
| `[InitializeOnLoadMethod]` tool that re-edits a prefab on every reload | one-shot migration tools are deleted after use |
| Imported sub-projects and vendor demo content kept in the repo | vendor stays outside `_Game`, trimmed to the used closure |
| 4k VFX pack files for a handful of effects | closure scan, keep what is referenced |
| `.gitignore` globs that can hide first-party folders (`Demo*`, `Example*`, `Tutorial*`) | negate explicitly, audit with `git check-ignore -v` |
| Mixed button node names (`Btn_X`, `BtnX`, `Button_X`) | `Btn_<Name>` |
| Large namespaces for imported modules next to `Game` | `Game` only for first-party |
| A 22 MB prefab / 12 MB scene | prefab > 2 MB and scene > 5 MB are findings |

Keep from the reference: feature-first folders, one namespace, suffix grammar, factory/data/event separation, persistent root prefab, scene-authored prefabs, runtime device policy over a single Quality level, pooled runtime spawns, registry-based collision.
