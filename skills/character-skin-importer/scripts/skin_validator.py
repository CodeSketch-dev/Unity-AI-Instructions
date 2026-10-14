"""Validate a character catalog and skin prefabs (read-only, stdlib only).

Usage:
  py -I skin_validator.py catalog <catalog.json>
  py -I skin_validator.py prefab  <skin.prefab> --catalog <catalog.json> --rig <rigId> [--role player|bot] [--stats stats.json]

catalog checks (FAIL unless noted): duplicate/unknown skin ids and rigs and types, unlock rules (Free price 0,
Gem/Coin price > 0, IAP needs iap_id, unlock must be one of Free/Gem/Coin/IAP/Ads/Daily/Subscription), allowed types per
mode exist, rig slots point at rig bones, rig bone count <= rig max_bones, duplicate skin order (WARN).
prefab checks: skeleton = ordered SkinnedMeshRenderer bones equal the rig's required bones (bone-mismatch, reports
missing/extra; equal -> info shared-mesh-ok with the skeleton hash), bone and material budgets, exactly one Animator,
bot culling mode CullCompletely (WARN), bot shadows off (WARN), updateWhenOffscreen off (WARN), no baked Rigidbody/Joint
(baked-ragdoll), no Camera/Light, no missing scripts. stats.json ({"tris": n, "texture": px}) comes from the Editor
importer (report 19 sec 3.4) because triangle counts are not stored in prefab YAML. Budgets are INFERRED starting values.
"""
import json
import os
import re
import sys
from collections import namedtuple

Finding = namedtuple("Finding", "level code where message")
UNLOCKS = {"Free", "Gem", "Coin", "IAP", "Ads", "Daily", "Subscription"}
DOC_RE = re.compile(r"^--- !u!(\d+) &(-?\d+)", re.M)


def skeleton_hash(bones):
    """FNV-1a 32-bit over the ordered bone names joined by '|' (stable; equal hash = same skeleton contract)."""
    h = 0x811C9DC5
    for byte in "|".join(bones).encode("utf-8"):
        h = ((h ^ byte) * 0x01000193) & 0xFFFFFFFF
    return h


def check_catalog(cat):
    out = []
    rigs, types = cat.get("rigs", {}), set(cat.get("skin_types", []))
    for rid, rig in rigs.items():
        bones = rig.get("required_bones", [])
        if len(bones) > rig.get("max_bones", 10 ** 9):
            out.append(Finding("FAIL", "rig-over-limit", rid, "%d required bones exceed max_bones %s" % (len(bones), rig.get("max_bones"))))
        for slot in rig.get("slots", []):
            if slot["bone"] not in bones:
                out.append(Finding("FAIL", "slot-bone-missing", rid, "slot %r uses bone %r that is not in required_bones" % (slot["id"], slot["bone"])))
    seen, orders = set(), {}
    for s in cat.get("skins", []):
        sid = s.get("id")
        if sid in seen:
            out.append(Finding("FAIL", "duplicate-skin-id", str(sid), "skin id used twice"))
        seen.add(sid)
        if s.get("rig") not in rigs:
            out.append(Finding("FAIL", "unknown-rig", str(sid), "rig %r is not defined" % s.get("rig")))
        if types and s.get("type") not in types:
            out.append(Finding("FAIL", "unknown-type", str(sid), "type %r is not in skin_types" % s.get("type")))
        u, price = s.get("unlock"), s.get("price", 0) or 0
        if u not in UNLOCKS:
            out.append(Finding("FAIL", "bad-unlock", str(sid), "unlock %r not one of %s" % (u, sorted(UNLOCKS))))
        if u == "IAP" and not s.get("iap_id"):
            out.append(Finding("FAIL", "iap-without-id", str(sid), "IAP skin needs iap_id"))
        if u in ("Gem", "Coin") and price <= 0:
            out.append(Finding("FAIL", "gem-without-price", str(sid), "%s skin needs a positive price" % u))
        if u == "Free" and price != 0:
            out.append(Finding("FAIL", "free-with-price", str(sid), "Free skin has price %s" % price))
        orders.setdefault(s.get("order"), []).append(sid)
    for order, ids in orders.items():
        if len(ids) > 1:
            out.append(Finding("WARN", "duplicate-order", ",".join(map(str, ids)), "same order %s" % order))
    for mode, allowed in (cat.get("allowed_types_per_mode") or {}).items():
        for t in allowed:
            if types and t not in types:
                out.append(Finding("FAIL", "unknown-mode-type", mode, "mode allows unknown type %r" % t))
    return out


def _docs(text):
    marks = list(DOC_RE.finditer(text))
    for i, m in enumerate(marks):
        yield int(m.group(1)), int(m.group(2)), text[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]


def _field(body, key):
    m = re.search(r"^\s+%s:\s*(.*?)\s*$" % re.escape(key), body, re.M)
    return m.group(1) if m else None


def _list_refs(body, key):
    m = re.search(r"^\s+%s:\s*\n((?:\s+- .*\n?)*)" % re.escape(key), body, re.M)
    return re.findall(r"fileID:\s*(-?\d+)", m.group(1)) if m else []


