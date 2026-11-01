#!/usr/bin/env python
"""Knife Tower style parity audit: per feature folder, counts of patterns that differ from the house style.

usage: python style_audit.py <scripts root>      (e.g. Assets/_Game/DigEgg/Runtime/Logic/Dig)
Columns: files | C# event/static Action (-> StaticBus + Event_ classes) | coroutines (-> UniTask) | Update() (-> tick/event)
         | MonoBehaviour (-> <X>_Component : MonoCached) | explicit private | #region | file != class name
"""
import os, re, sys

root = sys.argv[1]
rows = []
for feat in sorted(os.listdir(root)):
    p = os.path.join(root, feat)
    if not os.path.isdir(p):
        continue
    c = dict(files=0, ev=0, co=0, upd=0, mb=0, prv=0, reg=0, mism=0)
    for d, _, fs in os.walk(p):
        for f in fs:
            if not f.endswith('.cs'):
                continue
            t = open(os.path.join(d, f), encoding='utf-8-sig', errors='ignore').read()
            c['files'] += 1
            c['ev'] += len(re.findall(r'\bevent\s+(?:System\.)?Action|static\s+(?:System\.)?Action', t))
            c['co'] += t.count('IEnumerator')
            c['upd'] += len(re.findall(r'\bvoid Update\(', t))
            c['mb'] += len(re.findall(r':\s*MonoBehaviour\b', t))
            c['prv'] += len(re.findall(r'^\s*private\s', t, re.M))
            c['reg'] += t.count('#region')
            base = f[:-3].split('.')[0]
            m = re.findall(r'\b(?:class|struct|enum)\s+(\w+)', t)
            if m and base not in m:
                c['mism'] += 1
    rows.append((feat, c))
print('%-14s %5s %5s %5s %5s %5s %5s %5s %5s' % ('feature', 'files', 'event', 'coro', 'upd', 'mb', 'priv', 'regn', 'mism'))
tot = dict.fromkeys(rows[0][1], 0) if rows else {}
for feat, c in rows:
    print('%-14s %5d %5d %5d %5d %5d %5d %5d %5d' % (feat, c['files'], c['ev'], c['co'], c['upd'], c['mb'], c['prv'], c['reg'], c['mism']))
    for k in c:
        tot[k] += c[k]
print('%-14s %5d %5d %5d %5d %5d %5d %5d %5d' % ('TOTAL', tot['files'], tot['ev'], tot['co'], tot['upd'], tot['mb'], tot['prv'], tot['reg'], tot['mism']))
