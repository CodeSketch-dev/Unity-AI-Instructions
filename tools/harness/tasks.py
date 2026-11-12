"""Harness task files: data/harness/tasks/<id>.json. Verifier commands are argument lists (never a shell string)."""
import json
from dataclasses import dataclass, field
from pathlib import Path

KINDS = ("work", "train")


@dataclass
class Task:
    id: str
    title: str
    brief: str
    owns: list
    verify: list
    permission: str = "repo-edit"
    kind: str = "work"
    max_attempts: int = 2
    agent: str = ""
    extra: dict = field(default_factory=dict)


def _check(raw, name):
    def bad(field_name, why):
        raise ValueError("task '%s': field '%s' %s" % (name, field_name, why))
    for k in ("id", "title", "brief"):
        if not isinstance(raw.get(k), str) or not raw[k].strip():
            bad(k, "must be a non-empty string")
    if not isinstance(raw.get("owns"), list) or not raw["owns"]:
        bad("owns", "must be a non-empty list of path globs")
    v = raw.get("verify")
    if not isinstance(v, list) or not v:
        bad("verify", "must be a non-empty list of {name, cmd}")
    for item in v:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            bad("verify", "items need a string name")
        if not isinstance(item.get("cmd"), list) or not item["cmd"] or not all(isinstance(c, str) for c in item["cmd"]):
            bad("verify.cmd", "must be an argument list, not a shell string")
    if raw.get("kind", "work") not in KINDS:
        bad("kind", "must be one of %s" % (KINDS,))


def load_tasks(directory):
    out = []
    for p in sorted(Path(directory).glob("*.json")):
        raw = json.loads(p.read_text(encoding="utf-8"))
        _check(raw, p.stem)
        known = {"id", "title", "brief", "owns", "verify", "permission", "kind", "max_attempts", "agent"}
        out.append(Task(extra={k: v for k, v in raw.items() if k not in known}, **{k: raw[k] for k in known if k in raw}))
    return sorted(out, key=lambda t: t.id)
