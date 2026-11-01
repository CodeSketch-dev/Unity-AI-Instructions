"""Build a mapping for migrate_scripts.py from flat `<Prefix><Feature><Part>` class names.

usage: python gen_all.py <source folder relative to the project, e.g. Assets/_Game/Old> [out.json]
For every .cs whose file name matches ^<Prefix>(Feature)(Part)$ (no dots) the mapping sends it to
<runtimeFolder>/<Feature>/<Prefix>_<Feature>_<Part>, or <editorFolder>/<Feature>/... when the path contains an Editor folder.
Prints name collisions. Settings: migration_config.py.
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import migration_config as cfg

P = cfg.prefix
src = os.path.join(cfg.PROJECT_ROOT, *sys.argv[1].split('/'))
out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migration', 'mapping.json')
runtime, editor = cfg.runtime_folder, cfg.editor_folder
out, names = {}, collections.Counter()
for d, _, fs in os.walk(src):
    is_editor = (os.sep + 'Editor' + os.sep) in (d + os.sep)
    for f in fs:
        if not f.endswith('.cs'):
            continue
        b = f[:-3]
        if '.' in b:
            continue
        m = re.match('^' + re.escape(P) + r'([A-Z][a-z0-9]*)(.*)$', b)
        if not m:
            continue
        feat, rest = m.groups()
        new = P + '_' + feat + ('_' + rest if rest else '')
        names[new] += 1
        out[b] = '%s/%s/%s' % (editor if is_editor else runtime, feat, new)
dups = [n for n, c in names.items() if c > 1]
os.makedirs(os.path.dirname(out_path), exist_ok=True)
json.dump(out, open(out_path, 'w'), indent=1)
print('classes', len(out), 'duplicate new names', dups, '->', out_path)
