#!/usr/bin/env python
"""Rename + move C# classes (file and .meta together) and rewrite identifiers outside string literals.

usage: python migrate_scripts.py mapping.json [--apply]
mapping.json: {"OldClass": "Runtime/Logic/Dig/Rush/Dig_Rush_Clock", ...}   (path relative to Assets/_Game/DigEgg, no .cs, e.g. Runtime/Logic/Dig/Rush/Dig_Rush)
Without --apply it only prints the plan.
"""
import json, os, re, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cs_lex import lex

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ASSETS = os.path.join(ROOT, 'Assets')
SCRIPTS = os.path.join(ASSETS, '_Game')   # mapping paths are relative to Assets/_Game, e.g. Scripts/Logic/Dig/Rush/Dig_Rush
SEARCH_ROOTS = [os.path.join(ASSETS, '_Game'), os.path.join(ASSETS, 'SketchSdk')]
STR_RE = re.compile(r'(\$@"(?:[^"]|"")*"|@"(?:[^"]|"")*"|\$"(?:\.|[^"\\n])*"|"(?:\.|[^"\\n])*"|//[^\n]*)')


def all_cs():
    for r in SEARCH_ROOTS:
        for d, _, fs in os.walk(r):
            for f in fs:
                if f.endswith('.cs'):
                    yield os.path.join(d, f)


def main():
    mapping = json.load(open(sys.argv[1], encoding='utf8'))
    apply = '--apply' in sys.argv
    files = {}
    for p in all_cs():
        base = os.path.basename(p)[:-3]
        files.setdefault(base, []).append(p)
    assets = []
    for d, _, fs in os.walk(os.path.join(ASSETS, '_Game')):
        for f in fs:
            if f.endswith('.asset'):
                assets.append(f)
    ren = {}
    extra = {}   # partial companions: 'Old.Suffix' -> new path
    for old, newpath in mapping.items():
        if any(old in a for a in assets):
            print('SKIP (asset named after class):', old); continue
        for b in list(files):
            if b.startswith(old + '.') and len(files[b]) == 1:
                extra[b] = (os.path.basename(newpath) + b[len(old):], newpath + b[len(old):])
        if '--strings-only' in sys.argv:
            ren[old] = (os.path.basename(newpath), newpath); continue
        if old not in files or len(files[old]) != 1:
            print('SKIP (missing/ambiguous file):', old, files.get(old)); continue
        new = os.path.basename(newpath)
        ren[old] = (new, newpath)
    # string literals equal to an old name -> report
    pat = re.compile(r'\b(' + '|'.join(sorted(map(re.escape, ren), key=len, reverse=True)) + r')\b') if ren else None
    texts = {}
    for p in all_cs():
        t = open(p, encoding='utf-8-sig').read()
        texts[p] = t
        if pat:
            for m in STR_RE.finditer(t):
                s = m.group(0)
                if s.startswith('"') and pat.search(s):
                    print('NOTE string literal mentions old name:', os.path.relpath(p, ROOT), s[:80])
    print('plan:', len(ren), 'renames')
    for o, (n, pth) in ren.items():
        print(' ', o, '->', pth)
    if not apply or not ren:
        return
    for p, t in texts.items():
        refl = re.compile(r'(Game\.DigEgg\.)(' + '|'.join(sorted(map(re.escape, ren), key=len, reverse=True)) + r')')
        out = []
        for is_code, seg in lex(t):
            if is_code:
                out.append(pat.sub(lambda m: ren[m.group(1)][0], seg))
            elif seg.startswith('"') and 'Game.DigEgg.' in seg:
                out.append(refl.sub(lambda m: m.group(1) + ren[m.group(2)][0], seg))
            else:
                out.append(seg)
        nt = ''.join(out)
        if nt != t:
            open(p, 'w', encoding='utf-8', newline='').write(nt)
    if '--strings-only' in sys.argv:
        print('strings fixed'); return
    for old, (new, newpath) in ren.items():
        src = files[old][0]
        dst = os.path.join(SCRIPTS, newpath.replace('/', os.sep) + '.cs')
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        if os.path.exists(src + '.meta'):
            shutil.move(src + '.meta', dst + '.meta')
    for b, (nb, np_) in extra.items():
        src = files[b][0]
        if not os.path.exists(src):
            continue
        dst = os.path.join(SCRIPTS, np_.replace('/', os.sep) + '.cs')
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        if os.path.exists(src + '.meta'):
            shutil.move(src + '.meta', dst + '.meta')
    # reflection type names in strings: "Game.DigEgg.OldName," / "...OldName\""
    new_by_old = {o: n for o, (n, _) in ren.items()}
    for p2 in all_cs():
        t2 = open(p2, encoding='utf-8-sig').read()
        n2 = re.sub(r'(Game\.DigEgg\.)(\w+)(?=[,"])', lambda mm: mm.group(1) + new_by_old.get(mm.group(2), mm.group(2)), t2)
        if n2 != t2:
            open(p2, 'w', encoding='utf-8', newline='').write(n2)
    print('applied')


if __name__ == '__main__':
    main()
