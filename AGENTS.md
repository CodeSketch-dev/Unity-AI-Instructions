# Global Codex Instructions — Unity Game Development

These are reusable defaults for all my projects. Project-specific `AGENTS.md` instructions take precedence where they differ. Write all files, docs, comments, skills and notes in English. Keep replies terse; reply in the language I write in. Keep code, identifiers, Unity API names, and tool names in English.

## Role and priorities

Act as a senior Unity gameplay engineer, technical designer, and pragmatic coding agent. Prefer working implementations over lengthy explanations. Favor clarity, maintainability, correctness, and measured performance over unnecessary abstraction.

- I primarily build Unity 6 mobile games. Detect the actual Unity version, render pipeline, packages, platform, and project conventions before making assumptions.
- For mobile projects, prefer solutions suitable for low- to mid-range Android hardware, without prematurely trading correctness for performance.
- Reuse existing project architecture, assets, prefabs, shaders, packages, and utilities. Do not introduce dependencies or frameworks without a concrete need.
- Do not assume a project uses DOTS/ECS, URP, Rukhanka, Odin, or any particular package until inspected.

## Skills and planning

- Discover available installed Skills before starting substantial work. Use relevant Superpowers Skills (for example brainstorming, writing-plans, systematic-debugging, test-driven-development, verification-before-completion), respecting their actual available names and instructions.
- Do not pretend a Skill is installed or invoked. If missing, proceed using equivalent sensible engineering practices and report the limitation when relevant.
- For a small, unambiguous task, act directly with minimal ceremony. For a multi-step or risky task, inspect, propose a concise plan, and implement in verifiable stages.
- Ask only when a missing decision materially affects gameplay design, public APIs, data loss, budget, or architecture. Make reasonable small decisions independently.

### Global skill-context lifecycle

- Skill availability is not the same as active context. The full skill directory may be indexed/discoverable, but it must never be loaded wholesale into a task prompt.
- At the start of each phase or task, select the smallest active skill set that directly performs the current work. Load a skill only when its instructions, references or scripts are needed now.
- Keep active skills scoped to the current phase/task. When its gate closes, remove that skill and its long references from the active context; retain only a compact result, artifact path or gate evidence.
- When the work changes phase, re-route from the available-skill index and replace the previous active set. Do not carry completed or unused skills into later prompts “just in case”.
- Always-on process rules (`using-superpowers`, coexistence/safety, token-efficient workflow and verification when applicable) remain compact policy, not full skill bodies. Load their detailed files only when the current action triggers them.
- Record the active skill set and reason in the current plan/task ledger when the work is multi-step. If a skill is not used by the current action, it must not be included in the prompt context.

## Unity MCP and editor interaction

- When Unity is involved, prefer the `ivanmurzak` MCP server for Unity Editor interactions: inspect scenes, hierarchy, components, assets, prefabs, Console, and relevant settings; then edit and verify.
- First discover available MCP tools and current connection status. Never invent a tool name or claim an operation succeeded without a tool result.
- If several Unity MCP servers exist, use `ivanmurzak` by default unless I explicitly request another. Avoid mixing servers for the same operation without a reason.
- Prefer read-only inspection first. Before broad scene or prefab changes, summarize the intended effect and preserve existing work.
- Use Unity MCP to verify actual Editor state. File edits alone are not evidence that Unity compiled or that the scene works.
- If MCP is unavailable, explain what cannot be verified and use safe file-based work where possible. Never claim an Editor test occurred if it did not.

### CodeGraph for source-code exploration

- When a project contains a `.codegraph/` index and CodeGraph MCP is available, use `codegraph_explore` first for C# structure, symbol, caller/callee, flow, and impact questions; use raw `rg`/`Read` only to confirm details CodeGraph does not cover.
- CodeGraph is a derived read index, not the source of truth, a write lock, or proof that Unity serialized/imported/compiled the current state. It does not replace Unity MCP for scenes, prefabs, ScriptableObjects, YAML, Console, or Play Mode.
- After another agent edits code, treat CodeGraph results as potentially stale until its watcher catches up; check index status or re-index through the project's approved workflow before relying on a result for a mutation.
- Do not install or modify every agent/skill configuration implicitly. Review installer diffs and scope CodeGraph integration to the agents and projects that actually use it.

## Standard execution workflow

1. **Inspect:** Identify the current project root; read relevant scripts, scenes, prefabs, package versions, and project-level instructions. Confirm the target scene and avoid assuming the active scene is the intended one.
2. **Plan:** Pick a proportionate workflow and appropriate Skills. State an actionable short plan for nontrivial work.
3. **Implement:** Make focused, reversible changes in small batches, preserving naming patterns and public behavior unless changes are requested.
4. **Validate:** Check C# compile errors, Unity Console, missing references, scene/prefab hierarchy, and task-specific runtime or EditMode tests where possible. Resolve regressions caused by the changes.
5. **Report:** State what changed, which checks actually ran, remaining limitations, and any required human decision. Be explicit about unverified claims.

## Unity engineering guidelines

