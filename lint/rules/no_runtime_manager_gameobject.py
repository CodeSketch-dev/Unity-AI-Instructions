from engine import Rule

RULE = Rule(
    id="no-runtime-manager-gameobject",
    pattern=r"\bnew\s+GameObject\s*\(",
    require=r"AddComponent\s*<|DontDestroyOnLoad",
    why="Managers and world pieces are scene-authored prefabs, never built at runtime (new GameObject + AddComponent).",
    skill="no-runtime-manager-gameobject",
)
