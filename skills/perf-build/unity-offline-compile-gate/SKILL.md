---
name: unity-offline-compile-gate
description: "Compile gate outside the Editor: check C# builds before asking Unity, and know its limits (asmdef references, UnityEngine.Object ambiguity). Use when Editor is unavailable or before an expensive compile cycle."
triggers: offline compile, dotnet build, csc, asmdef, compile gate, ambiguous reference, compile errors
---

# Offline compile gate
- Necessary but not sufficient: a clean external build is not proof Unity compiles or serialises correctly.
- Known gaps: asmdefs cannot reference Assembly-CSharp-Editor (use reflection); `UnityEngine.Object` vs `System.Object` ambiguity.
- Never run tests on stale assemblies: force compilation, confirm the dll timestamp, clear old results.
- Final proof is always the Editor Console (`unity-log-triage`).
