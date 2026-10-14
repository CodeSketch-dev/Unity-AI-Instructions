"""Lint a UI screen spec and convert it to builder JSON (stdlib only).

Usage:
  py -I ui_spec_tool.py lint  <spec.yaml|json>
  py -I ui_spec_tool.py build <spec.yaml|json> --canvas 1920x1080 [--out ui-spec.json]
  py -I ui_spec_tool.py rects <spec.yaml|json> [--out rects.json]   (absolute rects for wireframes/validators)

The spec follows report 21 section 1.4 (layout contract in reference-canvas pixels).
`build` converts positions/sizes to Unity RectTransform values for the game canvas and
writes JSON that the Editor builder (assets/UiSpecBuilder.cs.txt) reads. YAML support is
a deliberate subset: block maps/lists, flow maps/lists, scalars, comments.
"""
import json
import math
import re
import sys
from collections import namedtuple

Finding = namedtuple("Finding", "code where message")

ANCHORS = {
    "top-left": ((0, 1), (0, 1)), "top-center": ((0.5, 1), (0.5, 1)), "top-right": ((1, 1), (1, 1)),
    "mid-left": ((0, 0.5), (0, 0.5)), "center": ((0.5, 0.5), (0.5, 0.5)), "mid-right": ((1, 0.5), (1, 0.5)),
    "bottom-left": ((0, 0), (0, 0)), "bottom-center": ((0.5, 0), (0.5, 0)), "bottom-right": ((1, 0), (1, 0)),
    "stretch": ((0, 0), (1, 1)), "stretch-top": ((0, 0), (1, 1)), "stretch-bottom": ((0, 0), (1, 1)),
    "stretch-left": ((0, 0), (1, 1)), "stretch-right": ((0, 0), (1, 1)),
}


# ---------------------------------------------------------------- YAML subset
def _scalar(tok):
    t = tok.strip()
    if t in ("", "~", "null", "Null", "NULL"):
        return None
    if t in ("true", "True"):
        return True
    if t in ("false", "False"):
        return False
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        return t[1:-1]
    try:
        return int(t)
    except ValueError:
        pass
    try:
        return float(t)
    except ValueError:
        return t


def _split_top(s, sep=","):
    parts, depth, cur, quote = [], 0, [], None
    for ch in s:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch in "[{":
            depth += 1
            cur.append(ch)
        elif ch in "]}":
            depth -= 1
            cur.append(ch)
        elif ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def _find_colon(s):
    depth, quote = 0, None
    for i, ch in enumerate(s):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == ":" and depth == 0 and (i + 1 == len(s) or s[i + 1] == " "):
            return i
    return -1


def _flow(s):
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        out = {}
        for part in _split_top(s[1:-1]):
            i = _find_colon(part)
            out[part[:i].strip()] = _flow(part[i + 1:]) if i >= 0 else None
        return out
    if s.startswith("[") and s.endswith("]"):
        return [_flow(p) for p in _split_top(s[1:-1])]
    return _scalar(s)


def _strip_comment(line):
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] == " "):
            return line[:i]
    return line


def _block(lines, i, indent):
    """Parse a block starting at lines[i] with the given indent. Returns (value, next_i)."""
    if lines[i][1].startswith("- ") or lines[i][1] == "-":
        out = []
        while i < len(lines) and lines[i][0] == indent and (lines[i][1].startswith("- ") or lines[i][1] == "-"):
            rest = lines[i][1][1:].strip()
            if not rest:
                i += 1
                v, i = _block(lines, i, lines[i][0])
                out.append(v)
            elif _find_colon(rest) >= 0 and not rest.startswith(("{", "[")):
                # "- key: value" starts an inline mapping continuing on deeper lines
                sub = [(indent + 2, rest)]
                j = i + 1
                while j < len(lines) and lines[j][0] > indent:
                    sub.append(lines[j])
                    j += 1
                v, _ = _block(sub, 0, indent + 2)
                out.append(v)
                i = j
            else:
                out.append(_flow(rest))
                i += 1
        return out, i
    out = {}
    while i < len(lines) and lines[i][0] == indent:
        text = lines[i][1]
        c = _find_colon(text)
        key, rest = text[:c].strip(), text[c + 1:].strip()
        if rest:
            out[key] = _flow(rest)
            i += 1
        else:
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                out[key], i = _block(lines, i, lines[i][0])
            elif i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
                out[key], i = _block(lines, i, indent)
            else:
                out[key] = None
    return out, i


