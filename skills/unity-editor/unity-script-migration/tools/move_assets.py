#!/usr/bin/env python
"""Move asset files/folders (with their .meta, GUIDs unchanged) and rewrite the path strings in C# code.

usage: python move_assets.py map.json [--apply]
map.json: {"Assets/Old/Folder": "Assets/New/Folder", "Assets/Old/File.shader": "Assets/NewDir/"}   (a destination ending in '/' keeps the name)
 - a folder move onto an existing folder merges (files moved one by one, name clashes are reported and skipped)
 - path strings in .cs files ("Assets/Old/Folder/x.asset", "_Game/Old/...") are rewritten with the lexer, longest prefix first
Dry run by default. Unity must be closed or refreshed afterwards (AssetDatabase.Refresh); references are by GUID so nothing else changes.
"""
import json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cs_lex import lex
import migration_config as cfg

ROOT = cfg.PROJECT_ROOT
apply = '--apply' in sys.argv
mapping = json.load(open(sys.argv[1], encoding='utf-8'))
norm = lambda p: p.replace('\\', '/').rstrip('/')


def target(src, dst):
    if dst.endswith('/'):
        return norm(dst) + '/' + os.path.basename(norm(src))
    return norm(dst)


moves = []
for src, dst in mapping.items():
    s = os.path.join(ROOT, *norm(src).split('/'))
    d = target(src, dst)
    if not os.path.exists(s):
        print('SKIP (missing):', src)
        continue
    moves.append((norm(src), d))


def move_one(src, dst):
    s = os.path.join(ROOT, *src.split('/'))
    d = os.path.join(ROOT, *dst.split('/'))
    os.makedirs(os.path.dirname(d), exist_ok=True)
    if os.path.isdir(s) and os.path.isdir(d):
        for name in os.listdir(s):
            if name.endswith('.meta') and name[:-5] == os.path.basename(s):
                continue
            sub_s, sub_d = src + '/' + name, dst + '/' + name
            if os.path.exists(os.path.join(ROOT, *sub_d.split('/'))) and not name.endswith('.meta'):
                print('CLASH, skipped:', sub_s, '->', sub_d)
                continue
            if name.endswith('.meta'):
                continue
            move_one(sub_s, sub_d)
        return
    shutil.move(s, d)
    if os.path.exists(s + '.meta'):
        shutil.move(s + '.meta', d + '.meta')


for src, dst in moves:
    n = sum(len(fs) for _, _, fs in os.walk(os.path.join(ROOT, *src.split('/')))) if os.path.isdir(os.path.join(ROOT, *src.split('/'))) else 1
    print('%6d files  %s -> %s' % (n, src, dst))
if not apply:
    sys.exit(0)
for src, dst in moves:
    move_one(src, dst)
# path strings in code
pairs = sorted(moves, key=lambda m: -len(m[0]))
pats = []
for src, dst in pairs:
    pats.append((re.compile(re.escape(src)), dst))
    if src.startswith('Assets/'):
        pats.append((re.compile(r'(?<![\w/])' + re.escape(src[len('Assets/'):])), dst[len('Assets/'):]))
changed = 0
for r in cfg.search_roots:
    for d, _, fs in os.walk(r):
        for f in fs:
            if not f.endswith('.cs'):
                continue
            p = os.path.join(d, f)
            t = open(p, encoding='utf-8-sig').read()
            out = []
            for code, seg in lex(t):
                if not code and seg.startswith(('"', '$"', '@"')):
                    for pat, rep in pats:
                        seg = pat.sub(rep, seg)
                out.append(seg)
            nt = ''.join(out)
            if nt != t:
                open(p, 'w', encoding='utf-8', newline='').write(nt)
                changed += 1
print('moved', len(moves), 'entries; rewrote path strings in', changed, 'files')