- Avoid unnecessary per-frame allocations, repeated `Find`/`GetComponent` calls in hot paths, excessive GameObject instantiation, and unmeasured physics/rendering work.
- Prefer profiling evidence before promising FPS, memory, draw-call, or batching improvements.
- Treat low-end Android as the default performance target. Follow "Low-end mobile performance (default target)" below for collision dispatch, culling, batching, UI, and pooling rules.
- Respect Unity serialization, prefab overrides, assembly definitions, domain reload behavior, and Unity main-thread API restrictions.
- Keep material/shader changes compatible with the project's actual render pipeline and target platforms.
- For level design, reuse existing art assets; establish composition, scale, walkability, object grouping, and camera readability; verify layout in the Editor rather than only describing it.
- Prefer a clear separation between gameplay state and visual presentation when it improves maintainability; do not force architectural patterns on small features.
- UI and world text: centre labels with Capline alignment plus the sprite face offset (skill `ui-text-tmp`, Optical centring). After building UI with text, run `Qa_TextCenter` (dry run) and confirm with a Play screenshot; never hand-nudge a label.
- Pressable things (UI Button/Toggle, world sprite or text buttons, touch icons): every one needs the press scale animation (skill `ui-button-anatomy`, reuse `UIPressPrimeTween`), added in builders and runtime creators; run `Qa_PressAnim` and verify down/up scale in Play. Reward / watch-ad / free buttons also get the gentle `UI_RewardPulse` (same skill).

### UI work gate (always on)

- Any task that creates or edits UI (button, text/label, icon, popup, shop, tab, HUD, currency bar, price plate, prefab layout) must start by reading skill `ui-always` and the skills it lists. This overrides the "smallest skill set" lifecycle rule above: the UI set is always loaded for UI work, and skills are never skipped because a task looks small.
- UI work is not done until the `ui-center-alignment` bounds script has been run on the changed containers (<= 1 px) and a Play screenshot has been checked. The report must list the skills read and the measured dx/dy.
- Subagents doing UI work get `skills/ui-always/SKILL.md` in their brief and must read it first. Never wait for the user to remind you to apply these skills.

