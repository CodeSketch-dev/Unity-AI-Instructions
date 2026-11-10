"""Deterministic task classifier (no model call). Fast path for trivial work; criticality forces accuracy.

classify(text) -> {category, complexity, fast_path, critical, needs, deterministic, candidates, steps}
Evaluation must never cost more than execution: this is a handful of regexes.
"""
import json
import os
import re

_TAX = None


def taxonomy():
    global _TAX
    if _TAX is None:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "taxonomy.json"), encoding="utf-8") as f:
            _TAX = json.load(f)
    return _TAX


def classify(text, taxonomy_data=None):
    tx = taxonomy_data or taxonomy()
    t = (text or "").lower()
    cat = {"id": "generic.other", "candidates": ["direct_edit"], "deterministic": False, "needs": []}
    for c in tx["categories"]:
        if re.search(c["match"], t):
            cat = c
            break
    words = len(re.findall(r"\w+", t))
    steps = 1 + len(re.findall(tx["step_words"], t))
    scope = len(re.findall(r"\b(%s)\b" % tx["scope_words"], t))
    critical = bool(re.search(tx["critical"], t))
    score = (2 if words > 60 else 1 if words > 25 else 0) + min(steps - 1, 3) + (2 if scope else 0) + (2 if critical else 0)
    level = "trivial" if score == 0 and words <= 15 else "simple" if score <= 1 else "moderate" if score <= 3 else "complex"
    return {"category": cat["id"], "complexity": level, "critical": critical, "needs": cat.get("needs", []),
            "deterministic": cat.get("deterministic", False), "candidates": cat["candidates"], "steps": steps,
            "fast_path": level in ("trivial", "simple") and not critical,
            "note": "fast path: take candidates[0], verify, record; skip scoring" if level in ("trivial", "simple") and not critical
            else "evaluate: run `cli.py select` for this category/env; verify before continuing"}
