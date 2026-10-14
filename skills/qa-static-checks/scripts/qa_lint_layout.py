"""House-style layout and naming lint for first-party C# (stdlib only).

  py -I qa_lint_layout.py --project P [--files ...] [--root Assets/_Game]

Errors: file under first-party root declares no/other namespace than Game*; Data_*/Factory_*/Event_* type in the wrong folder;
        loose files directly under Assets/.
Warnings: file name differs from its first type; [SerializeField] field without leading underscore; const not UPPER_SNAKE.
Established projects keep their own spellings: pass --root to point at the project's real first-party folder.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qa_common import base_parser, finding, read_text, rel, report, select_files  # noqa: E402

TYPE_RE = re.compile(r"^\s*(?:public|internal)?\s*(?:abstract\s+|static\s+|sealed\s+|partial\s+)*(?:class|struct|enum|interface)\s+(\w+)", re.M)
NS_RE = re.compile(r"^\s*namespace\s+([\w.]+)", re.M)
SER_RE = re.compile(r"\[SerializeField\]\s*(?:private\s+)?[\w<>\[\],.?]+\s+(\w+)\s*[;=]")
CONST_RE = re.compile(r"\bconst\s+[\w<>\[\].]+\s+(\w+)\s*=")
ROLE_FOLDERS = (("Data_", "/Scripts/Data/"), ("Factory_", "/Scripts/Factory/"), ("Event_", "/Scripts/Event/"))


def lint_text(text, r):
    out = []
    types = TYPE_RE.findall(text)
    is_editor = "/Editor/" in "/" + r
    ns = NS_RE.search(text)
    if types and not ns:
        out.append(finding("NAMESPACE", "error", r, 1, "no namespace (expected Game or a Game.* namespace)"))
    elif ns and not ns.group(1).startswith("Game") and not is_editor:
        out.append(finding("NAMESPACE", "error", r, text[:ns.start()].count("\n") + 1, "namespace %s does not start with Game" % ns.group(1)))
    stem = os.path.splitext(os.path.basename(r))[0]
    if types and stem not in types:
        out.append(finding("FILE-NAME", "warn", r, 1, "file name %s differs from type %s" % (stem, types[0])))
    for t in types:
        for prefix, folder in ROLE_FOLDERS:
            if t.startswith(prefix) and folder not in "/" + r and not is_editor:
                out.append(finding("ROLE-FOLDER", "error", r, 1, "%s belongs under %s" % (t, folder.strip("/"))))
    for m in SER_RE.finditer(text):
        if not m.group(1).startswith("_"):
            out.append(finding("SERIALIZE-NAME", "warn", r, text[:m.start()].count("\n") + 1, "serialized field %s should start with _" % m.group(1)))
    for m in CONST_RE.finditer(text):
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", m.group(1)):
            out.append(finding("CONST-NAME", "warn", r, text[:m.start()].count("\n") + 1, "const %s should be UPPER_SNAKE_CASE" % m.group(1)))
    return out


def scan(root, files=None, first_party="Assets/_Game"):
    out = []
    for p in select_files(root, (".cs",), files, subdirs=("Assets",)):
        r = rel(root, p)
        parts = r.split("/")
        if len(parts) == 2 and parts[0] == "Assets":
            out.append(finding("ASSETS-ROOT", "error", r, 1, "loose file directly under Assets/"))
        if not r.startswith(first_party + "/") or "/Tests/" in r:
            continue
        text = read_text(p)
        if text:
            out += lint_text(text, r)
    return out


def main(argv=None):
    ap = base_parser(__doc__)
    ap.add_argument("--root", default="Assets/_Game", help="first-party content folder")
    a = ap.parse_args(argv)
    return report(scan(a.project, a.files, a.root), a.json)


if __name__ == "__main__":
    sys.exit(main())
