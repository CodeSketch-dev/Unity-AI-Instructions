"""Static UI validator for Unity prefabs (read-only, text YAML, stdlib only).

Usage: py -I ui_validator.py <file.prefab> [--hud] [--ref 1920x1080] [--exceptions qa/ui-exceptions.json]
                              [--banner 200] [--margin 24]
                              [--kind popup|page|hud|canvas|none] [--dump-rects texts.json]
                              [--project <unity-project>] (enables UI-9SLICE, UI-MISSING guid checks) [--reference ref.prefab] (enables UI-REF-MATCH)
Resolves every RectTransform to a rect in canvas units (CanvasScaler Expand) at several
aspect ratios and applies numeric rules. FAIL (exit 1) rules: UI-OVERLAP, UI-SAFE, UI-BANNER (--hud),
UI-CHILD-EQ-PARENT, UI-RAYCAST. WARN rule: UI-TOUCH (needs a reasoned exception to silence).
Elements under Layout Groups / ContentSizeFitter are reported as UI-UNKNOWN and skipped (their size
needs the runtime validator). Rule ids follow report 17 section 5.3.
"""
import json
import os
import re
import sys
from collections import namedtuple

Finding = namedtuple("Finding", "level rule path message")
Node = namedtuple("Node", "id name path father is_canvas amin amax pos size pivot interactive graphic raycast is_text unknown active handler sprite img_type text font_size font_min autosize scale script_guids overflow_mode")

DOC_RE = re.compile(r"^--- !u!(\d+) &(-?\d+)", re.M)
VEC_RE = re.compile(r"\{x:\s*(-?[\d.eE+-]+),\s*y:\s*(-?[\d.eE+-]+)")
EXEMPT = ("background", "backdrop", "dim", "overlay", "blocker", "block", "bg", "fill", "viewport", "mask")
ASPECTS = [(1920, 1080), (2400, 1080), (1600, 1200)]
# notch + gesture bar simulation (pixels) for the wide aspect, per report 17: left/right 132, bottom 63
SAFE_PX = {(2400, 1080): (132, 0, 132, 63)}


def _field(body, key):
    m = re.search(r"^\s+%s:\s*(.*?)\s*$" % re.escape(key), body, re.M)
    return m.group(1) if m else None


def _vec(body, key, default=(0.0, 0.0)):
    v = _field(body, key)
    m = VEC_RE.search(v) if v else None
    return (float(m.group(1)), float(m.group(2))) if m else default


def _ref(body, key):
    m = re.search(r"fileID:\s*(-?\d+)", _field(body, key) or "")
    return int(m.group(1)) if m else 0


