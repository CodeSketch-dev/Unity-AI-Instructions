"""Detect CodeSketch/SketchEngine in a Unity project and grep the package source.

Usage: py -I framework_api_grep.py <unity-project> [symbol]
Prints framework, version, package dir. With a symbol, prints file:line hits (max 50).
Without a symbol, prints the count of public type declarations.
"""
import glob
import json
import os
import re
import sys

PACKAGES = (("com.codesketch", "CodeSketch"), ("com.sketchengine", "SketchEngine"))
TYPE_RE = re.compile(r"\b(?:public|internal)\s+(?:abstract\s+|static\s+|sealed\s+|partial\s+)*(?:class|struct|interface|enum)\s+(\w+)")
MAX_HITS = 50


def detect(project):
    result = {"framework": None, "package": None, "version": None, "package_dir": None}
    manifest = os.path.join(project, "Packages", "manifest.json")
    if not os.path.isfile(manifest):
        return result
    with open(manifest, encoding="utf-8") as f:
        deps = json.load(f).get("dependencies", {})
    for pkg, label in PACKAGES:
        if pkg in deps:
            result.update(framework=label, package=pkg, version=deps[pkg])
            embedded = os.path.join(project, "Packages", pkg)
            cache = sorted(glob.glob(os.path.join(project, "Library", "PackageCache", pkg + "@*")))
            if os.path.isdir(embedded):
                result["package_dir"] = embedded
            elif cache:
                result["package_dir"] = cache[0]
            break
    return result


def iter_cs(package_dir):
    for base, _, files in os.walk(package_dir):
        for name in files:
            if name.endswith(".cs"):
                yield os.path.join(base, name)


def find_symbol(package_dir, symbol):
    pat = re.compile(r"\b%s\b" % re.escape(symbol))
    hits = []
    for path in iter_cs(package_dir):
        with open(path, encoding="utf-8", errors="replace") as f:
            for n, line in enumerate(f, 1):
                if pat.search(line):
                    hits.append((path, n, line.strip()))
                    if len(hits) >= MAX_HITS:
                        return hits
    return hits


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or not os.path.isdir(argv[0]):
        print("usage: framework_api_grep.py <unity-project> [symbol]", file=sys.stderr)
        return 2
    d = detect(argv[0])
    if not d["framework"]:
        print("framework: none found in Packages/manifest.json")
        return 1
    print("framework: %s (%s %s)" % (d["framework"], d["package"], d["version"]))
    print("package_dir: %s" % (d["package_dir"] or "NOT FOUND (open the project in Unity once to populate Library/PackageCache)"))
    if not d["package_dir"]:
        return 1
    if len(argv) > 1:
        for path, n, line in find_symbol(d["package_dir"], argv[1]):
            print("%s:%d: %s" % (os.path.relpath(path, d["package_dir"]), n, line[:140]))
    else:
        count = 0
        for path in iter_cs(d["package_dir"]):
            with open(path, encoding="utf-8", errors="replace") as f:
                count += len(TYPE_RE.findall(f.read()))
        print("public types: %d" % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