def loads(text):
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}") and '"' in stripped[:3] + stripped:
        try:
            return json.loads(stripped)
        except ValueError:
            pass
    lines = []
    for raw in text.splitlines():
        line = _strip_comment(raw).rstrip()
        if line.strip() and not line.strip().startswith("---"):
            lines.append((len(line) - len(line.lstrip(" ")), line.strip()))
    if not lines:
        return {}
    value, _ = _block(lines, 0, lines[0][0])
    return value


# ---------------------------------------------------------------------- lint
def lint(spec):
    out = []
    for key in ("id", "type", "reference_canvas", "elements"):
        if key not in spec:
            out.append(Finding("missing-key", key, "top-level key '%s' is required" % key))
    rc = spec.get("reference_canvas") or {}
    if "reference_canvas" in spec and not (isinstance(rc.get("w"), (int, float)) and isinstance(rc.get("h"), (int, float)) and rc["w"] > 0 and rc["h"] > 0):
        out.append(Finding("bad-canvas", "reference_canvas", "w and h must be positive numbers"))
    elements = spec.get("elements") or []
    names, numbers = {}, {}
    for idx, e in enumerate(elements):
        where = e.get("name") or "elements[%d]" % idx
        name, n = e.get("name"), e.get("n")
        if not name:
            out.append(Finding("missing-name", where, "element has no name"))
        elif name in names:
            out.append(Finding("duplicate-name", where, "name used twice (names are builder keys)"))
        names[name] = e
        if n is not None:
            if n in numbers:
                out.append(Finding("duplicate-number", where, "n=%s used twice" % n))
            numbers[n] = e
        anchor = e.get("anchor")
        if anchor not in ANCHORS:
            out.append(Finding("bad-anchor", where, "anchor %r not in %s" % (anchor, ", ".join(sorted(ANCHORS)))))
            continue
        if anchor.startswith("stretch"):
            if not isinstance(e.get("rect"), dict):
                out.append(Finding("missing-rect", where, "stretch anchors need rect {top,bottom,left,right}"))
        else:
            if not (isinstance(e.get("pos"), list) and len(e["pos"]) == 2):
                out.append(Finding("missing-pos", where, "fixed anchors need pos [x, y]"))
            if not (isinstance(e.get("size"), list) and len(e["size"]) == 2):
                out.append(Finding("missing-size", where, "fixed anchors need size [w, h]"))
        t = e.get("text")
        if isinstance(t, dict) and not t.get("key"):
            out.append(Finding("text-no-key", where, "text needs a localization key"))
    if not any(f.code in ("bad-anchor", "missing-pos", "missing-size", "missing-rect", "bad-canvas", "missing-key") for f in out):
        out.extend(_geometry_findings(spec))
    for e in elements:
        for child in e.get("children") or []:
            if child not in names:
                out.append(Finding("unknown-child", e.get("name", "?"), "child %r is not an element" % child))
    return out


def element_rects(spec):
    """Absolute rect (x0, y0, x1, y1) of every element in reference-canvas px, origin bottom-left, y up."""
    rc = spec["reference_canvas"]
    w, h = rc["w"], rc["h"]
    out = {}
    for e in spec.get("elements") or []:
        amin, amax = ANCHORS[e["anchor"]]
        if e["anchor"].startswith("stretch"):
            r = e.get("rect") or {}
            out[e["name"]] = (r.get("left", 0), r.get("bottom", 0), w - r.get("right", 0), h - r.get("top", 0))
        else:
            cx, cy = amin[0] * w + e["pos"][0], amin[1] * h + e["pos"][1]
            sw, sh = e["size"]
            out[e["name"]] = (cx - sw / 2, cy - sh / 2, cx + sw / 2, cy + sh / 2)
    return out


