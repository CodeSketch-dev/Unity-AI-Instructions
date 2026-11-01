#!/usr/bin/env python
"""Split multi-type C# files into one-type-per-file and build the rename mapping.

usage: python split_types.py <folder relative to gameRoot, e.g. Scripts/Logic/<Prefix>/Break> [--apply]
Dry run prints what would be split / renamed. --apply writes new files (named after the OLD type name, so
migrate_scripts.py can then rename + move them), renames single-type files whose name != type, and writes
Tools/migration/split_<folder>.json for migrate_scripts.py.

Rules: partial types never move (they stay where they are); a type whose new name collides with an existing one keeps
its old name (reported as COLLISION); a file is left untouched if any target file already exists.
Naming: <Prefix>_<Feature>_<Rest> where Feature = the folder, Rest = old name without the prefix / duplicated feature word.
Names without the prefix get <Prefix>_<Feature>_<Name>. Interfaces keep a leading 'I'. Prefix and folders: migration_config.py.
"""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cs_lex import lex
import migration_config as cfg

ROOT = cfg.game_root
P = cfg.prefix
TYPE_RE = re.compile(r'\b(class|struct|enum|interface)\s+(\w+)')
BOM = b'\xef\xbb\xbf'


def mask_of(t):
    out = []
    for is_code, seg in lex(t):
        out.append(seg if is_code else re.sub(r'[^\n\r]', ' ', seg))
    return ''.join(out)


def parse(t):
    """Return (preamble, members, ns_close). members: list of (start, end, name|None, kind|None, is_partial)."""
    m = mask_of(t)
    nss = list(re.finditer(r'\bnamespace\s+[\w\.]+\s*\{', m))
    if len(nss) != 1:
        return None          # none, or several namespace blocks: leave the file alone
    ns = nss[0]
    i = ns.end()
    depth = 0
    j = i
    n = len(m)
    spans = []
    start = i
    while j < n:
        c = m[j]
        if c == '{':
            depth += 1
        elif c == '}':
            if depth == 0:
                break
            depth -= 1
            if depth == 0:
                spans.append((start, j + 1))
                start = j + 1
        elif c == ';' and depth == 0:
            spans.append((start, j + 1))
            start = j + 1
        j += 1
    members = []
    for s, e in spans:
        seg = m[s:e]
        k = seg.find('{')
        head = seg[:k] if k >= 0 else seg
        mt = TYPE_RE.search(head)
        members.append((s, e, mt.group(2) if mt else None, mt.group(1) if mt else None,
                        bool(re.search(r'\bpartial\b', head))))
    return t[:ns.end()], members, j


def new_name(old, feature):
    iface = bool(re.match(r'^I[A-Z]\w*$', old))
    core = old[1:] if iface else old
    if core.startswith(P + '_'):
        return old
    if core.startswith(P) and len(core) > len(P) and core[len(P)].isupper():
        core = core[len(P):]
    if core.startswith(feature) and len(core) > len(feature) and core[len(feature)].isupper():
        core = core[len(feature):]
    elif core == feature:
        core = ''
    for w in (P + feature, P):
        if core.replace(w, '') and w in core[1:]:
            core = core.replace(w, '')
    nm = P + '_' + feature + ('_' + core if core else '')
    return ('I' + nm) if iface else nm


def write(path, text, bom):
    open(path, 'wb').write((BOM if bom else b'') + text.encode('utf-8'))


def main():
    folder = sys.argv[1]
    apply = '--apply' in sys.argv
    base = os.path.join(ROOT, folder.replace('/', os.sep))
    feature = os.path.basename(base.rstrip(os.sep))
    mapping = {}
    plan = []
    taken = {}
    existing = set()
    for dd, _, ff in os.walk(ROOT):
        for fn in ff:
            if fn.endswith('.cs'):
                existing.update(m_.group(2) for m_ in TYPE_RE.finditer(open(os.path.join(dd, fn), encoding='utf-8-sig', errors='ignore').read()))
    for d, _, fs in os.walk(base):
        for f in sorted(fs):
            if not f.endswith('.cs') or '.' in f[:-3]:
                continue
            p = os.path.join(d, f)
            raw = open(p, 'rb').read()
            t = raw.decode('utf-8-sig').replace('\r\n', '\n')
            crlf = b'\r\n' in raw
            bom = raw.startswith(BOM)
            r = parse(t)
            if r is None:
                plan.append(('SKIP (no block namespace)', p))
                continue
            pre, members, ns_close = r
            types = [x for x in members if x[2]]
            if not types:
                continue
            stem = f[:-3]
            tail = t[ns_close:]
            if tail.strip() != '}' or re.search(r'^\s*#(if|region)', t, re.M):
                plan.append(('SKIP (code after namespace or #if)', os.path.relpath(p, ROOT)))
                continue
            movable = [x for x in types if not x[4]]
            keep = next((x for x in types if x[2] == stem), movable[0] if movable else types[0])
            for s_, e_, nm, kind, part in types:
                nn = new_name(nm, feature)
                if nn != nm and (nn in existing or taken.get(nn, nm) != nm):
                    plan.append(('COLLISION kept old name ' + nm + ' (wanted ' + nn + ')', p))
                    continue
                taken[nn] = nm
                if nn != nm:
                    mapping[nm] = nn
            moved = [x for x in movable if x != keep]
            kind_ = 'split' if moved else ('rename-file' if keep[2] != stem and not keep[4] else 'ok')
            plan.append((kind_, os.path.relpath(p, ROOT), [x[2] for x in types], 'partial' if any(x[4] for x in types) else ''))
            if not apply:
                continue
            outs = []
            blocked = False
            for s_, e_, nm, kind, part in moved:
                out = os.path.join(d, nm + '.cs')
                if os.path.exists(out):
                    plan.append(('EXISTS, file untouched', out))
                    blocked = True
                    break
                outs.append((out, pre + t[s_:e_] + '\n' + tail))
            if blocked:
                continue
            nlfix = (lambda s: s.replace('\n', '\r\n')) if crlf else (lambda s: s)
            for out, body in outs:
                write(out, nlfix(body), bom)
            if moved:
                rest = [x for x in types if x not in moved]
                write(p, nlfix(pre + '\n'.join(t[x[0]:x[1]] for x in rest) + '\n' + tail), bom)
            if keep[2] != stem and not keep[4]:
                dst = os.path.join(d, keep[2] + '.cs')
                if not os.path.exists(dst):
                    os.replace(p, dst)
                    if os.path.exists(p + '.meta'):
                        os.replace(p + '.meta', dst + '.meta')
    for row in plan:
        print(*row)
    print('mapping', len(mapping))
    if apply:
        sub = cfg.editor_folder if 'Editor' in folder else cfg.runtime_folder
        out = {k: sub + '/' + feature + '/' + v for k, v in mapping.items()}
        json.dump(out, open(os.path.join(os.path.dirname(__file__), 'migration', 'split_' + feature + '.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
