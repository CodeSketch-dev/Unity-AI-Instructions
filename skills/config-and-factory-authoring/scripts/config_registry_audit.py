"""Static audit of config ScriptableObject assets against their factories (read-only).

Usage: py -I config_registry_audit.py [--no-fail] <unity-project>
Checks (text YAML only):
  unregistered-config   asset under Assets/_Game/Configs/<Feature>/ whose GUID no singleton factory asset references
  duplicate-id          same id-like field value on two assets in one folder
  null-ref              prefab/sprite/thumbnail/icon field set to {fileID: 0}
  pool-prewarm-over-max prewarm greater than max capacity in a pool config
Exit 1 if any finding unless --no-fail. Findings are WARN-level hints, not proof.
"""
import os
import re
import sys
from collections import defaultdict, namedtuple

Finding = namedtuple("Finding", "code path message")
SKIP_REGISTRATION = {"Audio", "Pool"}  # audio uses factory fields; pools are often auto-populated
ID_KEYS = ("_id", "_ID", "ID", "_skinName", "_productId", "_iapProductId")
NULL_HINT = re.compile(r"(prefab|sprite|thumbnail|icon|avatar)", re.I)
GUID_RE = re.compile(r"guid:\s*([0-9a-f]{32})")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def guid_of(asset_path):
    meta = asset_path + ".meta"
    if not os.path.isfile(meta):
        return None
    m = GUID_RE.search(read(meta))
    return m.group(1) if m else None


def singleton_refs(project):
    refs = set()
    for base, _, files in os.walk(os.path.join(project, "Assets")):
        if os.path.basename(base) == "ScriptableObjectSingletons":
            for name in files:
                if name.endswith(".asset"):
                    refs.update(GUID_RE.findall(read(os.path.join(base, name))))
    return refs


def config_assets(project):
    root = os.path.join(project, "Assets", "_Game", "Configs")
    for base, _, files in os.walk(root):
        for name in files:
            if name.endswith(".asset"):
                yield os.path.join(base, name)


def feature_of(project, path):
    rel = os.path.relpath(path, os.path.join(project, "Assets", "_Game", "Configs"))
    return rel.split(os.sep)[0]


def field(text, key):
    m = re.search(r"^\s*%s:\s*(.+?)\s*$" % re.escape(key), text, re.M)
    return m.group(1) if m else None


def audit(project):
    findings = []
    refs = singleton_refs(project)
    ids = defaultdict(list)
    for path in config_assets(project):
        rel = os.path.relpath(path, project)
        text = read(path)
        feature = feature_of(project, path)
        guid = guid_of(path)
        in_feature = os.path.dirname(path) != os.path.join(project, "Assets", "_Game", "Configs")
        if in_feature and feature not in SKIP_REGISTRATION and guid and guid not in refs:
            findings.append(Finding("unregistered-config", rel, "no singleton factory asset references this asset"))
        for key in ID_KEYS:
            val = field(text, key)
            if val and val not in ("", "0", "''", '""'):
                ids[(os.path.dirname(path), key, val)].append(rel)
        for m in re.finditer(r"^\s*(\w+):\s*\{fileID:\s*0\}", text, re.M):
            if not m.group(1).startswith("m_") and NULL_HINT.search(m.group(1)):
                findings.append(Finding("null-ref", rel, "%s is not assigned" % m.group(1)))
        pre, mx = field(text, "_poolPrewarm"), field(text, "_poolCapacityMax")
        if pre and mx and pre.isdigit() and mx.isdigit() and int(pre) > int(mx):
            findings.append(Finding("pool-prewarm-over-max", rel, "prewarm %s > max %s" % (pre, mx)))
    for (_, key, val), paths in ids.items():
        if len(paths) > 1:
            findings.append(Finding("duplicate-id", ",".join(paths), "%s '%s' used %d times" % (key, val, len(paths))))
    return findings


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    no_fail = "--no-fail" in argv
    args = [a for a in argv if a != "--no-fail"]
    if not args or not os.path.isdir(args[0]):
        print("usage: config_registry_audit.py [--no-fail] <unity-project>", file=sys.stderr)
        return 2
    findings = audit(args[0])
    for f in findings:
        print("WARN %s [%s] %s" % (f.code, f.path, f.message))
    print("%d finding(s)" % len(findings))
    return 1 if findings and not no_fail else 0


if __name__ == "__main__":
    sys.exit(main())
