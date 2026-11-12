"""Mine UI design tokens from Unity prefabs (read-only, text YAML, stdlib only).

Usage: py -I ui_miner.py <unity-project> [--root Assets/_Game] [--out tokens.json] [--no-resolve]
Scans *.prefab under --root (default Assets). Emits canvas settings, button sizes and
co-attached scripts, TMP/Image stats, ScrollRect insets, layout spacing, grid cells and
name prefixes. Values are observations from the project, not rules: use them as soft
defaults (see ui-design-tokens). Only direct prefab objects are read; nested prefab
instance overrides are not resolved.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

DOC_RE = re.compile(r"^--- !u!(\d+) &(-?\d+)", re.M)
VEC_RE = re.compile(r"\{x:\s*(-?[\d.eE+-]+),\s*y:\s*(-?[\d.eE+-]+)")


def num(v):
    f = float(v)
    return int(f) if f == int(f) else round(f, 3)


def field(body, key):
    m = re.search(r"^\s+%s:\s*(.*?)\s*$" % re.escape(key), body, re.M)
    return m.group(1) if m else None


def vec(body, key):
    v = field(body, key)
    m = VEC_RE.search(v) if v else None
    return (num(m.group(1)), num(m.group(2))) if m else None


def ref(body, key):
    v = field(body, key)
    m = re.search(r"fileID:\s*(-?\d+)", v or "")
    return int(m.group(1)) if m else None


def guid_of(body):
    m = re.search(r"m_Script:.*?guid:\s*([0-9a-f]{32})", body)
    return m.group(1) if m else None


def split_docs(text):
    marks = list(DOC_RE.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        yield int(m.group(1)), int(m.group(2)), text[m.end():end]


def classify_mono(body):
    if field(body, "m_UiScaleMode") is not None:
        return "scaler"
    if field(body, "m_fontSize") is not None or field(body, "m_enableAutoSizing") is not None:
        return "tmp"
    if "m_OnClick:" in body and field(body, "m_Transition") is not None:
        return "button"
    if field(body, "m_Content") is not None and field(body, "m_Viewport") is not None:
        return "scroll"
    if field(body, "m_CellSize") is not None:
        return "grid"
    if field(body, "m_ChildControlWidth") is not None and field(body, "m_Spacing") is not None:
        return "linear"
    if field(body, "m_Sprite") is not None and field(body, "m_PreserveAspect") is not None:
        return "image"
    return "other"


def build_guid_map(project, wanted):
    """Resolve only the wanted guids to script names; stop as soon as all are found."""
    out = {}
    wanted = set(wanted)
    for sub in ("Assets", "Packages", os.path.join("Library", "PackageCache")):
        for base, _, files in os.walk(os.path.join(project, sub)):
            for name in files:
                if not name.endswith(".cs.meta"):
                    continue
                try:
                    with open(os.path.join(base, name), encoding="utf-8", errors="replace") as f:
                        m = re.search(r"guid:\s*([0-9a-f]{32})", f.read(400))
                except OSError:
                    continue
                if m and m.group(1) in wanted:
                    out[m.group(1)] = name[:-len(".cs.meta")]
                    if len(out) == len(wanted):
                        return out
    return out


def prefab_files(project, root):
    for base, _, files in os.walk(os.path.join(project, root)):
        for name in files:
            if name.endswith(".prefab"):
                yield os.path.join(base, name)


def hist(counter, top=None):
    return {str(k): v for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0])))[:top]}


def mine(project, root="Assets", resolve=True):
    canvas_modes, sort_orders, scalers = Counter(), [], []
    btn_sizes, co_guids = Counter(), Counter()
    btn_total = 0
    tmp = {"total": 0, "auto": 0, "raycast_off": 0, "min": Counter(), "max": Counter()}
    img = {"total": 0, "raycast_off": 0}
    scroll_insets = []
    linear_spacing, grids = Counter(), []
    prefixes = Counter()
    n = 0
    for path in prefab_files(project, root):
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        if "\n--- !u!224 " not in text:
            continue  # not a UI prefab (no RectTransform)
        n += 1
        gos, rects, comps = {}, {}, defaultdict(list)
        for cls, fid, body in split_docs(text):
            if cls == 1:
                gos[fid] = (field(body, "m_Name") or "").strip()
            elif cls == 224:
                rects[ref(body, "m_GameObject")] = body
            elif cls == 223:
                canvas_modes[field(body, "m_RenderMode")] += 1
                so = field(body, "m_SortingOrder")
                if so is not None:
                    sort_orders.append(num(so))
            elif cls == 114:
                comps[ref(body, "m_GameObject")].append((classify_mono(body), guid_of(body), body))
        for go_id, name in gos.items():
            if "_" in name:
                prefixes[name.split("_", 1)[0]] += 1
            kinds = comps.get(go_id, [])
            rect = rects.get(go_id)
            for kind, guid, body in kinds:
                if kind == "scaler":
                    res = vec(body, "m_ReferenceResolution")
                    scalers.append({"reference_resolution": list(res) if res else None,
                                    "match_mode": num(field(body, "m_ScreenMatchMode") or 0)})
                elif kind == "tmp":
                    tmp["total"] += 1
                    tmp["auto"] += field(body, "m_enableAutoSizing") == "1"
                    tmp["raycast_off"] += field(body, "m_RaycastTarget") == "0"
                    if field(body, "m_fontSizeMin") is not None:
                        tmp["min"][num(field(body, "m_fontSizeMin"))] += 1
                    if field(body, "m_fontSizeMax") is not None:
                        tmp["max"][num(field(body, "m_fontSizeMax"))] += 1
                elif kind == "image":
                    img["total"] += 1
                    img["raycast_off"] += field(body, "m_RaycastTarget") == "0"
                elif kind == "scroll" and rect:
                    amin, amax, sd = vec(rect, "m_AnchorMin"), vec(rect, "m_AnchorMax"), vec(rect, "m_SizeDelta")
                    if amin and amax and sd:
                        h = -sd[0] if amin[0] != amax[0] else 0
                        v = -sd[1] if amin[1] != amax[1] else 0
                        scroll_insets.append({"name": name, "horizontal_total": h, "vertical_total": v})
                elif kind == "linear":
                    linear_spacing[num(field(body, "m_Spacing"))] += 1
                elif kind == "grid":
                    grids.append({"cell": list(vec(body, "m_CellSize")), "spacing": list(vec(body, "m_Spacing") or (0, 0))})
            if any(k == "button" for k, _, _ in kinds):
                btn_total += 1
                if rect:
                    amin, amax, sd = vec(rect, "m_AnchorMin"), vec(rect, "m_AnchorMax"), vec(rect, "m_SizeDelta")
                    if amin and amax and sd and amin == amax and sd != (0, 0):
                        btn_sizes[(sd[0], sd[1])] += 1
                for kind, guid, _ in kinds:
                    if kind == "other" and guid:
                        co_guids[guid] += 1
    top = co_guids.most_common(15)
    names = build_guid_map(project, [g for g, _ in top]) if resolve and top else {}
    co_scripts = [{"script": names.get(g, g), "buttons_with": c} for g, c in top]
    ratio = lambda a, b: round(a / b, 3) if b else 0.0
    return {
        "prefabs_scanned": n,
        "canvas": {"render_modes": hist(canvas_modes), "sort_orders": sorted(sort_orders), "scalers": scalers},
        "buttons": {"total": btn_total,
                    "sizes": [{"size": list(s), "count": c} for s, c in sorted(btn_sizes.items(), key=lambda kv: (-kv[1], kv[0]))],
                    "co_scripts": co_scripts},
        "text": {"total": tmp["total"], "autosize_ratio": ratio(tmp["auto"], tmp["total"]),
                 "raycast_off_ratio": ratio(tmp["raycast_off"], tmp["total"]),
                 "min_sizes": hist(tmp["min"]), "max_sizes": hist(tmp["max"], 8)},
        "images": {"total": img["total"], "raycast_off_ratio": ratio(img["raycast_off"], img["total"])},
        "scroll": {"total": len(scroll_insets), "insets": scroll_insets},
        "layout": {"linear_spacing": hist(linear_spacing), "grids": grids},
        "naming": {"prefixes": hist(prefixes, 25)},
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    opts = {"--root": "Assets", "--out": None}
    flags = {"--no-resolve"}
    pos, i = [], 0
    while i < len(argv):
        if argv[i] in opts and i + 1 < len(argv):
            opts[argv[i]] = argv[i + 1]
            i += 2
        else:
            if argv[i] not in flags:
                pos.append(argv[i])
            i += 1
    if not pos or not os.path.isdir(os.path.join(pos[0], "Assets")):
        print("usage: ui_miner.py <unity-project> [--root Assets/_Game] [--out tokens.json] [--no-resolve]", file=sys.stderr)
        return 2
    tokens = mine(pos[0], opts["--root"], resolve="--no-resolve" not in argv)
    text = json.dumps(tokens, indent=2)
    if opts["--out"]:
        with open(opts["--out"], "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote %s (%d prefabs)" % (opts["--out"], tokens["prefabs_scanned"]))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
