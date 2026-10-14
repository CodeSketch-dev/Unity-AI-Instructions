"""Condense a Unity Editor log / pasted Console text into a short, deduplicated list of problems.

Why: raw logs are tens of thousands of tokens and mostly repeats. This prints one line per distinct problem
with count and first source location, compile errors first.

  python -I summarize_unity_log.py                       # default Editor.log of this OS, last session part
  python -I summarize_unity_log.py path/to/log.txt --top 15 --warnings
  type console.txt | python -I summarize_unity_log.py -  # read stdin

Default log locations
  Windows  %LOCALAPPDATA%\\Unity\\Editor\\Editor.log
  macOS    ~/Library/Logs/Unity/Editor.log
"""
import argparse
import os
import re
import sys
from collections import OrderedDict

COMPILE_RE = re.compile(r"(Assets/[^\s(]+|Packages/[^\s(]+)\((\d+),(\d+)\):\s*(error|warning)\s+(CS\d+):\s*(.+)")
LOC_RE = re.compile(r"\(at ((?:Assets|Packages)/[^\s:)]+):(\d+)\)")
EXC_RE = re.compile(r"^(?:[\w.]+\.)?(\w+(?:Exception|Error))\s*:\s*(.*)")
MARKERS = ("Begin MonoManager ReloadAssembly", "Reloading assemblies after finishing script compilation",
           "- Starting Compile", "Initialize engine version")
NOISE = ("Unloading ", "Total:", "AssetDatabase", "Refresh completed", "Asset Pipeline", "Mono: successfully", "[Licensing]",
         "Native extension", "Importing", "Start importing")


def default_log():
    if sys.platform.startswith("win"):
        return os.path.join(os.environ.get("LOCALAPPDATA", ""), "Unity", "Editor", "Editor.log")
    return os.path.expanduser("~/Library/Logs/Unity/Editor.log")


def normalize(msg):
    msg = re.sub(r"0x[0-9a-fA-F]+", "0x?", msg)
    msg = re.sub(r"\b\d{3,}\b", "N", msg)
    msg = re.sub(r"\(at [^)]*\)", "", msg)
    return msg.strip()[:160]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log", nargs="?", default=None, help="log file, or - for stdin (default: Editor.log)")
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--warnings", action="store_true", help="include warnings (default: errors/exceptions only)")
    parser.add_argument("--all-sessions", action="store_true", help="do not cut at the last domain reload/compile marker")
    args = parser.parse_args()

    if args.log == "-":
        text = sys.stdin.read()
    else:
        path = args.log or default_log()
        if not os.path.isfile(path):
            sys.exit(f"log not found: {path}")
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            text = handle.read()
    lines = text.splitlines()
    total_lines = len(lines)

    if not args.all_sessions:
        last = -1
        for i, line in enumerate(lines):
            if any(m in line for m in MARKERS):
                last = i
        if last >= 0:
            lines = lines[last:]

    problems = OrderedDict()

    def add(kind, key, msg, loc):
        entry = problems.setdefault((kind, key), {"kind": kind, "msg": msg, "loc": loc, "count": 0})
        entry["count"] += 1
        if not entry["loc"] and loc:
            entry["loc"] = loc

    i = 0
    while i < len(lines):
        line = lines[i]
        m = COMPILE_RE.search(line)
        if m:
            kind = "COMPILE-ERR" if m.group(4) == "error" else "COMPILE-WARN"
            if kind == "COMPILE-ERR" or args.warnings:
                add(kind, (m.group(5), m.group(1), m.group(2)), f"{m.group(5)} {m.group(6)[:120]}", f"{m.group(1)}:{m.group(2)}")
            i += 1
            continue
        stripped = line.strip()
        if any(stripped.startswith(n) for n in NOISE):
            i += 1
            continue
        e = EXC_RE.match(stripped)
        is_exc = bool(e)
        is_log_err = stripped.startswith("[Error]") or stripped.lower().startswith("error:") or stripped.startswith("Assertion failed")
        is_warn = args.warnings and (stripped.startswith("[Warning]") or stripped.lower().startswith("warning:"))
        if is_exc or is_log_err or is_warn:
            loc = None
            for j in range(i, min(i + 12, len(lines))):
                lm = LOC_RE.search(lines[j])
                if lm:
                    loc = f"{lm.group(1)}:{lm.group(2)}"
                    break
            kind = "EXCEPTION" if is_exc else ("ERROR" if is_log_err else "WARN")
            msg = normalize(stripped)
            add(kind, (msg, loc), msg, loc)
        i += 1

    order = {"COMPILE-ERR": 0, "EXCEPTION": 1, "ERROR": 2, "COMPILE-WARN": 3, "WARN": 4}
    items = sorted(problems.values(), key=lambda p: (order[p["kind"]], -p["count"]))
    print(f"log lines: {total_lines}, analysed: {len(lines)}, distinct problems: {len(items)}")
    if not items:
        print("no errors found in the analysed part")
        return
    print("| # | kind | x | message | first location |\n|---|---|---|---|---|")
    for n, p in enumerate(items[:args.top], 1):
        print(f"| {n} | {p['kind']} | {p['count']} | {p['msg'].replace('|', '/')[:120]} | {p['loc'] or ''} |")
    if len(items) > args.top:
        print(f"... {len(items) - args.top} more (use --top)")
    first_compile = [p for p in items if p["kind"] == "COMPILE-ERR"]
    if first_compile:
        print("\nFix compile errors first: nothing else reflects the current code until they are gone.")


if __name__ == "__main__":
    main()
