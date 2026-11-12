from engine import Rule

RULE = Rule(
    id="no-find-in-update",
    pattern=r"\b(?:FindObjectOfType|FindObjectsOfType|FindFirstObjectByType|FindAnyObjectByType|FindObjectsByType)\s*[<(]|\bGameObject\.Find\s*\(",
    require=r"void\s+(?:Update|FixedUpdate|LateUpdate)\s*\(",
    why="Find* scans the whole scene; in a file with Update/FixedUpdate/LateUpdate it can run every frame and hitches low-end Android.",
    skill="no-find-in-update",
)
