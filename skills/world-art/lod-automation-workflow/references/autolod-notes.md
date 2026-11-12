# AutoLOD notes (idea-only)
Source: third-party example (Unity-Technologies/AutoLOD, Unity Companion License; nothing copied, wording is ours).

Structure observed:
- Editor: import post-processor with per-model and project-wide settings; pluggable async mesh simplifier (default quadric, optional commercial backends); two batchers (simple merge, material-preserving merge); scene-level hierarchical LOD tool; texture atlas helper.
- Runtime: a spatial volume tree that holds renderers and swaps merged low-detail proxies for children by camera distance.

Defaults worth reusing as ideas: halve quality per level, final level at 1% screen height, no LOD for already-light meshes.
Not adopted: the package itself (experimental, unsupported, licence limits).
