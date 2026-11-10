# Tool hierarchy (default prior; change it only from measured data)

Order: 1 direct API/SDK/Editor API/test framework -> 2 deterministic CLI, scripts, structured logs, telemetry -> 3 targeted UI Automation (accessibility, scoped) -> 4 screenshot + vision -> 5 hybrid.

| Task | Start with | Fallback | Never |
|---|---|---|---|
| Unity compile errors | compiler output / Editor log parse | Editor API console read | screenshot of the console |
| Unity build | batchmode CLI with log file, or Editor build API | Editor menu via MCP | UI clicking the Build window |
| Unity tests | Unity Test Framework (EditMode/PlayMode) | MCP tests-run | eyeballing Play Mode |
| Gameplay physics | automated tests + runtime telemetry (positions, contacts) | telemetry + vision of key frames | vision-only judgement |
| Game View look (alignment, clipping) | telemetry (rect/bounds numbers) + one screenshot | vision alone when nothing is measurable | skipping the screenshot for visual claims |
| Scene/prefab edits | Editor API / MCP object tools | script via Editor | hand-edited YAML |
| Windows form/dialog | UI Automation scoped to the target branch | skeleton snapshot then scoped; then vision | whole-tree dump, blind coordinate clicks |
| Windows system tasks | PowerShell/Python script with structured output | UI automation | UI for what a CLI does |
| Code search | grep/ripgrep scoped, code index | read file ranges | reading whole repo |

Rules: use structured data when it is sufficient; read only the target branch of an accessibility tree (skeleton first when the app is dense); vision for what only eyes can judge; deterministic assertions for what numbers can prove. Accessibility is not assumed faster or available (Unity in-Editor UI is often not exposed): measure per (category, env) with `adaptive-task-intelligence`, and switch order only on data.
