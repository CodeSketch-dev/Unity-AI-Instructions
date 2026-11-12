#!/usr/bin/env python
"""Rename + move C# classes (file and .meta together, GUID kept) and rewrite identifiers in code (not in strings/comments).

usage: python migrate_scripts.py mapping.json [--apply] [--strings-only]
mapping.json: {"OldClass": "Scripts/Logic/<Prefix>/Rush/<Prefix>_Rush_Clock", ...}   (path relative to gameRoot, no .cs)
Without --apply it only prints the plan. --strings-only keeps files where they are and only rewrites references.
Project settings (prefix, namespace, roots): see migration_config.py / Tools/migration.json.
"""
import json, os, re, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cs_lex import lex
import migration_config as cfg

ROOT = cfg.PROJECT_ROOT
SCRIPTS = cfg.game_root
SEARCH_ROOTS = cfg.search_roots
NS = re.escape(cfg.namespace + '.')


def all_cs():
    for r in SEARCH_ROOTS:
        for d, _, fs in os.walk(r):
            for f in fs:
                if f.endswith('.cs'):
                    yield os.path.join(d, f)


def move_with_meta(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    if os.path.exists(src + '.meta'):
        shutil.move(src + '.meta', dst + '.meta')


def main():
    mapping = json.load(open(sys.argv[1], encoding='utf8'))
    apply = '--apply' in sys.argv
    strings_only = '--strings-only' in sys.argv
    files = {}
    for p in all_cs():
        files.setdefault(os.path.basename(p)[:-3], []).append(p)
    assets = []
    for r in SEARCH_ROOTS:
        for d, _, fs in os.walk(r):
            assets.extend(f for f in fs if f.endswith('.asset'))
    ren = {}
    extra = {}   # partial companions: 'Old.Suffix' -> (new file base, new path)
    for old, newpath in mapping.items():
        if any(old in a for a in assets):
            print('SKIP (asset named after class):', old)
            continue
        if strings_only:
            ren[old] = (os.path.basename(newpath), newpath)
            continue
        if old not in files or len(files[old]) != 1:
            print('SKIP (missing/ambiguous file):', old, files.get(old))
            continue
        ren[old] = (os.path.basename(newpath), newpath)
        for b in list(files):
            if b.startswith(old + '.') and len(files[b]) == 1:
                extra[b] = (os.path.basename(newpath) + b[len(old):], newpath + b[len(old):])
    if not ren:
        print('nothing to do')
        return
    names = '|'.join(sorted(map(re.escape, ren), key=len, reverse=True))
    pat = re.compile(r'\b(' + names + r')\b')
    refl = re.compile(r'(' + NS + r')(' + names + r')\b')
    texts = {p: open(p, encoding='utf-8-sig').read() for p in all_cs()}
    for p, t in texts.items():
        for is_code, seg in lex(t):
            if not is_code and seg.startswith('"') and pat.search(seg) and cfg.namespace + '.' not in seg:
                print('NOTE string literal mentions an old name:', os.path.relpath(p, ROOT), seg[:80])
    print('plan:', len(ren), 'renames')
    for o, (n, pth) in ren.items():
        print(' ', o, '->', pth)
    if not apply:
        return
    for p, t in texts.items():
        out = []
        for is_code, seg in lex(t):
            if is_code:
                out.append(pat.sub(lambda m: ren[m.group(1)][0], seg))
            elif seg.startswith('"') and cfg.namespace + '.' in seg:
                out.append(refl.sub(lambda m: m.group(1) + ren[m.group(2)][0], seg))
            else:
                out.append(seg)
        nt = ''.join(out)
        if nt != t:
            open(p, 'w', encoding='utf-8', newline='').write(nt)
    if strings_only:
        print('references rewritten')
        return
    for old, (new, newpath) in ren.items():
        move_with_meta(files[old][0], os.path.join(SCRIPTS, newpath.replace('/', os.sep) + '.cs'))
    for b, (nb, np_) in extra.items():
        src = files[b][0]
        if os.path.exists(src):
            move_with_meta(src, os.path.join(SCRIPTS, np_.replace('/', os.sep) + '.cs'))
    # reflection type names that were not in the mapping keys are left alone; the ones in it were handled above
    print('applied')


if __name__ == '__main__':
    main()
