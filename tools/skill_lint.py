"""Lint a skills directory.

Usage: py -I tools/skill_lint.py [--strict] <skills-dir>
Exit 0 when there are no errors (and no warnings with --strict), else 1.
"""
import os
import re
import sys
from collections import defaultdict, namedtuple

Finding = namedtuple("Finding", "severity code skill message")

DESC_MIN, DESC_MAX = 20, 300
BODY_MAX_LINES = 500  # body must be strictly shorter
SHINGLE = 6  # words shared by two descriptions that count as a trigger collision
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def parse_frontmatter(text):
    """Return (dict, body) or (None, text). Supports key: value, quoted values, and > / | folded blocks."""
    lines = text.lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, text
    data = {}
    key = None
    for raw in lines[1:end]:
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if m and not raw.startswith((" ", "\t")):
            key, val = m.group(1), m.group(2).strip()
            if val in (">", "|", ">-", "|-"):
                val = ""
            elif len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            data[key] = val
        elif key and raw.strip():
            data[key] = (data[key] + " " + raw.strip()).strip()
    return data, "\n".join(lines[end + 1:])


def plain_scalar_problem(raw):
    """A real YAML parser rejects an unquoted scalar containing ': ' or ' #' or starting with an indicator character."""
    raw = raw.strip()
    if not raw or raw[0] in "\"'":
        return None
    if raw[0] in "[{&*!|>%@`" or ": " in raw or " #" in raw or raw.endswith(":"):
        return "unquoted value would fail strict YAML (contains ': ' or ' #' or starts with an indicator); wrap it in double quotes"
    return None


def strip_fences(body):
    out, fenced = [], False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def shingles(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(words[i:i + SHINGLE]) for i in range(len(words) - SHINGLE + 1)}


def lint_dir(root):
    findings = []
    names = defaultdict(list)
    descs = {}
    for folder in sorted(os.listdir(root)):
        sdir = os.path.join(root, folder)
        if not os.path.isdir(sdir):
            continue
        path = os.path.join(sdir, "SKILL.md")
        if not os.path.isfile(path):
            findings.append(Finding("error", "no-skill-md", folder, "SKILL.md missing"))
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        fm, body = parse_frontmatter(text)
        if fm is None:
            findings.append(Finding("error", "no-frontmatter", folder, "frontmatter missing or unterminated"))
            continue
        name = fm.get("name", "")
        names[name].append(folder)
        if name != folder:
            findings.append(Finding("error", "name-mismatch", folder, "name '%s' != folder" % name))
        for key in ("name", "description"):
            m = re.search(r"^%s:[ 	]*(.*)$" % key, text, re.M)
            problem = plain_scalar_problem(m.group(1)) if m else None
            if problem:
                findings.append(Finding("error", "yaml-plain-scalar", folder, "%s: %s" % (key, problem)))
        desc = fm.get("description", "")
        if not (DESC_MIN <= len(desc) <= DESC_MAX):
            findings.append(Finding("error", "description-length", folder,
                                    "description is %d chars, need %d-%d" % (len(desc), DESC_MIN, DESC_MAX)))
        descs[folder] = desc
        n_lines = len(body.splitlines())
        if n_lines >= BODY_MAX_LINES:
            findings.append(Finding("error", "body-too-long", folder,
                                    "body %d lines, limit < %d (move detail to references/)" % (n_lines, BODY_MAX_LINES)))
        for target in LINK_RE.findall(strip_fences(body)):
            if re.match(r"^([a-z][a-z0-9+.-]*:|#)", target, re.I):
                continue
            rel = target.split("#", 1)[0]
            if rel and not os.path.exists(os.path.normpath(os.path.join(sdir, rel))):
                findings.append(Finding("error", "missing-ref", folder, "linked file not found: %s" % rel))
    for name, folders in names.items():
        if name and len(folders) > 1:
            findings.append(Finding("error", "duplicate-name", ",".join(folders), "name '%s' used %d times" % (name, len(folders))))
    seen = defaultdict(list)
    for folder, desc in descs.items():
        for sh in shingles(desc):
            seen[sh].append(folder)
    pairs = defaultdict(set)
    for sh, folders in seen.items():
        if len(set(folders)) > 1:
            fs = sorted(set(folders))
            for i in range(len(fs)):
                for j in range(i + 1, len(fs)):
                    pairs[(fs[i], fs[j])].add(sh)
    for (a, b), shs in sorted(pairs.items()):
        findings.append(Finding("warn", "trigger-collision", "%s,%s" % (a, b),
                                "descriptions share %d phrase(s), e.g. '%s'" % (len(shs), sorted(shs)[0])))
    return findings


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    strict = "--strict" in argv
    args = [a for a in argv if a != "--strict"]
    if len(args) != 1 or not os.path.isdir(args[0]):
        print("usage: skill_lint.py [--strict] <skills-dir>", file=sys.stderr)
        return 2
    findings = lint_dir(args[0])
    for f in findings:
        print("%s %s [%s] %s" % (f.severity.upper(), f.code, f.skill, f.message))
    errors = sum(1 for f in findings if f.severity == "error")
    warns = sum(1 for f in findings if f.severity == "warn")
    print("%d error(s), %d warning(s)" % (errors, warns))
    return 1 if errors or (strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
