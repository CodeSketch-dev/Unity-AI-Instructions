"""Deterministic GDD -> task graph generator (stdlib only; no LLM needed).

Usage: py -I gen_task_graph.py <gdd-dir> [--out task-graph.json] [--day-h 16] [--no-cut]
Reads the GDD (see gdd_lint.load_gdd), instantiates the task template of every system type, adds the cross-cutting
tasks (bootstrap, gates, audits, build), resolves `depends_on`, assigns phases, groups and estimates, and cuts scope
(P2 then P1) when the wall-clock estimate exceeds the day budget. Emits task-graph.json and task-graph.md.
Agents: P producer, D dev (file lane, worktree), B builder (Editor lane, serial), U UI agent, T tester.
Estimates are starting guesses (report 21 sec 3.6) to be recalibrated after the pilot.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gdd_lint  # noqa: E402

FILE_LANE_WORKERS = 4

# type -> list of (key, title, phase, skills, agent, est_h, claims, verify)
TEMPLATES = {
    "character": [
        ("controller", "Character data and controller", 2, ["kcc-character-controller", "config-driven-feature"], "D", 1.2, ["code:Logic/Character/*"], ["[edit] feel numbers", "[play] move and jump path"]),
        ("wiring", "Character prefab wiring and animation", 2, ["character-rig-and-animation-contract", "done-means-wired"], "B", 0.6, ["prefab:Character"], ["[play] animation states"]),
    ],
    "camera": [("camera", "Camera rig and input axes", 2, ["freelook-third-person-camera"], "D", 0.8, ["code:Logic/Camera/*"], ["[play] orbit works"])],
    "input": [("input", "Joystick, look drag and buttons", 2, ["mobile-input-controls", "mobile-hud-layout"], "D", 0.8, ["code:Logic/Input/*"], ["[play] joystick region, no overlap"])],
    "interactable": [
        ("registry", "Collision-registry interactables", 2, ["collision-registry", "platform-kit", "checkpoint-respawn"], "D", 1.0, ["code:Logic/Interact/*"], ["[edit] trigger fires once", "no GetComponent in callbacks"]),
        ("respawn", "Respawn, fall and death loop", 2, ["checkpoint-respawn", "clone-feature-recipes"], "D", 0.8, ["code:Logic/Run/*"], ["[play] respawn at checkpoint"]),
    ],
    "economy": [
        ("tables", "Economy tables to config assets, wallet and events", 2, ["economy-progression-design", "economy-loop-archetypes", "config-and-factory-authoring", "data-block-template"], "D", 0.7, ["asset:SingletonAssets/Factory_Economy"], ["[edit] wallet and events"]),
    ],
    "shop": [
        ("logic", "Shop logic: buy, equip, persist", 3, ["config-and-factory-authoring", "recipe-add-skin-or-item", "done-means-wired"], "D", 0.8, ["code:Logic/Shop/*"], ["[edit] insufficient funds unchanged", "[play] restart persists"]),
        ("catalog", "Catalog fill from tables (assets and icons)", 4, ["reference-port", "asset-transfer-closure"], "D", 1.0, ["asset:Configs/Shop"], ["[edit] data audit equals prices.csv"]),
    ],
    "inventory": [("inventory", "Inventory and hotbar", 4, ["hotbar-inventory"], "D", 1.0, ["code:Logic/Inventory/*"], ["[play] pick, equip, full state"])],
    "pets": [("pets", "Pets: data, follow, equip", 4, ["cosmetic-slot-providers", "config-and-factory-authoring"], "D", 1.5, ["code:Logic/Pet/*"], ["[play] pet follows and income"])],
    "quests": [("quests", "Quests and tracker", 4, ["recipe-quests-achievements", "ui-pattern-library"], "D", 1.0, ["code:Logic/Quest/*"], ["[play] quest completes and claims"])],
    "tutorial": [("tutorial", "Tutorial steps and pointers", 4, ["tutorial-phase-system", "unity-ui"], "D", 0.6, ["code:Logic/Tutorial/*"], ["[play] full tutorial path"])],
    "audio": [("audio", "Audio factory and sfx wiring", 4, ["game-audio-system", "sfx-variation-ducking"], "D", 0.5, ["code:Logic/Audio/*"], ["[inspect] each event has sfx"])],
    "vfx": [("vfx", "Pooled effects", 4, ["vfx-budget-rules", "pool-everything", "game-feel-polish"], "D", 0.6, ["code:Logic/Vfx/*"], ["[inspect] pooled and within budget"])],
    "monetization": [
        ("ads", "Ads layer (mock), consent, rewarded flows", 5, ["monetization-integration", "ads-layer-generic", "ads-popup-flow"], "D", 0.8, ["code:Logic/Ads/*"], ["[play] mock flows, ad failure never blocks"]),
        ("iap", "IAP stubs and grants", 5, ["iap-catalog", "unity-iap-port"], "D", 0.6, ["code:Logic/Iap/*"], ["[play] grant once"]),
    ],
    "retention": [("daily", "Daily reward and retention", 5, ["recipe-daily-login", "recipe-retention-timers"], "D", 0.6, ["code:Logic/Retention/*"], ["[play] claim once per day"])],
    "localization": [("strings", "String table and runtime lookup", 3, ["ui-localization", "localization-pipeline"], "D", 0.5, ["asset:Localization"], ["[inspect] no hard-coded text"])],
    "bots": [("bots", "Bots as players", 4, ["bots-as-players", "bot-brain-waypoints"], "D", 1.2, ["code:Logic/AI/*"], ["[play] bots finish the course"])],
    "minigame": [("minigame", "Minigame registration and scene", 4, ["recipe-add-minigame", "minigame-registration", "scene-flow-loading"], "D", 1.0, ["asset:Factory_Minigame"], ["[play] entry loads the scene"])],
}
UI_EST = {"hud": 1.2, "popup_modal": 0.9, "popup_fullscreen": 1.4, "world_board": 0.8, "toast": 0.4, "banner": 0.4}
CROSS = [  # (key, title, phase, skills, agent, est, claims, verify, system_dependent)
    ("lint", "Lint and freeze the GDD, generate the plan", 0, ["gdd-intake", "game-clone-recon"], "P", 0.3, ["file:gdd/_generated/*", "file:gdd/_generated/evidence-index.json"], ["lint 0 BLOCK", "evidence index valid"]),
    ("visual-evidence", "Index reference images for visual reconstruction", 0, ["clone-pipeline", "game-clone-recon"], "P", 0.2, ["file:gdd/_generated/evidence-index.json"], ["evidence index valid", "--require-images passes"]),
    ("visual-mapspec", "Emit and validate the compact visual MapSpec", 1, ["roblox-shader-kit", "clone-pipeline"], "P", 0.4, ["file:gdd/_generated/map-spec.json"], ["MapSpec schema valid", "unknowns explicit"]),
    ("specs", "Short specs for P0 systems", 0, ["spec-then-plan"], "D", 0.5, ["file:docs/specs/*"], ["specs exist per P0 system"]),
    ("provenance", "Asset provenance and reference index", 0, ["reference-index", "clone-ip-safety", "asset-transfer-closure"], "D", 0.2, ["file:docs/asset-provenance.md"], ["all ref-project paths resolve"]),
    ("bootstrap", "Project bootstrap: URP, folders, asmdefs, framework map, MCP", 1, ["unity-project-bootstrap", "new-game-bootstrap", "framework-version-map", "unity-mcp-workflow"], "B", 0.7, ["asset:ProjectSettings"], ["compile, Console clean"]),
    ("bootdata", "Boot scene, Data/Factory scaffolding, cheats menu", 1, ["boot-sequence-setup", "config-and-factory-authoring", "debug-cheats-menu"], "D", 0.5, ["code:Core/*"], ["[edit] boot test"]),
    ("map", "Project map and guard scripts", 1, ["project-context-map", "multi-agent-coexistence"], "D", 0.3, ["file:docs/PROJECT-MAP.md"], ["map paths exist"]),
    ("gate2", "Gate G2: golden path steps for the core loop", 2, ["playmode-script-testing", "unity-qa-playtest", "qa-fix-retest-loop"], "T", 0.6, ["file:Tests/PlayMode/*"], ["[play] golden path core steps"]),
    ("balance", "Generate and simulate the balance plan", 2, ["auto-balance-game", "auto-balance-loop", "config-and-factory-authoring"], "D", 0.7, ["file:gdd/_generated/balance-plan.json"], ["balance validator 0 errors", "simulation reaches target tolerance"]),
    ("gate3", "Gate G3: screenshots and layout checks", 3, ["ui-validator", "ui-visual-qa", "qa-fix-retest-loop"], "T", 0.5, ["file:qa/shots/*"], ["[shot] 3 aspect ratios"]),
    ("audit", "Wiring audit, data audit, Console triage", 6, ["done-means-wired", "unity-log-triage", "qa-static-checks", "qa-editmode-validators"], "T", 0.6, ["file:qa/reports/*"], ["zero missing refs"]),
    ("perf", "Performance audit on the Mobile tier", 6, ["mobile-perf-audit", "profiling-evidence", "qa-playmode-smoke"], "T", 0.8, ["file:qa/reports/*"], ["budgets within tier"]),
    ("regress", "Regression of all gates and full golden path", 6, ["playmode-script-testing", "rule-qa-validity", "rule-qa-verdicts", "qa-fix-retest-loop"], "T", 0.5, ["file:qa/*"], ["all gates green"]),
    ("build", "Android build and release checklist", 7, ["mobile-build-release", "unity-batch-build"], "B", 0.6, ["file:Build/*"], ["build ok, gate script"]),
]
PRIO = {"P0": 0, "P1": 1, "P2": 2}


def _task(tid, system, key, title, phase, skills, agent, est, claims, verify, prio):
    return {"id": tid, "system": system, "key": key, "title": title, "phase": phase, "skills": skills, "agent": agent,
            "claims": claims, "depends_on": [], "est_h": est, "verify": verify, "priority": prio, "status": "pending", "attempts": 0}


def generate(g, day_h=16, cut=True):
    tasks, by_system = [], {}
    n = [0]

    def new(*a):
        n[0] += 1
        t = _task("T%02d" % n[0], *a)
        tasks.append(t)
        return t

    cross = {}
    for key, title, phase, skills, agent, est, claims, verify in CROSS:
        cross[key] = new("pipeline", key, title, phase, skills, agent, est, claims, verify, "P0")
    for name, v in g["systems"].items():
        fm = v["fm"]
        typ, prio = fm.get("type"), fm.get("priority", "P1")
        chain = []
        if typ == "world":
            for z in fm.get("zones") or []:
                first = z.get("index", 0) == 0
                chain.append(new(fm.get("id", name), "zone-" + str(z.get("id")), "Zone %s greybox, hazards and checkpoints" % z.get("name", z.get("id")),
                                 2 if first else 4, ["zone-level-design", "roblox-world-kit", "mesh-merge-baker"], "B", 1.3 if first else 1.5,
                                 ["scene:Game"], ["[play] path reachable", "[inspect] renderers within budget"], prio if first else "P1"))
        else:
            for key, title, phase, skills, agent, est, claims, verify in TEMPLATES.get(typ, []):
                chain.append(new(fm.get("id", name), key, title, phase, skills, agent, est, list(claims), list(verify), prio))
        if typ == "interactable":
            kinds = fm.get("kinds") or []
            chain[0]["est_h"] = round(0.4 + 0.15 * len(kinds), 2)
        by_system[fm.get("id", name)] = chain
        for a, b in zip(chain, chain[1:]):
            if typ != "world":
                b["depends_on"].append(a["id"])
    for name, v in g["systems"].items():
        fm = v["fm"]
        for dep in fm.get("depends_on") or []:
            for t in by_system.get(fm.get("id", name), [])[:1]:
                if by_system.get(dep):
                    t["depends_on"].append(by_system[dep][-1]["id"])
    for name, v in g["ui"].items():
        fm = v["fm"]
        est = UI_EST.get(fm.get("kind"), 0.9)
        prio = fm.get("priority", "P1")
        build = new(fm.get("id", name), "ui-build", "Build %s from its layout contract" % fm.get("id", name), 3, ["ui-builder", "ui-pattern-library", "unity-ui"], "U", est, ["prefab:" + str(fm.get("id", name))], ["[shot] 3 aspect ratios", "ui_validator 0 FAIL"], prio)
        bind = new(fm.get("id", name), "ui-bind", "Bind %s to systems and events" % fm.get("id", name), 3, ["done-means-wired", "static-bus-events"], "D", 0.4, ["code:Logic/UI/" + str(fm.get("id", name))], ["[play] opens and closes"], prio)
        bind["depends_on"].append(build["id"])
        build["depends_on"].append(cross["bootstrap"]["id"])
    # cross-cutting edges
    boot, bootdata = cross["bootstrap"]["id"], cross["bootdata"]["id"]
    cross["bootdata"]["depends_on"] += [boot]
    cross["map"]["depends_on"] += [boot]
    cross["specs"]["depends_on"] += [cross["lint"]["id"]]
    cross["visual-evidence"]["depends_on"] += [cross["lint"]["id"]]
    cross["visual-mapspec"]["depends_on"] += [cross["visual-evidence"]["id"]]
    cross["provenance"]["depends_on"] += [cross["lint"]["id"]]
    cross["bootstrap"]["depends_on"] += [cross["specs"]["id"]]
    for t in tasks:
        if t["system"] not in ("pipeline",) and t["phase"] >= 2 and bootdata not in t["depends_on"]:
            t["depends_on"].append(bootdata)
    p2 = [t["id"] for t in tasks if t["phase"] == 2 and t["system"] != "pipeline"]
    cross["gate2"]["depends_on"] += p2
    cross["balance"]["depends_on"] += p2
    cross["gate2"]["depends_on"] += [cross["balance"]["id"]]
    p3 = [t["id"] for t in tasks if t["phase"] == 3 and t["system"] != "pipeline"]
    cross["gate3"]["depends_on"] += p3 + [cross["gate2"]["id"]]
    later = [t["id"] for t in tasks if t["phase"] in (4, 5)]
    cross["audit"]["depends_on"] += later + [cross["gate3"]["id"]]
    cross["perf"]["depends_on"] += [cross["audit"]["id"]]
    cross["regress"]["depends_on"] += [cross["audit"]["id"], cross["perf"]["id"]]
    cross["build"]["depends_on"] += [cross["regress"]["id"]]
    for t in tasks:
        t["depends_on"] = sorted(set(t["depends_on"]) - {t["id"]})
    dropped = []
    if cut:
        dropped = apply_cut(tasks, day_h)
    return finalize(tasks, dropped, day_h)


def _depths(tasks):
    by = {t["id"]: t for t in tasks}
    memo = {}

    def d(i):
        if i not in memo:
            memo[i] = 1 + max([d(x) for x in by[i]["depends_on"] if x in by] or [0])
        return memo[i]
    return {t["id"]: d(t["id"]) for t in tasks}


def _longest(tasks):
    by = {t["id"]: t for t in tasks}
    memo = {}

    def f(i):
        if i not in memo:
            memo[i] = by[i]["est_h"] + max([f(x) for x in by[i]["depends_on"] if x in by] or [0])
        return memo[i]
    return max([f(t["id"]) for t in tasks] or [0])


def totals(tasks):
    s = sum(t["est_h"] for t in tasks)
    editor = sum(t["est_h"] for t in tasks if t["agent"] in ("B", "U"))
    crit = _longest(tasks)
    return {"sum_h": round(s, 2), "critical_path_h": round(crit, 2), "editor_lane_h": round(editor, 2),
            "wall_h": round(max(crit, editor, s / (FILE_LANE_WORKERS + 1)), 2)}


def apply_cut(tasks, day_h):
    dropped = []
    for prio in ("P2", "P1"):
        if totals(tasks)["wall_h"] <= day_h:
            break
        ids = {t["id"] for t in tasks if t["priority"] == prio and t["system"] != "pipeline"}
        if not ids:
            continue
        dropped += [t["id"] for t in tasks if t["id"] in ids]
        tasks[:] = [t for t in tasks if t["id"] not in ids]
        for t in tasks:
            t["depends_on"] = [d for d in t["depends_on"] if d not in ids]
    return dropped


def finalize(tasks, dropped, day_h):
    depth = _depths(tasks)
    waves = {}
    for t in tasks:
        waves.setdefault(t["phase"], set()).add(depth[t["id"]])
    wave_index = {p: {d: i + 1 for i, d in enumerate(sorted(ds))} for p, ds in waves.items()}
    groups = {}
    for t in sorted(tasks, key=lambda x: (x["phase"], depth[x["id"]], x["id"])):
        key = (t["phase"], depth[t["id"]])
        slots = groups.setdefault(key, [])
        label = "G%d.%d" % (t["phase"], wave_index[t["phase"]][depth[t["id"]]])
        for letter, members in enumerate(slots):
            if not any(set(t["claims"]) & set(m["claims"]) for m in members) and not (t["agent"] in ("B", "U") and any(m["agent"] in ("B", "U") for m in members)):
                members.append(t)
                t["group"] = label + chr(97 + letter)
                break
        else:
            slots.append([t])
            t["group"] = label + chr(97 + len(slots) - 1)
    tasks.sort(key=lambda x: (x["phase"], depth[x["id"]], x["id"]))
    return {"schema": 1, "tasks": tasks, "dropped": dropped, "day_h": day_h, "totals": totals(tasks)}


def to_markdown(graph):
    lines = ["# Task graph", "", "Totals: %s" % json.dumps(graph["totals"]), "Dropped (scope cut): %s" % (", ".join(graph["dropped"]) or "none"), "",
             "| Id | Ph | Task | Skills | Ag | Claims | Verify | Grp | h | Deps |", "|---|---|---|---|---|---|---|---|---|---|"]
    for t in graph["tasks"]:
        lines.append("| %s | %d | %s | %s | %s | %s | %s | %s | %.1f | %s |" % (t["id"], t["phase"], t["title"], ", ".join(t["skills"]), t["agent"],
                     ", ".join(t["claims"]), "; ".join(t["verify"]), t["group"], t["est_h"], ", ".join(t["depends_on"])))
    return "\n".join(lines) + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or not os.path.isdir(argv[0]):
        print(__doc__, file=sys.stderr)
        return 2
    day_h = float(argv[argv.index("--day-h") + 1]) if "--day-h" in argv else 16.0
    g = gdd_lint.load_gdd(argv[0])
    graph = generate(g, day_h, cut="--no-cut" not in argv)
    out = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(argv[0], "_generated", "task-graph.json")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(graph, f, indent=1)
    with open(os.path.splitext(out)[0] + ".md", "w", encoding="utf-8", newline="\n") as f:
        f.write(to_markdown(graph))
    print("%d tasks, %s, dropped %d" % (len(graph["tasks"]), json.dumps(graph["totals"]), len(graph["dropped"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