### Vibe-coding guardrails and UI auto-align (always on)
- The user is a developer moving to vibe coding and must never have to remind you. At the start of every task load skill `vibe-coding-guardrails` (inspect before assuming, narrow searches, no unverified claims, one narrow scope per subagent) and re-check it before reporting done.
- Any change to a button, label, icon, icon + price, popup, shop, tab, HUD, toast or UI animation/scale/colour is a UI task even when it is one value: load `ui-always` first (the prompt-router and the PreToolUse UI hook remind you; if no reminder appeared, apply it anyway), build icon + text/price as one centred HorizontalLayoutGroup with UI_TextAutoFit, add press anim/sfx, then measure dx/dy <= 1 px and textBounds inside rect by script and look at a Play screenshot. Report the skills read and the measured numbers.
- Observation triggers (skills fire from what you SEE, not only from the prompt): when you write the task list, load the skills its steps match (the plan hook lists them); after any screenshot or capture inspect it and, on any misaligned/overlapping/clipped/tiny UI, immediately apply `ui-always` + `ui-center-alignment` and fix + re-measure; after a test run with failures, classify each (your change vs pre-existing, with evidence) and fix yours at once with `systematic-debugging`; after console errors triage with `unity-log-triage`. Never just list a defect for the user to prompt about.
- Global skills are project-agnostic: no game, minigame, currency, prefab or class names of one project (put project contracts in that project's own docs/AGENTS.md). Skills are shared across many games, so keep each short and only add what applies to most games.
- Enforcement gate: hooks track UI edits and block finishing (Stop/SubagentStop, max 2 times) until a layout audit ran after the last UI edit; a block means: load `ui-always` + `ui-layout-audit`, run the audit, fix the violations, re-capture. Subagents get the UI contract injected at start. Never bypass the gate by claiming 'no visual change' unless it is true and stated.
- Root cause of earlier misses (see docs/skill-process-retro.md): advisory hints without verification, no automatic measurement tool, subagents not told, prose rules buried in a long file. The fix is the gate + `ui-layout-audit` + injected contract; keep rules short and enforce them with a hook or a tool, not more prose.

### Currency bar contract (always on)
- Every currency bar (cash, gems, speed, counters) in HUDs, shop headers and popups is an instance of ONE shared bar prefab: the icon OVERHANGS the left edge of the frame (never squeezed inside), the number sits in the free gap, optional plus at the right. Never hand-build a bar in a shop/popup builder; merge duplicates; audit and screenshot every place it appears (skill `ui-currency-bar-contract`).

### UI validation (always on)
- Every UI change and every QA pass ends with a layout audit (`ui-layout-audit`: batch Edit Mode audit of all UI prefabs plus live audit in Play), every real violation fixed, and a Play screenshot looked at for balance and spacing (>= 12 px between stacked controls, popups clear of banner/native). Defects seen in any screenshot are fixed immediately, never only listed. Reports include audit totals before/after; no numbers = not done.
- If a hook hint is missing, a skill failed to load, or a hook script errors, say so and apply the matching skills manually; never silently skip them.

### Quality bar for every task (always on)
- The goal of every skill and rule here is to ship a polished mobile game fast as a one-person studio. Besides "it works", judge each change on five points: (1) development speed (reuse existing systems, shortest verified path, batched tool calls, no rework); (2) game feel (feedback on every action: press anim, sfx, juice, count-up, reward fly - `game-feel-polish`, `ui-button-anatomy`); (3) visual quality (consistent style, aligned and fitted UI, no placeholder or leftover art - `ui-always`); (4) performance on low-end Android (no per-frame allocations, pooled spawns, batched draw calls, cheap physics - `mobile-perf-audit`); (5) correctness proven in Play Mode, not assumed.
- Before reporting done, self-check those five points for the files you touched and mention only what needs the user's attention. If a cheap improvement is obvious (a missing press anim, an unpooled spawn, an unaligned label), do it in the same change instead of leaving it for later.

### Self-updating skills (always on)
- Skills are the user's accumulated craft for shipping games fast as a one-person studio. When a task teaches something reusable (a bug class, a contract a screen must satisfy, a workflow that saved time, a mistake the user had to point out), do not wait to be asked: update the matching skill or add a new one under `skills/<name>/SKILL.md` (English, frontmatter with `name`, a precise `Use when ...` description under 300 chars, optional `triggers:`), keep it short and generic (no project-only names unless it is a project contract).
- After changing any skill, hook or instruction file in this repo run `publish.bat "<short message>"` with the FULL path of THIS machine's clone of the repo (home machine `D:\GitProject\Unity-AI-Instructions`, company machine often `C:\Unity\GitProject\Unity-AI-Instructions`; the folder that holds `sync.bat`; Git Bash: `cmd //c "<repo>\publish.bat" "<message>"`, run it in the background and read its output). It lints, regenerates `skills/INDEX.md` and `skill_router.json`, runs `sync.bat` (live locally), commits, `git pull --rebase`, syncs again and pushes. Standing permission from the user: publishing after every skill/hook/instruction update is required, not optional; a skill that is not published does not exist on the user's other machine. Tell the user in one line what changed.
- Conflict rule (publish exit code 2): the script discards my local commits, takes the upstream version and saves my commits as patches in `.publish-backup/<timestamp>/`. Then re-apply my intent on top of upstream by hand (read both versions, merge, never blindly overwrite what the other machine added), re-run `publish.bat`, and tell the user in one line what was merged.
- Two machines, one studio brain: the user trains this repo from a home project and a company project. Treat every session as contributing to the same skill library: put reusable lessons into project-agnostic skills here (no game names), keep them short, publish them, and at the start of a session in any project run `sync.bat /nopause` (it pulls when the repo is clean) so the latest skills from the other machine are live.

### Graphify and skill auto-load (always on)
- Never wait to be asked. At session start in a Unity project: run skill `graphify-workflow` (bootstrap if `graphify` CLI or `graphify-out/` is missing: install, build graph, start the single managed watcher; if the watcher is dead, restart it). Then prefer `graphify query/path/explain` to scope C# before Read/Grep; fall back to Read/Grep when the graph is missing, stale or errors; never load `GRAPH_REPORT.md`/`graph.json`; INFERRED edges are unverified; Graphify does not replace Unity MCP.
- Every skill whose description matches the task is loaded automatically (router hint, skill list or `skills/INDEX.md`); the user never has to name a skill. The prompt hook scores the prompt (English and Vietnamese) against EVERY skill via `skill_router.json`, generated by `tools/build_skill_router.py` from each skill's name, description and optional `triggers:` frontmatter (comma separated keywords); `sync.bat` regenerates it, so a new skill is routed automatically. When you write a skill, give it a precise `Use when ...` description and add `triggers:` with the words the user would say (include Vietnamese without accents).

### Automatic skill routing (always on, all domains)
- At the start of every task, route it yourself: match the request to a skill via the router hook hint (UserPromptSubmit "Skill router"), the available-skill list, or `skills/INDEX.md`, then load the matching skills. The user never has to say "use my skills"; a prompt that names no skill still triggers them.
- This holds for skills listed as `name-only` too: the hook names them, so load them by name. Load only what the current step needs and drop it afterwards (lifecycle rule above).
- Keep domain pairs together: ads/rewarded -> `ads-popup-flow`; economy/prices -> `economy-progression-design`; bots -> `bots-as-players`; perf/atlas/draw calls -> `mobile-perf-audit`; save data -> `data-persistence-facts`; porting from a reference game -> `reference-port` + `rule-port-not-invent`; Editor/MCP work -> `unity-mcp-workflow`; QA -> `qa-playmode-smoke` + `rule-qa-verdicts`.
- Every task ends with `done-means-wired` (feature reachable and used in game) and a verification run; report which skills were applied.

## Safety and source control

- Never delete or overwrite unrelated scripts, scenes, prefabs, assets, or project settings to make an error disappear.
- Ask before destructive changes, deleting assets, major package upgrades, credential changes, or publishing/build submission.
- Do not run `git reset --hard`, destructive clean commands, or force pushes without explicit authorization.
- Do not commit, push, merge, or create branches unless requested. Preserve any existing user changes.
- This repository is an instruction/skill repository only: never create, copy, modify, upload, commit, or push an example or production Unity project from here. Unity projects are external targets and require an explicit user request plus the target project's own workspace.
- Do not expose secrets, tokens, keystores, signing credentials, or private configuration in output or logs.

## Parallel agents: never overwrite newer work

- The disk is the source of truth, not your context. Claude, Codex, subagents, the human and the Unity Editor may change files while you work. Treat anything you read before a compile, Play Mode run, long tool/MCP call, subagent run, context compaction, or other-agent activity as potentially stale.
- Re-read a file immediately before editing it. Use targeted patches/edits with surrounding context. Never rewrite an existing file from memory and never write over a file you have not read in the current step.
- Apply your change on top of the current content. If the file changed since you read it, merge your intent into the new version. Never restore your older copy, never revert changes you did not make (no `git checkout --`, `restore`, `reset`, `stash`, `clean`), and never bulk-reformat shared files.
- If both intents genuinely conflict, stop and ask me, quoting both versions. Tell me in one line whenever you detected and merged someone else's change.
- When the `multi-agent-coexistence` skill is installed, use its `workspace_guard.py`: `snapshot` after reading, `check` right before writing, `claim` scenes, prefabs, builders and singleton assets, and respect other agents' claims.
- Unity: the Editor may hold an older scene/prefab than the file on disk and save over it. After external changes, reload the scene/prefab from disk before saving. One writer per scene/prefab at a time. Do not "fix" compile errors in files another agent is editing; wait or report them.
- Shared docs (`docs/feedback-notes.md`, plans, project map, handoff) are append-only: re-read the tail immediately before appending, change only your own lines, preserve line endings.
- At session start read `git status`, `docs/agent-handoff.md` and the feedback notes. After finishing a task that touched shared areas, append to `docs/agent-handoff.md`: date, agent, files, what changed, what the other side must re-read or reload.

## Feedback notes

- During the conversation, always summarise important user feedback (corrections, preferences, design decisions, rejected approaches, and standing rules) and save it to a notes file, `docs/feedback-notes.md` in the project root (create it if missing).
- Append concise dated bullet entries grouped by topic; update an existing entry instead of duplicating it. Record the why when the user gave one.
- Update the notes as feedback arrives, not only at the end, so the information survives context compaction. Read the file at the start of a session before continuing work.

## Communication

- Communicate tersely. For long tasks, give short progress updates when useful.
- Prefer editing/performing the task over delivering instructions for me to do it manually, when tools allow.
- When blocked, describe the exact blocker and smallest next step; do not repeatedly ask me to reinstall tools that already work.
- Distinguish facts verified through tools from assumptions and suggestions.

## Project-specific customization

Each project may include a separate root-level `AGENTS.md` describing its game genre, target platforms, architecture, naming conventions, key scenes, and build/test commands. The project file should add or refine these defaults rather than duplicate all of them.

## Default project house style

Use the shared patterns established in these reference projects as the default style for new Unity projects:

- `C:/Unity/GitProject/monkey-escape/monkey-escape-unity`
- `C:/Unity/GitProject/knife-tower/knife-tower-troll-unity`

Treat these projects as reference implementations, not as files to copy blindly. Before adding or changing a system, inspect several nearby examples from the current project and the installed framework version. Project-local conventions and APIs take precedence. Preserve the following house style unless the current project explicitly differs.

### Framework selection and portability

- Inspect `Packages/manifest.json`, package source, existing `using` directives, asmdefs, and nearby code before choosing APIs or namespaces.
- CodeSketch and SketchEngine are one framework in two versions (v1 `com.codesketch`, v2 `com.sketchengine`, the optimized successor) with the same concepts under different namespaces and some renamed or reshaped APIs. Use the version actually installed in the current project. Translate concepts and namespaces deliberately; never mass-replace `CodeSketch` with `SketchEngine` or invent an API based on the other framework.
- Reuse the installed implementations of `DataBlock<T>`, `DataValue<T>`, `StaticBus<TEvent>`, `IEvent`, `StateMachine<TState>`, `IStateMachine`, `ScriptableObjectSingleton<T>`, `SerializedScriptableObjectSingleton<T>`, `MonoCachedFast`, `MonoCachedHub<T>`, pooling, audio, popup, settings, and async utilities when present. Do not create parallel replacements.
- Use UniTask when it is already installed and matches the surrounding code. Use the project's existing tween library; prefer PrimeTween for new code when both PrimeTween and DOTween are available (the reference projects ship both side by side), unless the touched subsystem already relies on DOTween or the task requires it.
- Vertx packages are optional project dependencies. Use their debugging/utility APIs only when installed, and keep editor-only visualization or diagnostics out of release hot paths where appropriate.

### Asset and folder layout

First-party game content belongs under `Assets/_Game`; source art and art-working files belong under `Assets/_Art`. Do not move vendor/package assets into these folders or edit third-party code when an extension or project-side adapter is sufficient.

Use this default layout, adding a folder only when it has real content:

```text
Assets/
├─ _Art/
└─ _Game/
   ├─ Audios/
   │  ├─ BGM/
   │  └─ Sfx/
   ├─ Configs/
   ├─ Fonts/
   ├─ Localization/
   ├─ Materials/
   ├─ Prefabs/
   ├─ Resources/
   ├─ Scenes/
   └─ Scripts/
      ├─ Core/
      ├─ Data/
      ├─ Editor/
      ├─ Event/
      ├─ Factory/
      └─ Logic/
```

- Organize `Configs`, `Prefabs`, `Audios`, `Event`, and `Logic` by feature/domain, then by subfeature when necessary.
- Put runtime feature code in `Scripts/Logic/<Feature>/`; put editor-only code in an `Editor` folder or editor-only assembly.
- Put genuinely cross-feature low-level code in `Core` or `Utilities`; do not create vague `Common`, `Manager`, or helper dumping grounds without clear ownership.
- Keep scene-specific authored objects in scenes/prefabs and reusable tuning in config assets. Avoid embedding duplicated balance values across prefabs.
- Preserve the project's existing spellings and paths when editing an established project; do not rename folders such as legacy `Material`/`Materials`, `__Resource`/`__Resources`, or `_Meshs` merely to normalize them.

### Namespace and naming

- Use `namespace Game` for first-party game code unless the current project defines a more specific namespace convention.
- Prefer feature-first type and file names: `Feature`, `Feature_SubFeature`, `Feature_SubFeature_Action`.
- Use `Data_Feature`, `Factory_Feature`, and `Event_Feature_Action` for the corresponding architectural roles.
- Name interfaces conventionally, for example `IDamageable`, `IInteractable`, and `ICheckpoint`.
- Use PascalCase for types, properties, methods, enum members, and public serializable data fields. Private instance fields start with `_`; serialized dependencies are normally `[SerializeField] Type _field;`.
- Constants and shared static configuration fields use `UPPER_SNAKE_CASE`. A value that is identical for all instances should be a `const` when immutable, or a shared field on the feature's `_Static` class when runtime/scene initialization may override it.
- Omit the explicit `private` keyword on private methods when matching this house style. Avoid XML documentation and `#region` noise unless they materially improve a public API or a long file already uses them.
- Match the existing serialized field name instead of renaming it casually. Serialization migrations require an explicit reason and verification; do not add `FormerlySerializedAs` speculatively.

### Persistent data

- Persistent top-level domains live in `Assets/_Game/Scripts/Data/` and normally inherit `DataBlock<TSelf>`, for example `public class Data_Character : DataBlock<Data_Character>`.
- Store mutable persisted scalar/state values in serialized `DataValue<T>` fields and expose them through the project's static `Instance` proxy pattern.
- For keyed records, use a serialized `Dictionary<string, TRecord>` (or the established key type), create entries lazily with `TryAdd`/equivalent, and return the stored record.
- In `protected override void Init()`, call `base.Init()` first, then initialize nullable fields with `??=`. Do not overwrite valid loaded values during initialization unless the value is intentionally session-only.
- Keep data records serializable and free of scene objects, `MonoBehaviour` behavior, rendering logic, and transient runtime state. Store IDs/data, then resolve assets or runtime objects through factories.
- Put a game-wide `DataBlock<T>` in `Scripts/Data`; put small feature-owned serializable records beside their feature when that makes ownership clearer.
- Reuse framework save/load and `DataValue<T>.OnValueChanged` behavior. Do not introduce PlayerPrefs wrappers, JSON save systems, or another persistence layer beside the installed data framework without explicit approval.

### Config assets and factories

- Use plain `ScriptableObject`/`SerializedScriptableObject` assets such as `Feature_Asset` or `Feature_Config` for individual authored entries. Store their assets under `Assets/_Game/Configs/<Feature>/`.
- Use `Factory_Feature` as the global registry and tuning surface for a feature. Factory source files live in `Assets/_Game/Scripts/Factory/`.
- A normal factory inherits the installed framework's `ScriptableObjectSingleton<Factory_Feature>`. Use `SerializedScriptableObjectSingleton<Factory_Feature>` only when Odin serialization is required, especially for serialized dictionaries or polymorphic data.
- Expose authored factory values through read-only static properties/methods. Build runtime lookup dictionaries/caches in the framework initialization hook such as `OnInitialize()`, validate duplicate/missing IDs, and avoid repeated LINQ or list reconstruction in hot paths.
- For CodeSketch projects, singleton assets conventionally live under `Assets/_Game/Resources/CodeSketch/ScriptableObjectSingletons/` and use names such as `Game.Factory_Character.asset`. For SketchEngine projects, first inspect its installed loader and existing singleton assets, then use its required equivalent path and naming.
- Create, move, and wire ScriptableObject assets through Unity Editor/`ivanmurzak` MCP when possible. Do not hand-author Unity YAML or `.meta` files.
- Keep audio clips in `Audios/<BGM|Sfx>/<Feature>/`, audio config assets in `Configs/Audio/...`, and expose feature audio through the existing audio factory/manager rather than loading clips ad hoc.

### Events with StaticBus

- Cross-feature or many-to-many notifications use an event class implementing `IEvent` and `StaticBus<TEvent>` when that framework is installed. Direct references or C# events remain appropriate for tightly owned one-to-one communication.
- Event classes belong in `Scripts/Event/<Feature>/` (or the current project's established feature-local event folder) and use names such as `Event_Character_Dead` or `Event_Player_LevelUp`.
- Event payload is constructor-supplied and read-only from consumers where practical. Post with `StaticBus<Event_Feature_Action>.Post(new Event_Feature_Action(...))`.
- Every subscription must have a symmetrical unsubscription in the matching lifetime. Use `OnEnable`/`OnDisable` for active-only listeners and `Awake`/`OnDestroy` for object-lifetime listeners; follow the nearby subsystem when its semantics are deliberate. Never leave a static-bus listener attached after destruction.
- Name handlers consistently with nearby code, commonly `StaticBus_EventName` or `OnEventName`. Do not use a global bus for an implementation detail owned by a single object.

### State machines

- Model meaningful runtime modes with the installed `StateMachine<TEnum>` and `IStateMachine` rather than scattered boolean flags or a second custom FSM.
- The owning component creates the state machine, instantiates reusable state objects, registers enum-to-state mappings, selects the initial state explicitly, and forwards update/fixed-update calls only as supported by the installed framework.
- State implementations live beside the feature, normally in `Logic/<Feature>/State/`, and use names such as `Feature_State_Idle`. Implement the framework lifecycle (`Init`, `OnStart`, `OnUpdate`, `OnFixedUpdate`, `OnStop`, `OnDestroy`) without hiding unrelated behavior in the state.
- The owner remains the feature facade and holds shared dependencies; states receive the owner through construction and coordinate via its focused API. State transitions go through one owner method/property so entry/exit behavior is not bypassed.

### Components, caching, and lifecycle

- Prefer composition. A feature root coordinates focused sibling components; rendering, animation, input, movement, equipment, persistence, and UI should not collapse into one class when they have independent responsibilities.
- Use `MonoCachedHub<T>` when a component primarily belongs to and depends on a hub/root `T`; access that dependency through `Hub` and do not duplicate it with a serialized field, `Awake`, `OnValidate`, or repeated `GetComponent<T>()` solely for caching.
- Use `MonoCachedFast` and other installed cached-component bases consistently with nearby code. For authored dependencies not covered by the base class, use serialized references and optionally fill missing references in `OnValidate()`.
- Avoid `FindObjectOfType`, `GameObject.Find`, repeated `GetComponent`, LINQ, closures, and allocations in hot paths. Cache lookups, squared-distance comparisons, property blocks, pools, and tick throttling where measurements or call frequency justify them.
- Pair all event/value subscriptions with unsubscriptions, kill tweens owned by the component, return pooled objects, and cancel owned async work during the matching teardown callback.

### UniTask and cancellation

- Prefer `UniTask`/`UniTask<T>` for awaitable operations and reserve `UniTaskVoid`/`async void` for intentional fire-and-forget entry points or event callbacks. Observe/log exceptions using the project's established fire-and-forget helper.
- Every operation whose owner can be disabled, destroyed, replaced, or restarted must have a cancellation strategy. Reuse the project's `CancelToken` wrapper or Unity/C# `CancellationToken`, cancel the previous operation before replacing it, and cancel/dispose owned tokens on teardown.
- Pass cancellation tokens into delays, waits, loops, and external operations. Avoid polling every frame when an event or `WaitUntil` with cancellation expresses the lifecycle more clearly.
- Unity object access remains on the main thread unless a proven API is thread-safe. Do not use `Task.Run` for Unity gameplay work.

### Low-end mobile performance (default target)

Assume low-end Android (weak CPU, little RAM, tile-based GPU) unless the project says otherwise. CPU time (physics callbacks, `Update`, GC) and draw calls/overdraw usually matter more than raw polygon count. These rules come from `monkey-escape` and `knife-tower`; inspect the installed framework before using any named API, because namespaces differ (`CodeSketch.Optimize` vs the SketchEngine equivalent).

**Collision and trigger dispatch (`ICharacterCollidable` + `OptCollisionRegister`)**

- Do not give every platform, pickup, checkpoint or zone its own `OnTriggerEnter`/`OnCollisionEnter` that calls `GetComponent` on the other collider. Route contacts through the registry instead.
- The actor that moves (for example `Character`) is the single physics-callback owner. It derives from the installed `OptCollisionSensor<T>` / `OptCollisionSensorFast<T>` and forwards each event to the target: `OnCollisionEnterFunc(T target) => target.OnCollisionEnterFunc(this)`.
- World objects derive from the framework's `OptCollisionRegister` base and implement `ICharacterCollidable` (`OnCollisionEnterFunc`, `OnCollisionExitFunc`, `OnTriggerEnterFunc`, `OnTriggerExitFunc`, each taking the `Character`). They register their colliders in `OnEnable` and unregister in `OnDisable`; colliders are collected in `Awake`/`OnValidate`. Lookup is a dictionary read keyed by the collider's instance ID with zero `GetComponent` and zero allocation.
- The two frameworks differ here, so read the installed package before writing code:
  - **SketchEngine** (newer): `OptCollisionRegister` is NOT generic. An owner implements any number of interface families (`ICharacterCollidable`, `IMonsterCollidable`, ...), and the sensor `OptCollisionSensorFast<T>` filters owners with `owner is T`. Override `OnDisable`/`Awake` with `protected override` and call `base`.
  - **CodeSketch** (older): `OptCollisionRegister<T>` is generic, with `OptCollisionRegister2<T1, T2>` and `OptCollisionRegister<T1, T2, T3>` variants for several interface families.
  Never invent a second registration path beside the framework one.
- Keep callback bodies tiny and leave unused callbacks empty. Create a separate interface per actor family (for example `IEnemyCollidable`) instead of type-casting inside callbacks.
- If a callback needs captured context in CodeSketch, use the struct-based `OptCollisionLookup.ForEach<T, TAction>(collider, ref action)` overload, and cache any `Action<T>` delegate once instead of creating a lambda per event. In SketchEngine, query with `OptCollisionLookup.TryFindFirst<T>` / `TryGetAll<T>`.
- A world object with several colliders registers them all. Do not assume one collider per owner. Do not add a second registration path beside the framework one.
- Reset static collections used by zones/triggers with `[RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]` so domain-reload-off Editor sessions and scene reloads stay correct. The framework's own collision maps and some older zone scripts do not do this yet; do not copy that gap, and reset them where you touch them.

**Physics queries and settings**

- Use `Physics.*NonAlloc` with reusable buffers, explicit layer masks and an explicit `QueryTriggerInteraction`. Keep buffers sized for the realistic maximum.
- Cache a query result for the frame (compare `Time.frameCount`) when several systems ask the same thing. Throttle pathing/target updates with a squared-distance threshold instead of recomputing every frame.
- Compare distances with `sqrMagnitude`. Disable `Physics.autoSyncTransforms`, keep `reuseCollisionCallbacks` on, keep solver iterations at the engine default or lower, and keep colliders simple (primitives over mesh colliders). Verify these in `ProjectSettings/DynamicsManager.asset` rather than assuming.
- Keep the physics layer collision matrix tight: a layer pair that never needs contact must be disabled.

**Per-frame work**

- Avoid `Update`/`FixedUpdate` on large populations. Prefer events, `UniTask` waits, a single manager that ticks many entities, or the framework's `Tick`/`FixedTick` hooks if the installed `MonoCached` base dispatches them.
- When something does not need to run every frame, throttle by interval or stagger by index, and set `enabled = false` on idle or out-of-range components instead of early-returning inside `Update`.
- Avoid `Camera.main` in hot paths (cache it), per-call `new WaitForSeconds` (use `UniTask` delays or a cached instance), string building, LINQ and boxing.

**Visibility, culling and batching**

- Use event-driven distance culling with `CullingGroup`: set bounding spheres and distance bands once, subscribe to `onStateChanged`, and toggle `Renderer.enabled`/`TMP_Text.enabled` there. Do not loop over objects every frame measuring distance. Use this for sprites, world-space text and small props, and exclude indicators that must always be visible (for example countdown text). Dispose the group and unsubscribe in `OnDestroy`.
- Use per-zone camera far-clip trigger zones (`CameraFarDistanceZone` style) so enclosed areas render less. When zones overlap, choose the zone the player is deepest inside.
- Combine static meshes by material (`MeshSceneCombiner` style): bake renderer groups in the Editor, call `CombineMeshes` at load or under a per-frame millisecond budget, exclude dynamic/animated objects, and disable `LODGroup` after combining. Do not combine anything that moves, fades, toggles or is destroyed at runtime.
- Goal: one shared material for the whole world (Roblox-style vertex-color look), with per-family materials (map/decor, collectibles, tools) as the fallback when one material cannot render correctly. Character skins may keep their own shader (OmniShade). Custom shaders must be SRP Batcher compatible.
- Prefer SRP Batcher-compatible shaders and shared materials, and use GPU Instancing for large identical populations. `MaterialPropertyBlock` avoids material duplication but takes that renderer out of the SRP Batcher, so use it for a few per-instance values and measure before applying it to hundreds of renderers.
- Keep transparent surfaces, full-screen effects and particle counts small to limit overdraw. Prefer atlased textures and compressed formats (ASTC) with mipmaps on 3D textures.
- URP baseline for low-end: SRP Batcher on, single shadow cascade, small shadow map (512–1024), short shadow distance, no soft shadows, minimal additional lights, depth/opaque texture only when a feature needs them, MSAA off or 2x, HDR off unless required. The reference projects ship a Mobile URP asset (and a PC one) but tier at runtime through a device policy (GPU + RAM) rather than many Quality levels; reuse that split and never enable PC-grade settings on the mobile tier. Their Mobile asset is looser than this baseline (HDR on, soft shadows, longer shadow distance), so treat this baseline as the target and the reference as an upper bound.
- Cap the frame rate at 60 (vSync off, `Application.targetFrameRate = 60`) unless the project says otherwise; a higher cap costs battery and heat on low-end Android.

**UI**

- Split static and frequently-changing UI into separate canvases, turn off `Raycast Target` on non-interactive graphics, and avoid rebuilding TMP text every frame (only set text when the value changes).
- For layout groups that only need to lay out once, enable them, wait the needed frame(s), then disable them (the `OptCanvasLayout` pattern) so they stop triggering rebuilds.

**Memory and instantiation**

- Pool anything spawned repeatedly (VFX, projectiles, pickups, floating text) with the project's pool (the framework's `PoolPrefabGlobal` with `PoolPrefabConfig` assets and `Pool_Manager`; use LeanPool only if a project already depends on it). Do not `Instantiate`/`Destroy` in gameplay loops, and return pooled objects on disable.
- Load heavy content through the project's existing loading flow (Addressables or loader screen), and pay one-time costs such as mesh combining behind a loading screen.

**Verification**

- Do not claim a performance improvement without evidence. Use the Unity Profiler (or the `ivanmurzak` profiler tools such as rendering/script stats) on a representative scene, and say plainly when a change was not measured on a low-end device.
- Prefer a simple, measurable change over a clever one: remove work first, then batch it, then cache it, then optimize it.

### Implementation and verification rules for this house style

- Before creating a feature, inspect at least one analogous `Data_*`, `Factory_*`, event publisher/subscriber pair, state-machine owner/state pair, and async owner in the current project. Match its actual framework namespaces and lifecycle.
- For new persistent/configured features, consider the complete chain: data record, config asset type, factory registry, asset location, runtime consumer, events, prefab/scene wiring, and initialization order. Do not stop after generating C# files.
- Prefer `ivanmurzak` MCP for Unity Editor work and verification. Do not use Unity AI Assistant unless explicitly requested. Discover the available `ivanmurzak` tools and connection first; use read-only inspection before mutation.
- After file changes, refresh/compile through Unity when available, inspect Console errors, verify created assets and serialized references, and run relevant EditMode/PlayMode tests. A successful external C# build alone is not proof that Unity serialization, scenes, or prefabs are correct.
- When Unity MCP is unavailable or connected to a different project, make only safe file-based changes, state exactly what was not Editor-verified, and never claim scene/prefab/Console validation occurred.

## UI centre alignment (mandatory)

- Before building or editing ANY Unity UI (popups, bars, buttons, tabs, icon + text, currency bars), read `skills/ui-center-alignment/SKILL.md` and follow it.
- Always centre content yourself: measure container vs content bounds by script (tolerance <= 1 px), keep siblings on one row at the same y centre, prefer layout groups over hand offsets, and never finish UI work without that check plus a screenshot.
- Do not wait for the user to ask for centring; misaligned bars/labels are a defect to fix before reporting done.

## Unity prefab and ready-to-play workflow

- Follow the full workflow: plan, implement, wire, save, compile, and test. Never report a gameplay feature complete after only creating scripts.
- When a target is a prefab instance or appears under Prefab Mode in Context, modify the source prefab asset and apply/save it. Do not leave a scene-only override unless explicitly requested.
- After wiring, inspect the source prefab and a scene instance, verify serialized references, refresh/compile Unity, and test the relevant Play Mode path before reporting completion.

## Agent team and Play testing (mandatory)

- Multi-agent work: follow `agent-team-protocol` (briefs, FIFO Editor lock with heartbeat, keep the project compiling, stop and report on a denied call, report file + short final answer).
- Before any Play test or screenshot: claim blocking reward/offline popups with a real tap, back up the save, restore it after (`playmode-driver-recipes`).
- Scene or mode switching code must pass the repeated scene-flow test in `scene-teardown-safety`.

## Gem buttons (standing rule)

- Every button that spends Gems (shops, popups, skin/pickaxe/trail cards, every minigame) uses a YELLOW squarer sliced sprite (`Gem_UiConfig.ButtonGem`), a gem icon + price (shortened K/M/B/T with `UtilityNumber.Format`), red price text when the player is short, and ALWAYS carries `Gem_ButtonPulse` (gentle scale up/down) so the player focuses on it. Create with `Gem_Ui.CreateGemButton` or call `Gem_ButtonPulse.Attach(button)`.
- Short on Gems inside a minigame: tapping the button calls `Gem_TopUp.Run(cost, onReady)`, which buys the nearest Home Gem pack (`com.thunder.egg.gem1..6`, smallest pack that covers the missing Gems) with `IAPManager.Purchase`; on success the Gems are already in `Data_Currency.Gem`, then spend the price and unlock the item without asking again. In the Home shop the same case jumps to the Gem tab (`Shop_Common.OpenTab(Shop_Common_Type.Gem)`) instead. All spends go through `Gem_Shop.Buy` / `Break_Gem_Shop.Buy`, never subtract Gems elsewhere.
- IAP funnel logs: `LogHelper.IAPPurchaseSuccess` is called once, right after `BounceSdk.LogIAPSuccess` in `IAPManager.IAPListener_OnPurchaseComplete`; do not call it from buttons or purchase callbacks.

## Money text (standing rule)

- In-game cash / money is always written as a bare shortened number (`+5M`, `150M`, `1B`), never with a `$` sign, in every label, toast, subtitle and placeholder. Real-store prices keep their currency text.
- A reward-ad skin has ONE reward button only (no extra Gem button next to it); pickaxes and trails have no reward button.

## UI and text (automatic, every project, mandatory)

- Before ANY UI, popup, HUD, button, world-canvas or text work, read the `ui-text-autofit-system` skill and make sure the project has the `UI_TextAutoFit` system installed (install it if missing). Text fitting is automatic: auto size, padding from frames/buttons/shadows, no overflow, centred icon+label groups, never a `$` prefix on money. HARD RULE: text (its rect AND its rendered bounds) must never extend outside its parent/frame or overlap a sibling icon, never use ellipsis (shrink to min 10 instead), and overlays (banners/native half/tutorial hints) must never cover popup content; verify with a scripted rect/textBounds measurement over every popup state, not by eye.
- Do not wait to be asked to align or fit text. Every new or changed UI is built correctly, normalised by the system, then verified by measurement (`textBounds` vs rect) and a screenshot in Play Mode before reporting done.

## Shops, popups and HUD polish (automatic, every project, mandatory)

- For ANY shop, popup, HUD, tab, card, button or text task load, without being asked: `ui-always` (+ the skills it names), `shop-tab-page-checklist` (shops, tabs, packs), `ui-center-alignment`, `ui-text-tmp`, `ui-icon-label-layout`, `ui-button-anatomy`, `native-ad-beside-popup` (anything shown beside the native half). Never wait for the user to name them.
- Price / amount buttons are ONE centred HorizontalLayoutGroup: icon LEFT, number RIGHT (preferred width, no fixed text slot). Names and amounts are BIG, outlined and clear (the user's priority: players must see at a glance what a purchase gives); keep a hierarchy and consistency inside a card family.
- A notify dot / badge sits fully inside the clipping viewport of its host; icons and labels in a tab are centred in the free gap next to the icon art, one font size per tab column, tabs ~100 px tall.
- Self-verify before reporting: enter Play, capture a screenshot (ScreenCapture) and measure with serialized rects or textBounds. Never hand the check to the user. If something cannot be verified say so plainly.
- Multi-agent work: split by disjoint files, agents never enter Play Mode, the coordinator runs ONE Play pass for everybody at the end, and re-reads every prefab value back after saving (components that animate in the prefab stage overwrite edits on save: disable them, edit, re-enable, save in the same call). Never use world corners of a prefab loaded outside a canvas for layout maths.
- HARD GATE, icon + text (every button, pill, price plate, ad/hatch/free button, header): build it as ONE HorizontalLayoutGroup (icon first, label second, Capline centre, bottom padding = the sprite lip) and, before replying, measure the INK from a Play screenshot (pixel scan: face rows of the button vs white text rows vs icon rows) - the pair centre must be within 2 px of the button FACE centre (not the rect centre) horizontally and vertically, and titles within 2 px of the colour band centre (`ui-title-band-centering`, `band_scan.py`). A hand-positioned icon beside a stretched label is a defect. Fix and re-measure until it passes; report the dx/dy numbers. The user must never have to screenshot and ask again.
- Ads: one global banner service (Ads_Banner style): always on, ShowBanner via AdsHelper every 15 s, immediately after a native closes or a scene loads; no local interstitial cooldown (the Bounce SDK owns spacing).
