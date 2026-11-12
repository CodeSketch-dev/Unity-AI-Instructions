"""Heal references to old type names: map unresolved PascalCase identifiers to the declared <Prefix>_<Feature>_<Part> type with the same normalized key.
usage: python fix_unresolved.py [--apply]"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cs_lex import lex
import migration_config as cfg
P = cfg.prefix
ROOT = cfg.game_root
TYPE_RE = re.compile(r'\b(?:class|struct|enum|interface|delegate\s+\w+)\s+(\w+)')
files = []
for d, _, fs in os.walk(ROOT):
    for f in fs:
        if f.endswith('.cs'):
            files.append(os.path.join(d, f))
texts = {p: open(p, encoding='utf-8-sig').read() for p in files}
declared = set()
for t in texts.values():
    declared.update(TYPE_RE.findall(t))
def key(n):
    n = re.sub(r'^I(?=' + P + '_)', '', n)
    return re.sub('_|' + P, '', n).lower()
by_key = {}
for n in declared:
    if n.startswith((P + '_', 'I' + P + '_')):
        by_key.setdefault(key(n), set()).add(n)
fix = {}
for k, v in by_key.items():
    if len(v) == 1:
        fix[k] = next(iter(v))
tok = re.compile(r'\b[A-Z]\w*\b|\bI[A-Z]\w*\b')
changed = 0
report = {}
for p, t in texts.items():
    out = []
    for is_code, seg in lex(t):
        if is_code:
            def rep(m):
                w = m.group(0)
                if w in declared or w.startswith((P + '_', 'I' + P + '_')):
                    return w
                k = key(w)
                if k in fix and (re.match(r'^I?' + P + '[A-Z]', w)) and len(k) > 6:
                    report[w] = fix[k]
                    return fix[k] if not (w.startswith('I') and fix[k].startswith('I' + P + '_')) else fix[k]
                return w
            seg = tok.sub(rep, seg)
        out.append(seg)
    nt = ''.join(out)
    if nt != t and '--apply' in sys.argv:
        open(p, 'w', encoding='utf-8', newline='').write(nt)
        changed += 1
for a, b in sorted(report.items()):
    print(a, '->', b)
print('files changed', changed, 'distinct symbols', len(report))
