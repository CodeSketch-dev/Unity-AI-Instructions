#!/usr/bin/env python
"""Convert the public `event Action<...>` members of one facade class to StaticBus events.

usage: python events_to_bus.py <facade file> <EventFolderName> [--apply]
 - writes <eventFolder>/<EventFolderName>/Event_<Prefix>_<Class>_<Name>.cs (payload names come from the trailing comment)
 - removes the declarations, turns `Name?.Invoke(a, b)` into `StaticBus<E>.Post(new E(a, b))`
 - rewrites method-group subscribers (`x.Name += Handler;` / `-=`) in other non-test files to StaticBus Subscribe/Unsubscribe and
   adds an adapter `void StaticBus_Handler(E e) => Handler(e.P1, ...)` above the handler definition
 - receivers must be variables/properties/fields declared with the facade type (so core-class events are never touched)
Lambdas and handlers defined in other partial files are reported; fix those by hand (compile errors list them too).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import migration_config as cfg

SCRIPTS = os.path.join(cfg.game_root, 'Scripts')
P = cfg.prefix
EV_DECL = re.compile(r'^(?P<ind>[ \t]*)public event (?:System\.)?Action(?:<(?P<types>[^;]*?)>)?\s+(?P<names>[\w, ]+);(?P<cmt>[ \t]*//[^\n]*)?[ \t]*\n', re.M)


def split_top(s):
    parts, depth, cur = [], 0, ''
    for c in s:
        if c == '<':
            depth += 1
        elif c == '>':
            depth -= 1
        if c == ',' and depth == 0:
            parts.append(cur.strip())
            cur = ''
        else:
            cur += c
    if cur.strip():
        parts.append(cur.strip())
    return parts


def pascal(w):
    w = re.sub(r'\(.*?\)', '', w)
    ws = re.findall(r'[A-Za-z0-9]+', w)
    return ''.join(x[:1].upper() + x[1:] for x in ws) or 'Value'


def read(p):
    return open(p, encoding='utf-8-sig').read()


def main():
    facade_path = os.path.abspath(sys.argv[1])
    folder = sys.argv[2]
    apply = '--apply' in sys.argv
    src = read(facade_path)
    cls = re.search(r'\bclass\s+(\w+)', src).group(1)
    short = cls.replace(P + '_', '', 1)            # e.g. World_Steal
    events = []
    for m in EV_DECL.finditer(src):
        types = split_top(m.group('types')) if m.group('types') else []
        cmt = (m.group('cmt') or '').strip()[2:].split(';')[0].split(' - ')[0]
        names = [n.strip() for n in m.group('names').split(',')]
        words = [pascal(x) for x in cmt.split(',')] if cmt and len(cmt.split(',')) == len(types) else []
        words = [w if len(re.findall('[A-Z][a-z0-9]*', w)) <= 2 else 'Value' for w in words]
        for n in names:
            props = []
            for i, t in enumerate(types):
                nm = words[i] if i < len(words) else ('Value' if len(types) == 1 else 'Arg' + str(i + 1))
                if nm in [n] + [p[1] for p in props]:
                    nm += str(i + 1)
                props.append((t, nm))
            events.append((n, props))
    print(cls, 'events:', [(n, [p[1] for p in ps]) for n, ps in events])
    evname = lambda n: cfg.event_prefix + '%s_%s' % (short, n)
    # all non-test sources
    files = {}
    for d, _, fs in os.walk(SCRIPTS):
        for f in fs:
            if f.endswith('.cs'):
                files[os.path.join(d, f)] = read(os.path.join(d, f))
    receivers = set()
    for t in files.values():
        for m in re.finditer(r'\b' + cls + r'\??\s+(\w+)', t):
            receivers.add(m.group(1))
    for t in files.values():       # properties typed as the facade, e.g. `public <Prefix>_World_Steal Steal { get; ... }` are covered above
        pass
    print('receivers:', sorted(receivers))
    report = []
    new_files = {}
    for n, props in events:
        body = ['using SketchEngine.Patterns.Observer;', '', 'namespace ' + cfg.namespace, '{', '    public class %s : IEvent, %s' % (evname(n), cfg.source_interface), '    {', '        public object Source { get; }']
        for t, nm in props:
            body.append('        public %s %s { get; }' % (t, nm))
        body.append('')
        body.append('        public %s(%s)' % (evname(n), ', '.join(['object source'] + ['%s %s' % (t, nm[:1].lower() + nm[1:]) for t, nm in props])))
        body.append('        {')
        body.append('            Source = source;')
        for t, nm in props:
            body.append('            %s = %s;' % (nm, nm[:1].lower() + nm[1:]))
        body.append('        }')
        body += ['    }', '}', '']
        new_files[os.path.join(cfg.game_root, cfg.event_folder.replace('/', os.sep), folder, evname(n) + '.cs')] = '\n'.join(body)
    # facade rewrite
    nsrc = EV_DECL.sub('', src)
    for n, props in events:
        def inv(m):
            args = m.group(1).strip()
            return 'StaticBus<%s>.Post(new %s(%s))' % (evname(n), evname(n), ('this, ' + args) if args else 'this')
        nsrc = re.sub(r'\b' + n + r'\?\.Invoke\(([^;]*?)\)(?=\s*[;\)\}])', inv, nsrc)
        if re.search(r'\b' + n + r'\?\.Invoke', nsrc):
            report.append('facade: leftover Invoke of ' + n)
    if 'using SketchEngine.Patterns.Observer;' not in nsrc:
        nsrc = 'using SketchEngine.Patterns.Observer;\n' + nsrc
    edits = {facade_path: nsrc}
    # consumers
    for p, t in files.items():
        if p == facade_path or os.sep + 'Tests' + os.sep in p:
            continue
        nt = t
        adapters = {}
        for n, props in events:
            pat = re.compile(r'\b(?:' + '|'.join(map(re.escape, sorted(receivers))) + r')\??\.' + n + r'\s*([+-])=\s*(\w+)\s*;') if receivers else None
            if not pat:
                continue
            def rep(m):
                op, h = m.group(1), m.group(2)
                adapters[(n, h)] = props
                return 'StaticBus<%s>.%s(StaticBus_%s);' % (evname(n), 'Subscribe' if op == '+' else 'Unsubscribe', h)
            nt = pat.sub(rep, nt)
        if nt != t:
            for (n, h), props in adapters.items():
                dm = re.search(r'^([ \t]*)(?:public |internal |private )?void ' + h + r'\(', nt, re.M)
                call = '%s(%s)' % (h, ', '.join('e.' + nm for _, nm in props))
                adapter = '%svoid StaticBus_%s(%s e) => %s;\n\n' % (dm.group(1) if dm else '        ', h, evname(n), call)
                if dm and ('void StaticBus_' + h + '(') not in nt:
                    nt = nt[:dm.start()] + adapter + nt[dm.start():]
                elif not dm:
                    report.append('%s: handler %s not defined in this file; add adapter by hand' % (os.path.relpath(p, SCRIPTS), h))
            if 'using SketchEngine.Patterns.Observer;' not in nt:
                nt = 'using SketchEngine.Patterns.Observer;\n' + nt
            edits[p] = nt
    for p in edits:
        print('edit', os.path.relpath(p, SCRIPTS))
    for r in report:
        print('REPORT', r)
    if apply:
        for p, t in new_files.items():
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'w', encoding='utf-8', newline='').write(t)
        for p, t in edits.items():
            open(p, 'w', encoding='utf-8', newline='').write(t)
        print('applied', len(new_files), 'event classes')


if __name__ == '__main__':
    main()
