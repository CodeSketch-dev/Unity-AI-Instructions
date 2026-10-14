"""Tiny YAML-subset reader (stdlib only) shared by the pipeline tools.

Supports block maps and lists, flow maps `{a: 1}` and lists `[1, 2]`, quoted/unquoted scalars,
null/true/false/numbers, comments. `split_front_matter` reads the YAML block fenced by `---` at the
top of a Markdown file. Not a general YAML parser: anchors, multi-line strings and tags are unsupported.
"""
import json
import re

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




def split_front_matter(text):
    """Return (front_matter_dict, body_text). Files without a leading `---` fence parse whole as YAML only when
    they look like YAML (callers decide); here they return ({}, text)."""
    lines = text.lstrip("﻿").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return loads("\n".join(lines[1:i])) or {}, "\n".join(lines[i + 1:])
    return {}, text
