"""List public events / static Actions and how many OTHER feature folders subscribe to them.

Cross-feature broadcasts are StaticBus candidates; events consumed only inside the owner's own feature (like Knife Tower's
`Character.EventDead += ...`) stay plain C# events.
usage: python event_audit.py [scripts root]
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import migration_config as cfg

root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(cfg.game_root, 'Scripts')
decl = re.compile(r'public (?:static )?event (?:System\.)?Action(?:<[^;]*?>)?\s+([\w, ]+);')
sdecl = re.compile(r'public static (?:System\.)?Action(?:<[^;]*?>)?\s+(\w+)\s*[;=]')
files = {}
for d, _, fs in os.walk(root):
    for f in fs:
        if f.endswith('.cs'):
            files[os.path.join(d, f)] = open(os.path.join(d, f), encoding='utf-8-sig').read()


def feature(p):
    parts = p.replace('\\', '/').split('/')
    for i, x in enumerate(parts):
        if x in ('Logic', 'Editor') and i + 2 < len(parts):
            return parts[i + 2] if parts[i + 1] == cfg.prefix else parts[i + 1]
    return os.path.dirname(p)


rows = []
for p, t in files.items():
    for m in list(decl.finditer(t)) + list(sdecl.finditer(t)):
        for name in [n.strip() for n in m.group(1).split(',')]:
            subs = set()
            for q, u in files.items():
                if q == p:
                    continue
                if re.search(r'\.' + name + r'\s*[+-]=|\b' + name + r'\s*[+-]=', u):
                    subs.add(feature(q))
            own = feature(p)
            cross = sorted(s for s in subs if s != own)
            rows.append((len(cross), os.path.relpath(p, root), name, cross))
for n, f, name, cross in sorted(rows, key=lambda r: -r[0]):
    print('%2d %-48s %-22s %s' % (n, f, name, ','.join(cross)))
print('events', len(rows), 'with cross-feature subscribers', sum(1 for r in rows if r[0]))
