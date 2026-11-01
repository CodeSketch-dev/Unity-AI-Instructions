import os, re, json, sys, collections
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Assets', '_Game', 'DigEgg'))
out = {}; newnames = collections.Counter()
for sub, prefix in (('Runtime', 'Runtime/Logic/Dig'), ('Editor', 'Editor/Dig')):
    for d, _, fs in os.walk(os.path.join(ROOT, sub)):
        if (os.sep + 'Logic' + os.sep + 'Dig') in d or (os.sep + 'Editor' + os.sep + 'Dig') in d: continue
        for f in fs:
            if not f.endswith('.cs'): continue
            b = f[:-3]
            if '.' in b: continue
            m = re.match(r'^Dig([A-Z][a-z0-9]*)(.*)$', b)
            if not m: continue
            feat, rest = m.groups()
            new = 'Dig_' + feat + ('_' + rest if rest else '')
            newnames[new] += 1
            out[b] = f'{prefix}/{feat}/{new}'
dup = [n for n, c in newnames.items() if c > 1]
print('classes', len(out), 'dups', dup)
json.dump(out, open(os.path.join(os.path.dirname(__file__), 'migration', 'rest.json'), 'w'), indent=1)