def check_prefab(path, rig, budget, role="bot", stats=None):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    go_name, tr_go, smrs, animators = {}, {}, [], []
    counts = {"rigidbody": 0, "joint": 0, "camera": 0, "light": 0, "missing": 0}
    for cls, fid, body in _docs(text):
        if cls == 1:
            go_name[fid] = (_field(body, "m_Name") or "").strip()
        elif cls == 4:
            m = re.search(r"m_GameObject:\s*\{fileID:\s*(-?\d+)", body)
            tr_go[fid] = int(m.group(1)) if m else 0
        elif cls == 137:
            smrs.append(body)
        elif cls == 95:
            animators.append(body)
        elif cls in (54, 144, 143, 57, 153):
            counts["rigidbody" if cls == 54 else "joint"] += 1
        elif cls == 20:
            counts["camera"] += 1
        elif cls == 108:
            counts["light"] += 1
        elif cls == 114 and re.search(r"m_Script:\s*\{fileID:\s*0\}", body):
            counts["missing"] += 1
    out = []
    where = os.path.basename(path)
    if counts["missing"]:
        out.append(Finding("FAIL", "missing-script", where, "%d component(s) with a missing script" % counts["missing"]))
    if counts["rigidbody"] or counts["joint"]:
        out.append(Finding("FAIL", "baked-ragdoll", where, "%d Rigidbody / %d joint on the skin prefab; use the shared pooled ragdoll prefab" % (counts["rigidbody"], counts["joint"])))
    if counts["camera"] or counts["light"]:
        out.append(Finding("FAIL", "camera-or-light", where, "skin prefab contains a Camera or Light"))
    if len(animators) != 1:
        out.append(Finding("FAIL", "animator-count", where, "expected exactly one Animator, found %d" % len(animators)))
    elif role == "bot" and _field(animators[0], "m_CullingMode") != "2":
        out.append(Finding("WARN", "bot-culling", where, "bots should use Animator CullCompletely (2)"))
    required = rig.get("required_bones", [])
    for body in smrs:
        names = [go_name.get(tr_go.get(int(b)), "?") for b in _list_refs(body, "m_Bones")]
        if names != required:
            missing = [b for b in required if b not in names]
            extra = [b for b in names if b not in required]
            order = "" if (missing or extra) else " (same bones, different order)"
            out.append(Finding("FAIL", "bone-mismatch", where, "skeleton differs: missing %s extra %s%s" % (missing, extra, order)))
        else:
            out.append(Finding("INFO", "shared-mesh-ok", where, "skeleton hash %08x matches the rig" % skeleton_hash(names)))
        limit = min(rig.get("max_bones", 10 ** 9), budget.get("bones", 10 ** 9))
        if len(names) > limit:
            out.append(Finding("FAIL", "too-many-bones", where, "%d bones > %d" % (len(names), limit)))
        mats = len(_list_refs(body, "m_Materials"))
        if mats > budget.get("materials", 10 ** 9):
            out.append(Finding("FAIL", "too-many-materials", where, "%d materials > %d" % (mats, budget["materials"])))
        if role == "bot" and _field(body, "m_CastShadows") not in (None, "0"):
            out.append(Finding("WARN", "bot-shadows", where, "bots should not cast real shadows"))
        if _field(body, "m_UpdateWhenOffscreen") == "1":
            out.append(Finding("WARN", "update-offscreen", where, "updateWhenOffscreen costs CPU; set local bounds instead"))
    if stats:
        if stats.get("tris", 0) > budget.get("tris", 10 ** 9):
            out.append(Finding("FAIL", "tri-budget", where, "%s tris > %s" % (stats["tris"], budget["tris"])))
        if stats.get("texture", 0) > budget.get("texture", 10 ** 9):
            out.append(Finding("FAIL", "texture-budget", where, "%s px texture > %s" % (stats["texture"], budget["texture"])))
    return out


def _print(findings):
    for f in findings:
        print("%s %s [%s] %s" % (f.level, f.code, f.where, f.message))
    fails = sum(1 for f in findings if f.level == "FAIL")
    print("%d fail(s), %d warning(s)" % (fails, sum(1 for f in findings if f.level == "WARN")))
    return 1 if fails else 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2 or argv[0] not in ("catalog", "prefab"):
        print(__doc__, file=sys.stderr)
        return 2
    opts = {}
    for i, a in enumerate(argv):
        if a.startswith("--") and i + 1 < len(argv):
            opts[a] = argv[i + 1]
    try:
        if argv[0] == "catalog":
            with open(argv[1], encoding="utf-8") as f:
                return _print(check_catalog(json.load(f)))
        with open(opts["--catalog"], encoding="utf-8") as f:
            cat = json.load(f)
        role = opts.get("--role", "bot")
        stats = None
        if "--stats" in opts:
            with open(opts["--stats"], encoding="utf-8") as f:
                stats = json.load(f)
        return _print(check_prefab(argv[1], cat["rigs"][opts["--rig"]], cat["budgets"][role], role, stats))
    except (OSError, KeyError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
