"""Select a phase-scoped skill manifest without loading skill bodies."""
from __future__ import annotations

import argparse
import json
import os
import time


def select(requested, always_on=(), previous=(), available=None):
    """Return sorted active skills and the names removed from the prior context."""
    available = set(available) if available is not None else None
    requested = set(requested or ())
    always_on = set(always_on or ())
    names = requested | always_on
    if available is not None:
        missing = sorted(names - available)
        if missing:
            raise ValueError("unknown skills: %s" % ", ".join(missing))
    return {"active": sorted(names), "unload": sorted(set(previous or ()) - names)}


def write_manifest(path, requested, always_on=(), phase="unknown", available=None, previous=()):
    """Atomically write the compact active-context manifest; no SKILL.md body is copied."""
    result = select(requested, always_on, previous, available)
    data = {"schema": 1, "phase": phase, "active": result["active"], "unload": result["unload"],
            "updated": time.strftime("%Y-%m-%dT%H:%M:%S")}
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=1)
    os.replace(temporary, path)
    return data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--phase", default="unknown")
    ap.add_argument("--requested", nargs="*", default=[])
    ap.add_argument("--always-on", nargs="*", default=[])
    args = ap.parse_args(argv)
    print(json.dumps(write_manifest(args.out, args.requested, args.always_on, args.phase), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