def _geometry_findings(spec):
    out = []
    rects = element_rects(spec)
    w, h = spec["reference_canvas"]["w"], spec["reference_canvas"]["h"]
    leaves = [e for e in spec.get("elements") or [] if not e.get("container") and not e.get("state") and e.get("name") in rects]
    for e in leaves:
        r = rects[e["name"]]
        if r[0] < -1 or r[1] < -1 or r[2] > w + 1 or r[3] > h + 1:
            out.append(Finding("offscreen", e["name"], "rect %s leaves the %dx%d canvas" % (tuple(round(v) for v in r), w, h)))
    for i, a in enumerate(leaves):
        ra = rects[a["name"]]
        for b in leaves[i + 1:]:
            rb = rects[b["name"]]
            ow = min(ra[2] - 4, rb[2] - 4) - max(ra[0] + 4, rb[0] + 4)
            oh = min(ra[3] - 4, rb[3] - 4) - max(ra[1] + 4, rb[1] + 4)
            if ow > 0 and oh > 0:
                out.append(Finding("overlap", a["name"], "overlaps %s (leaf elements must not overlap; mark containers with container: true)" % b["name"]))
    return out


# ------------------------------------------------------------------- anchors
def scale_factor(capture, game, match):
    """Capture px -> game reference px using the CanvasScaler log blend (match 0 = width, 1 = height)."""
    cw, ch = capture
    gw, gh = game
    return (gw / cw) ** (1 - match) * (gh / ch) ** match


def _r(v):
    v = round(v, 3)
    return int(v) if v == int(v) else v


def to_rect(e, scale):
    amin, amax = ANCHORS[e["anchor"]]
    out = {"anchorMin": list(amin), "anchorMax": list(amax)}
    if e["anchor"].startswith("stretch"):
        r = e.get("rect") or {}
        out["offsetMin"] = [_r(r.get("left", 0) * scale), _r(r.get("bottom", 0) * scale)]
        out["offsetMax"] = [_r(-r.get("right", 0) * scale), _r(-r.get("top", 0) * scale)]
        out["pivot"] = [0.5, 0.5]
        return out
    out["pivot"] = [0.5, 0.5]
    out["anchoredPosition"] = [_r(e["pos"][0] * scale), _r(e["pos"][1] * scale)]
    out["sizeDelta"] = [_r(e["size"][0] * scale), _r(e["size"][1] * scale)]
    return out


def build_json(spec, game_canvas):
    rc = spec["reference_canvas"]
    scale = scale_factor((rc["w"], rc["h"]), game_canvas, rc.get("match", 0.5))
    elements = []
    for e in spec["elements"]:
        item = {k: v for k, v in e.items() if k not in ("pos", "size", "rect", "anchor")}
        item["anchor"] = e["anchor"]
        item["rect"] = to_rect(e, scale)
        elements.append(item)
    return {"id": spec["id"], "type": spec["type"], "kind": spec.get("kind"), "scale": round(scale, 6),
            "game_canvas": list(game_canvas), "states": spec.get("states", []), "elements": elements}


# ----------------------------------------------------------------------- CLI
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2 or argv[0] not in ("lint", "build", "rects"):
        print(__doc__, file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        spec = loads(f.read())
    findings = lint(spec)
    for f in findings:
        print("ERROR %s [%s] %s" % (f.code, f.where, f.message))
    if findings:
        print("%d problem(s)" % len(findings))
        return 1
    if argv[0] == "lint":
        print("ok: %d elements" % len(spec["elements"]))
        return 0
    if argv[0] == "rects":
        rects = element_rects(spec)
        rc = spec["reference_canvas"]
        data = {"canvas": [rc["w"], rc["h"]], "id": spec["id"],
                "elements": [{"n": e.get("n"), "name": e["name"], "container": bool(e.get("container")), "state": e.get("state"),
                              "rect": [round(v, 1) for v in rects[e["name"]]]} for e in spec["elements"]]}
        text = json.dumps(data, indent=1)
        if "--out" in argv:
            with open(argv[argv.index("--out") + 1], "w", encoding="utf-8") as f:
                f.write(text)
        else:
            print(text)
        return 0
    canvas = (1920, 1080)
    out = None
    if "--canvas" in argv:
        w, h = argv[argv.index("--canvas") + 1].lower().split("x")
        canvas = (int(w), int(h))
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    text = json.dumps(build_json(spec, canvas), indent=2)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote %s" % out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
