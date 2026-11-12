"""Find missing scripts and dangling references in text-serialized Unity assets without opening Unity.

  py -I qa_scan_refs.py --project P [--files Assets/_Game/Prefabs/A.prefab] [--required-refs qa/required-refs.json]

Checks (.unity, .prefab, .asset, .mat, .controller, .anim that start with %YAML):
  MISSING-SCRIPT  MonoBehaviour whose m_Script guid has no .meta in the project
  MISSING-REF     {fileID: N, guid: G} where G is unknown (builtin guids and Library/PackageCache are honoured)
  DANGLING-LOCAL  {fileID: N} (no guid) whose &N anchor is not in the same file
  NULL-REQUIRED   a field matching a pattern in required-refs.json with {fileID: 0}
Binary-serialized assets are skipped with an INFO-less note in the summary (they cannot be read as text).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qa_common import base_parser, finding, first_party, read_text, rel, report, select_files, walk  # noqa: E402

EXTS = (".unity", ".prefab", ".asset", ".mat", ".controller", ".anim", ".overrideController")
GUID_RE = re.compile(r"^guid:\s*([0-9a-f]{32})", re.M)
REF_RE = re.compile(r"\{fileID: (-?\d+)(?:, guid: ([0-9a-f]{32}))?(?:, type: \d+)?\}")
SCRIPT_RE = re.compile(r"m_Script: \{fileID: 11500000, guid: ([0-9a-f]{32}), type: \d+\}")
ANCHOR_RE = re.compile(r"^--- !u!\d+ &(-?\d+)", re.M)
FIELD_RE = re.compile(r"^\s*([A-Za-z_][\w]*): \{fileID: 0\}\s*$")
BUILTIN_PREFIX = ("0000000000000000",)


def guid_map(root):
    guids = set()
    for p in walk(root, (".meta",)):
        t = read_text(p)
        m = GUID_RE.search(t or "")
        if m:
            guids.add(m.group(1))
    cache = os.path.join(root, "Library", "PackageCache")
    if os.path.isdir(cache):
        for dp, dn, fn in os.walk(cache):
            for n in fn:
                if n.endswith(".meta"):
                    t = read_text(os.path.join(dp, n))
                    m = GUID_RE.search(t or "")
                    if m:
                        guids.add(m.group(1))
    return guids


def scan_file(root, path, guids, required):
    text = read_text(path)
    out = []
    if text is None or not text.startswith("%YAML"):
        return out, text is not None and not text.startswith("%YAML")
    r = rel(root, path)
    anchors = set(ANCHOR_RE.findall(text))
    for n, line in enumerate(text.splitlines(), 1):
        m = SCRIPT_RE.search(line)
        if m and m.group(1) not in guids and not m.group(1).startswith(BUILTIN_PREFIX):
            out.append(finding("MISSING-SCRIPT", "error", r, n, "script guid %s has no .meta" % m.group(1)))
            continue
        for fid, guid in REF_RE.findall(line):
            if guid:
                if guid not in guids and not guid.startswith(BUILTIN_PREFIX) and not guid.startswith("f000000000000000"):
                    out.append(finding("MISSING-REF", "error", r, n, "guid %s not found" % guid))
            elif fid != "0" and fid not in anchors:
                out.append(finding("DANGLING-LOCAL", "error", r, n, "fileID %s has no anchor in this file" % fid))
        if required:
            fm = FIELD_RE.match(line)
            if fm and any(p.search(fm.group(1)) for p in required):
                out.append(finding("NULL-REQUIRED", "error", r, n, "required field %s is null" % fm.group(1)))
    return out, False


def scan(root, files=None, required_patterns=None, scope="Assets/_Game"):
    required = [re.compile(p) for p in (required_patterns or [])]
    guids = guid_map(root)
    findings, binary = [], 0
    subdirs = (first_party(root, scope),) if files is None else ("Assets", "Packages")
    for p in select_files(root, EXTS, files, subdirs=subdirs):
        f, was_binary = scan_file(root, p, guids, required)
        findings += f
        binary += 1 if was_binary else 0
    return findings, binary


def main(argv=None):
    ap = base_parser(__doc__)
    ap.add_argument("--required-refs", help="JSON file with {\"patterns\": [regex, ...]} of field names that must not be null")
    a = ap.parse_args(argv)
    patterns = []
    if a.required_refs and os.path.isfile(a.required_refs):
        with open(a.required_refs, encoding="utf-8") as f:
            patterns = json.load(f).get("patterns", [])
    findings, binary = scan(a.project, a.files, patterns, a.first_party)
    if binary:
        sys.stdout.write("note: %d binary-serialized asset(s) skipped\n" % binary)
    return report(findings, a.json)


if __name__ == "__main__":
    sys.exit(main())
