#!/usr/bin/env python
"""Rebase `class X : MonoBehaviour` onto SketchEngine's MonoCached and use its cached accessors.

usage: python to_mono_cached.py <folder relative to the project> [--apply]
Per file that declares at least one `class X : MonoBehaviour[, interfaces]`:
 - base type MonoBehaviour -> MonoCached (adds `using SketchEngine.Mono;`)
 - bare `transform` -> TransformCached and bare `gameObject` -> GameObjectCached (code only, never after a dot),
   skipped when the file declares its own identifier called transform/gameObject (parameter, local, field)
 - instance methods named Tick()/LateTick()/FixedTick() become `public override` (they would hide MonoCached's hooks)
Compile errors afterwards show any non-converted class in the same file that used a bare `transform`.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cs_lex import lex
import migration_config as cfg

root = os.path.join(cfg.PROJECT_ROOT, *sys.argv[1].split('/'))
apply = '--apply' in sys.argv
CLS = re.compile(r'(\bclass\s+\w+\s*:\s*)MonoBehaviour\b')
DECL = re.compile(r'\b(?:Transform|GameObject|var|RectTransform)\s+(transform|gameObject)\b|\b(transform|gameObject)\s*=>|\bout\s+\w+\s+(transform|gameObject)\b')
HOOK = re.compile(r'^([ \t]*)(?:public |private |internal |protected )?void (Tick|LateTick|FixedTick)\(\)', re.M)
files = changed_files = classes = 0
for d, _, fs in os.walk(root):
    if os.sep + 'Editor' + os.sep in d + os.sep:
        continue
    for f in fs:
        if not f.endswith('.cs'):
            continue
        p = os.path.join(d, f)
        t = open(p, encoding='utf-8-sig').read()
        if not CLS.search(t):
            continue
        files += 1
        out = []
        decl_conflict = False
        for code, seg in lex(t):
            if code and DECL.search(seg):
                decl_conflict = True
        for code, seg in lex(t):
            if code:
                seg, n = CLS.subn(r'\1MonoCached', seg)
                classes += n
                if not decl_conflict:
                    seg = re.sub(r'(?<![\w.])transform\b(?!\s*\()', 'TransformCached', seg)
                    seg = re.sub(r'(?<![\w.])gameObject\b(?!\s*\()', 'GameObjectCached', seg)
                seg = HOOK.sub(lambda m: m.group(1) + 'public override void ' + m.group(2) + '()', seg)
            out.append(seg)
        nt = ''.join(out)
        if 'using SketchEngine.Mono;' not in nt:
            nt = 'using SketchEngine.Mono;\n' + nt
        print(('conflict ' if decl_conflict else '') + os.path.relpath(p, cfg.PROJECT_ROOT))
        if apply and nt != t:
            open(p, 'w', encoding='utf-8', newline='').write(nt)
            changed_files += 1
print('files', files, 'classes', classes, 'written', changed_files)
