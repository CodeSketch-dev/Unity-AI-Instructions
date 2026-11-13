"""Lint-Triggered Skills engine. One rule = one file in tools/lint/rules/ exporting RULE (or RULES).
Every violation message is a micro-prompt: why it is banned + the skill file the agent MUST read.
The skill path is the one that exists inside a synced Unity project: .claude/skills/<name>/SKILL.md."""
import importlib
import os
import pkgutil
import re
from dataclasses import dataclass


@dataclass
class Rule:
    id: str
    pattern: str
    why: str
    skill: str
    require: str = None
    ext: tuple = (".cs",)
    exclude_dirs: tuple = ("Editor", "Tests", "Test")
    # Optional lexical scanner: text -> iterable of 1-based violation lines.
    scan: object = None


@dataclass
class Violation:
    path: str
    line: int
    rule_id: str
    message: str


def load_rules():
    import rules as pkg
    out = []
    for m in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module("rules." + m.name)
        if hasattr(mod, "RULE"):
            out.append(mod.RULE)
        out.extend(getattr(mod, "RULES", []))
    return out


VENDOR_DIRS = ("Packages", "Library", "PackageCache", "Plugins", "ThirdParty", "ReferenceSource~")


def _applies(rule, path):
    if not path.lower().endswith(rule.ext):
        return False
    parts = path.replace(chr(92), "/").split("/")
    return not any(p in rule.exclude_dirs or p in VENDOR_DIRS for p in parts[:-1])


def lint_text(path, text, rules=None):
    rules = load_rules() if rules is None else rules
    found = []
    lines = text.splitlines()
    for r in rules:
        if not _applies(r, path):
            continue
        if r.require and not re.search(r.require, text):
            continue
        if r.scan is None:
            rx = re.compile(r.pattern)
            matches = [i for i, line in enumerate(lines, 1) if rx.search(line)]
        else:
            matches = sorted({i for i in r.scan(text) if type(i) is int and 1 <= i <= len(lines)})
        for i in matches:
            line = lines[i - 1]
            if line.lstrip().startswith("//"):
                continue
            if ("lint-ok:" + r.id) not in line:
                msg = "[RULE %s] %s MANDATORY: read .claude/skills/%s/SKILL.md before fixing this line. Opt out only with // lint-ok:%s <reason>." % (r.id, r.why, r.skill, r.id)
                found.append(Violation(path, i, r.id, msg))
    return found