def nodes_from_prefab(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    marks = list(DOC_RE.finditer(text))
    gos, rects, rect_go, comps, canvases, inactive = {}, {}, {}, {}, set(), set()
    for i, m in enumerate(marks):
        cls, fid = int(m.group(1)), int(m.group(2))
        body = text[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        if cls == 1:
            gos[fid] = (_field(body, "m_Name") or "").strip()
            if _field(body, "m_IsActive") == "0":
                inactive.add(fid)
        elif cls == 224:
            g = _ref(body, "m_GameObject")
            rects[g] = body
            rect_go[fid] = g
        elif cls == 223:
            canvases.add(_ref(body, "m_GameObject"))
        elif cls == 114:
            comps.setdefault(_ref(body, "m_GameObject"), []).append(body)
    fathers = {g: rect_go.get(_ref(b, "m_Father")) for g, b in rects.items()}

    def path_of(g):
        names = []
        while g in gos:
            names.append(gos[g])
            g = fathers.get(g)
        return "/".join(reversed(names))

    layout_go = set()
    for g, bodies in comps.items():
        for b in bodies:
            if any(_field(b, k) is not None for k in ("m_CellSize", "m_ChildControlWidth", "m_HorizontalFit", "m_VerticalFit")):
                layout_go.add(g)
    out = []
    for g, name in gos.items():
        if g not in rects:
            continue
        b = rects[g]
        interactive = graphic = is_text = handler = False
        raycast = sprite = img_type = text_value = font_size = font_min = None
        autosize = False
        script_guids = []
        overflow_mode = None
        for cb in comps.get(g, []):
            if _field(cb, "m_Script") is not None:
                sg = re.search(r"guid:\s*([0-9a-f]{32})", _field(cb, "m_Script"))
                script_guids.append(sg.group(1) if sg else None)
            if "m_OnClick:" in cb and _field(cb, "m_Transition") is not None:
                interactive = True
            elif (_field(cb, "m_Content") is not None and _field(cb, "m_Viewport") is not None)                     or _field(cb, "m_HandleRect") is not None or _field(cb, "m_IsOn") is not None:
                handler = True  # scroll rect / scrollbar / slider / toggle: its graphics need raycast
            elif _field(cb, "m_fontSize") is not None or _field(cb, "m_enableAutoSizing") is not None:
                graphic = is_text = True
                raycast = _field(cb, "m_RaycastTarget") != "0"
                text_value = (_field(cb, "m_text") or "").strip("'\"")
                font_size = _num(_field(cb, "m_fontSize"))
                font_min = _num(_field(cb, "m_fontSizeMin"))
                autosize = _field(cb, "m_enableAutoSizing") == "1"
                overflow_mode = _num(_field(cb, "m_overflowMode"))
            elif _field(cb, "m_Sprite") is not None and _field(cb, "m_PreserveAspect") is not None:
                graphic = True
                raycast = _field(cb, "m_RaycastTarget") != "0"
                gm = re.search(r"guid:\s*([0-9a-f]{32})", _field(cb, "m_Sprite") or "")
                sprite = gm.group(1) if gm else None
                img_type = _num(_field(cb, "m_Type"))
        parent = fathers.get(g)
        chain, cur, active = g, g, True
        while cur in gos:
            if cur in inactive:
                active = False
            cur = fathers.get(cur)
        out.append(Node(g, name, path_of(g), parent, g in canvases, _vec(b, "m_AnchorMin"), _vec(b, "m_AnchorMax", (1.0, 1.0)),
                        _vec(b, "m_AnchoredPosition"), _vec(b, "m_SizeDelta"), _vec(b, "m_Pivot", (0.5, 0.5)),
                        interactive, graphic, raycast, is_text, parent in layout_go, active, handler,
                        sprite, img_type, text_value, font_size, font_min, autosize, _scale_x(b), script_guids, overflow_mode))
    return out


def _scale_x(rect_body):
    m = re.search(r"m_LocalScale:\s*\{x:\s*(-?[\d.eE+-]+)", rect_body)
    return float(m.group(1)) if m else 1.0


BUILTIN_GUIDS = {"0000000000000000f000000000000000", "0000000000000000e000000000000000"}


def project_guids(project):
    """All asset guids known to the project (Assets, Packages, Library/PackageCache metas)."""
    out = set()
    for sub in ("Assets", "Packages", os.path.join("Library", "PackageCache")):
        for base, _, files in os.walk(os.path.join(project, sub)):
            for name in files:
                if name.endswith(".meta"):
                    try:
                        with open(os.path.join(base, name), encoding="utf-8", errors="replace") as f:
                            m = re.search(r"guid:\s*([0-9a-f]{32})", f.read(400))
                    except OSError:
                        continue
                    if m:
                        out.add(m.group(1))
    return out


def struct_findings(nodes, kind="popup"):
    """UI-STRUCT for popup/page/hud prefabs: exactly one empty stretch child named Root under the prefab root."""
    by_id = {n.id: n for n in nodes}
    roots = [n for n in nodes if n.father not in by_id and not n.is_canvas]
    out = []
    for root in roots[:1]:
        kids = [n for n in nodes if n.father == root.id]
        names = [k.name for k in kids]
        if names != ["Root"]:
            out.append(Finding("FAIL", "UI-STRUCT", root.path, "%s prefab needs exactly one child named Root, found %s" % (kind, names)))
            continue
        r = kids[0]
        if tuple(r.amin) != (0.0, 0.0) or tuple(r.amax) != (1.0, 1.0) or tuple(r.pos) != (0.0, 0.0) or tuple(r.size) != (0.0, 0.0):
            out.append(Finding("FAIL", "UI-STRUCT", r.path, "Root must stretch fully with zero offsets"))
        if r.graphic:
            out.append(Finding("FAIL", "UI-STRUCT", r.path, "Root must not carry a Graphic"))
    return out


def canvas_findings(path):
    """UI-STRUCT for a canvas prefab: Overlay render mode, Scale With Screen Size, match mode Expand."""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    marks = list(DOC_RE.finditer(text))
    out = []
    for i, m in enumerate(marks):
        body = text[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        if int(m.group(1)) == 223 and _field(body, "m_RenderMode") not in (None, "0"):
            out.append(Finding("FAIL", "UI-STRUCT", os.path.basename(path), "Canvas render mode must be Screen Space - Overlay"))
        if int(m.group(1)) == 114 and _field(body, "m_UiScaleMode") is not None:
            if _field(body, "m_UiScaleMode") != "1":
                out.append(Finding("FAIL", "UI-STRUCT", os.path.basename(path), "CanvasScaler must use Scale With Screen Size"))
            if _field(body, "m_ScreenMatchMode") not in (None, "1"):
                out.append(Finding("FAIL", "UI-STRUCT", os.path.basename(path), "CanvasScaler match mode must be Expand"))
    return out


def text_rects(nodes, canvas):
    rects = resolve_rects(nodes, canvas)
    return [{"path": n.path, "rect": [round(v) for v in rects[n.id]], "font_size": n.font_size}
            for n in nodes if n.is_text and not n.unknown]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def sprite_borders(project):
    """guid -> (left, bottom, right, top) for textures whose importer has a non-zero spriteBorder."""
    out = {}
    for base, _, files in os.walk(os.path.join(project, "Assets")):
        for name in files:
            if not name.endswith(".meta") or name.endswith(".cs.meta"):
                continue
            try:
                with open(os.path.join(base, name), encoding="utf-8", errors="replace") as f:
                    t = f.read()
            except OSError:
                continue
            if "spriteBorder" not in t:
                continue
            g = re.search(r"guid:\s*([0-9a-f]{32})", t)
            v = re.search(r"spriteBorder:\s*\{x:\s*([\d.]+),\s*y:\s*([\d.]+),\s*z:\s*([\d.]+),\s*w:\s*([\d.]+)", t)
            if g and v:
                ppu = re.search(r"spritePixelsToUnits:\s*([\d.]+)", t)
                k = 100.0 / float(ppu.group(1)) if ppu and float(ppu.group(1)) else 1.0  # canvas reference PPU 100
                b = tuple(float(x) * k for x in v.groups())
                if any(b):
                    out[g.group(1)] = b
    return out


def canvas_size(ref, screen):
    scale = min(screen[0] / ref[0], screen[1] / ref[1])
    return (screen[0] / scale, screen[1] / scale)


def resolve_rects(nodes, canvas):
    by_id = {n.id: n for n in nodes}
    cache = {}

    def rect_of(n):
        if n.id in cache:
            return cache[n.id]
        if n.is_canvas or n.father not in by_id:
            parent = (0.0, 0.0, canvas[0], canvas[1])
            if n.is_canvas:
                cache[n.id] = parent
                return parent
        else:
            parent = rect_of(by_id[n.father])
        px, py, pw, ph = parent[0], parent[1], parent[2] - parent[0], parent[3] - parent[1]
        amin = (px + n.amin[0] * pw, py + n.amin[1] * ph)
        span = ((n.amax[0] - n.amin[0]) * pw, (n.amax[1] - n.amin[1]) * ph)
        size = (span[0] + n.size[0], span[1] + n.size[1])
        pivot_pos = (amin[0] + span[0] * n.pivot[0] + n.pos[0], amin[1] + span[1] * n.pivot[1] + n.pos[1])
        x0, y0 = pivot_pos[0] - size[0] * n.pivot[0], pivot_pos[1] - size[1] * n.pivot[1]
        r = (x0, y0, x0 + size[0], y0 + size[1])
        cache[n.id] = r
        return r

    return {n.id: rect_of(n) for n in nodes}


def _exempt(name):
    low = name.lower()
    return any(k in low for k in EXEMPT)


def _ancestors(n, by_id):
    out = set()
    while n.father in by_id:
        out.add(n.father)
        n = by_id[n.father]
    return out


def _inter(a, b, shrink=4):
    w = min(a[2] - shrink, b[2] - shrink) - max(a[0] + shrink, b[0] + shrink)
    h = min(a[3] - shrink, b[3] - shrink) - max(a[1] + shrink, b[1] + shrink)
    return w > 0 and h > 0


def _excused(exceptions, rule, path):
    return any(e.get("rule") == rule and e.get("path") == path and (e.get("reason") or "").strip() for e in exceptions or [])


def validate(nodes, canvas=(1920.0, 1080.0), safe_inset=(0, 0, 0, 0), edge_margin=24, hud=False, banner=200,
             touch_min=88, exceptions=None, include_inactive=False, sprite_borders=None, project_guids=None):
    rects = resolve_rects(nodes, canvas)
    by_id = {n.id: n for n in nodes}
    out = []

    def add(level, rule, node, msg):
        if not _excused(exceptions, rule, node.path):
            out.append(Finding(level, rule, node.path, msg))

    safe = (safe_inset[0] + edge_margin, safe_inset[3] + edge_margin,
            canvas[0] - safe_inset[2] - edge_margin, canvas[1] - safe_inset[1] - edge_margin)
    known = [n for n in nodes if not n.unknown and not n.is_canvas]
    for n in nodes:
        if n.unknown:
            add("INFO", "UI-UNKNOWN", n, "under a layout group; size needs the runtime validator")
    has_interactive_child = set()
    for n in nodes:
        if n.interactive or n.handler:
            has_interactive_child |= _ancestors(n, by_id)
    inter = [n for n in known if n.interactive and (n.active or include_inactive)]
    for i, a in enumerate(inter):
        for b in inter[i + 1:]:
            if a.id in _ancestors(b, by_id) or b.id in _ancestors(a, by_id):
                continue
            if _inter(rects[a.id], rects[b.id]):
                add("FAIL", "UI-OVERLAP", a, "overlaps %s" % b.path)
    for n in known:
        r = rects[n.id]
        if r[2] - r[0] <= 0 or r[3] - r[1] <= 0:
            continue                                   # degenerate rect (stretched negative / zero): needs runtime layout
        live = n.active or include_inactive            # inactive state panels are checked only on request
        if live and (n.interactive or n.is_text) and not _exempt(n.name):
            if r[0] < safe[0] or r[1] < safe[1] or r[2] > safe[2] or r[3] > safe[3]:
                add("FAIL", "UI-SAFE", n, "rect %s leaves the safe area %s" % (tuple(round(v) for v in r), tuple(round(v) for v in safe)))
            if hud and r[1] < safe[1] - edge_margin + banner:
                add("FAIL", "UI-BANNER", n, "bottom %.0f is below the %d px banner clearance" % (r[1], banner))
        if live and n.interactive and (r[2] - r[0] < touch_min or r[3] - r[1] < touch_min):
            add("WARN", "UI-TOUCH", n, "touch target %.0fx%.0f < %d" % (r[2] - r[0], r[3] - r[1], touch_min))
        parent = by_id.get(n.father)
        if parent and parent.graphic and not parent.is_text and n.graphic and not n.is_text and n.name != "Root" and not _exempt(n.name):
            pr = rects[parent.id]
            if all(abs(a - b) <= 1 for a, b in zip(r, pr)):
                add("FAIL", "UI-CHILD-EQ-PARENT", n, "same rect as parent %s (double frame / stretch bug?)" % parent.path)
        if live and n.graphic and n.raycast and not n.interactive and not _exempt(n.name):
            chain = _ancestors(n, by_id)
            if not any(by_id[a].interactive or by_id[a].handler for a in chain) and not n.handler and n.id not in has_interactive_child:
                add("FAIL", "UI-RAYCAST", n, "non-interactive graphic has Raycast Target on")
        border = (sprite_borders or {}).get(n.sprite)
        if border:
            if n.img_type != 1:
                add("FAIL", "UI-9SLICE", n, "sprite has a 9-slice border but Image Type is not Sliced")
            elif (r[2] - r[0]) < border[0] + border[2] or (r[3] - r[1]) < border[1] + border[3]:
                add("WARN", "UI-9SLICE", n, "rect %.0fx%.0f is smaller than the border sum (Unity shrinks the borders; check the look)" % (r[2] - r[0], r[3] - r[1]))
        if live and n.is_text and n.text and not (n.overflow_mode == 0 and not n.autosize):
            font = n.font_min if n.autosize and n.font_min else n.font_size
            lines = n.text.replace("\\n", "\n").split("\n")
            if font:
                w_est, h_est = max(len(x) for x in lines) * font * 0.55, len(lines) * font * 1.2
                if w_est > (r[2] - r[0]) or h_est > (r[3] - r[1]):
                    add("WARN", "UI-OVERFLOW", n, "estimated %.0fx%.0f text at size %.0f vs rect %.0fx%.0f (heuristic; runtime validator is authoritative)"
                        % (w_est, h_est, font, r[2] - r[0], r[3] - r[1]))
        if n.is_text and n.autosize and n.font_min is not None and n.font_min < 18:
            add("WARN", "UI-FONT-MIN", n, "autosize min font %.0f < 18 (readability on phones)" % n.font_min)
        if n.is_text:
            sign, cur = 1, n
            while cur is not None:
                sign *= -1 if cur.scale < 0 else 1
                cur = by_id.get(cur.father)
            if sign < 0:
                add("FAIL", "UI-MIRROR", n, "text is mirrored by a negative X scale on it or an ancestor")
        if live and hud and (n.interactive or n.is_text) and not _exempt(n.name):
            cx0, cx1 = canvas[0] * 0.3, canvas[0] * 0.7
            cy0, cy1 = canvas[1] * 0.3, canvas[1] * 0.7
            if r[0] < cx1 and r[2] > cx0 and r[1] < cy1 and r[3] > cy0:
                add("WARN", "UI-CENTER-FREE", n, "HUD element inside the central 40% x 40% of the view")
    for n in nodes:                                   # script/asset references (all nodes, also under layout groups)
        if None in n.script_guids:
            add("FAIL", "UI-MISSING", n, "component with a missing script (m_Script fileID 0)")
        if project_guids is not None:
            for g in n.script_guids:
                if g and g not in project_guids and g not in BUILTIN_GUIDS:
                    add("FAIL", "UI-MISSING", n, "script guid %s not found in the project" % g[:8])
            if n.sprite and n.sprite not in project_guids and n.sprite not in BUILTIN_GUIDS:
                add("FAIL", "UI-MISSING", n, "sprite guid %s not found in the project" % n.sprite[:8])
    groups = {}
    for n in known:
        if n.interactive and n.active and not _exempt(n.name):
            groups.setdefault(n.father, []).append(n)
    for father, members in groups.items():
        if len(members) < 3:
            continue
        xs = [rects[m.id] for m in members]
        horizontal = (max(r[2] for r in xs) - min(r[0] for r in xs)) >= (max(r[3] for r in xs) - min(r[1] for r in xs))
        order = sorted(range(len(members)), key=lambda i: xs[i][0] if horizontal else xs[i][1])
        gaps = [(xs[order[i + 1]][0] - xs[order[i]][2]) if horizontal else (xs[order[i + 1]][1] - xs[order[i]][3]) for i in range(len(order) - 1)]
        if min(gaps) >= 0:
            mean = sum(gaps) / len(gaps)
            if max(gaps) - min(gaps) > max(8.0, 0.15 * mean):
                add("WARN", "UI-SPACING", members[0], "uneven gaps %s between %d siblings (difference > max(8 px, 15%%))" % ([round(g) for g in gaps], len(members)))
    for p in known:                                    # icon + label pairs
        kids = [k for k in known if k.father == p.id]
        icons = [k for k in kids if k.graphic and not k.is_text and "icon" in k.name.lower()]
        labels = [k for k in kids if k.is_text and k.font_size]
        if icons and labels:
            ir, tr = rects[icons[0].id], rects[labels[0].id]
            overlap = min(ir[3], tr[3]) - max(ir[1], tr[1])
            if overlap < 0.5 * min(ir[3] - ir[1], tr[3] - tr[1]):
                continue                               # stacked, not side by side: not an icon+label row
            ratio = (ir[3] - ir[1]) / (0.7 * labels[0].font_size)
            if not 1.2 <= ratio <= 2.2:
                add("WARN", "UI-ICON-LABEL", icons[0], "icon height / label cap height = %.2f (expected 1.2-2.2)" % ratio)
            if abs((ir[1] + ir[3]) / 2 - (tr[1] + tr[3]) / 2) > 3:
                add("WARN", "UI-ICON-LABEL", icons[0], "icon and label are not vertically centred together (>3 px)")
    return out


def ref_match(ref_nodes, act_nodes, canvas=(1920.0, 1080.0), tol=2.0):
    """UI-REF-MATCH: compare elements by path against a reference prefab (position/size +-tol px, sprite, font size)."""
    rr, ar = resolve_rects(ref_nodes, canvas), resolve_rects(act_nodes, canvas)
    act = {n.path: n for n in act_nodes}
    out = []
    for rn in ref_nodes:
        if rn.is_canvas or rn.unknown:
            continue
        an = act.get(rn.path)
        if an is None:
            out.append(Finding("FAIL", "UI-REF-MATCH", rn.path, "element missing from the built prefab"))
            continue
        a, r = ar[an.id], rr[rn.id]
        ac, rc = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2), ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
        if abs(ac[0] - rc[0]) > tol or abs(ac[1] - rc[1]) > tol:
            out.append(Finding("FAIL", "UI-REF-MATCH", rn.path, "centre off: ref (%.0f,%.0f) built (%.0f,%.0f)" % (rc[0], rc[1], ac[0], ac[1])))
        if abs((a[2] - a[0]) - (r[2] - r[0])) > tol or abs((a[3] - a[1]) - (r[3] - r[1])) > tol:
            out.append(Finding("FAIL", "UI-REF-MATCH", rn.path, "size off: ref %.0fx%.0f built %.0fx%.0f" % (r[2] - r[0], r[3] - r[1], a[2] - a[0], a[3] - a[1])))
        if rn.sprite and an.sprite != rn.sprite:
            out.append(Finding("FAIL", "UI-REF-MATCH", rn.path, "sprite differs from the reference"))
        if rn.is_text and rn.font_size is not None and an.font_size != rn.font_size:
            out.append(Finding("FAIL", "UI-REF-MATCH", rn.path, "font size %s != reference %s" % (an.font_size, rn.font_size)))
    return out


def validate_aspects(nodes, ref=(1920, 1080), aspects=None, **opts):
    res = {}
    for screen in aspects or ASPECTS:
        canvas = canvas_size(ref, screen)
        scale = screen[0] / canvas[0]
        l, t, r, b = SAFE_PX.get(tuple(screen), (0, 0, 0, 0))
        inset = (l / scale, t / scale, r / scale, b / scale)
        res["%dx%d" % screen] = validate(nodes, canvas=canvas, safe_inset=inset, **opts)
    return res


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    pos, i = [], 0
    opts = {"--ref": "1920x1080", "--exceptions": None, "--banner": "200", "--margin": "24", "--reference": None, "--project": None,
            "--kind": "popup", "--dump-rects": None}
    flags = set()
    while i < len(argv):
        if argv[i] in opts and i + 1 < len(argv):
            opts[argv[i]] = argv[i + 1]
            i += 2
        else:
            (flags.add(argv[i]) if argv[i].startswith("--") else pos.append(argv[i]))
            i += 1
    if not pos or not os.path.isfile(pos[0]):
        print(__doc__, file=sys.stderr)
        return 2
    rw, rh = (int(x) for x in opts["--ref"].lower().split("x"))
    exceptions = []
    if opts["--exceptions"] and os.path.isfile(opts["--exceptions"]):
        with open(opts["--exceptions"], encoding="utf-8") as f:
            exceptions = json.load(f)
    nodes = nodes_from_prefab(pos[0])
    borders = sprite_borders(opts["--project"]) if opts["--project"] else None
    guids = project_guids(opts["--project"]) if opts["--project"] else None
    results = validate_aspects(nodes, ref=(rw, rh), hud="--hud" in flags, banner=int(opts["--banner"]),
                               edge_margin=int(opts["--margin"]), exceptions=exceptions, sprite_borders=borders, project_guids=guids)
    kind = opts["--kind"]
    if kind == "canvas":
        results["structure"] = canvas_findings(pos[0])
    elif kind in ("popup", "page", "hud"):
        results["structure"] = struct_findings(nodes, kind)
    if opts["--dump-rects"]:
        with open(opts["--dump-rects"], "w", encoding="utf-8") as f:
            json.dump({"canvas": [rw, rh], "texts": text_rects(nodes, (rw, rh))}, f, indent=1)
    if opts["--reference"]:
        results["ref-match"] = ref_match(nodes_from_prefab(opts["--reference"]), nodes, canvas=(rw, rh))
    fails = 0
    for aspect, findings in results.items():
        for f in findings:
            print("%s %s @%s [%s] %s" % (f.level, f.rule, aspect, f.path, f.message))
            fails += f.level == "FAIL"
    print("%d fail(s) over %d aspect(s)" % (fails, len(results)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
