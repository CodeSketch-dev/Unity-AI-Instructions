#!/usr/bin/env python
"""Rewrite test subscriptions to removed facade events (`w.EggBroken += r => x = r;`) into Dig_TestBus.On<Event>(w, e => ...).

usage: python tests_to_bus.py <errors.txt>     (lines copied from the Unity console: path(line,col): error CS1061: 'Dig_World_X' does not contain a definition for 'Name' ...)
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EV_DIR = os.path.join(ROOT, 'Assets', '_Game', 'Scripts', 'Event', 'Dig')


def props_of(event_name):
    for d, _, fs in os.walk(EV_DIR):
        if event_name + '.cs' in fs:
            t = open(os.path.join(d, event_name + '.cs'), encoding='utf-8').read()
            return [m.group(1) for m in re.finditer(r'public \S+ (\w+) \{ get; \}', t) if m.group(1) != 'Source']
    return None


def convert(stmt_rhs, props, ev):
    rhs = stmt_rhs.strip()
    m = re.match(r'^(?:\((?P<ps>[^)]*)\)|(?P<p>\w+))\s*=>\s*(?P<body>.*)$', rhs, re.S)
    if m:
        ps = [x.strip() for x in (m.group('ps') if m.group('ps') is not None else m.group('p')).split(',') if x.strip()]
        body = m.group('body').strip()
        decl = ''.join('var %s = e.%s; ' % (n, props[i]) for i, n in enumerate(ps) if i < len(props) and n != '_' and not re.fullmatch(r'_\d*', n))
        if body.startswith('{'):
            return 'e => { %s%s' % (decl, body[1:])
        return 'e => { %s%s; }' % (decl, body)
    # method group: handler(args...)
    args = ', '.join('e.' + p for p in props)
    return 'e => %s(%s)' % (rhs, args)


def main():
    errs = re.findall(r'([^\s(\n][^()\n]*\.cs)\((\d+),(\d+)\).*?\'(Dig_World_\w+)\' does not contain a definition for \'(\w+)\'', open(sys.argv[1], encoding='utf-8').read())
    by_file = {}
    for path, ln, col, cls, name in errs:
        by_file.setdefault(path, []).append((int(ln), int(col), cls, name))
    for path, items in by_file.items():
        p = os.path.join(ROOT, path.replace('\\\\', os.sep).replace('\\', os.sep))
        lines = open(p, encoding='utf-8-sig').read().split('\n')
        for ln, col, cls, name in sorted(items, key=lambda x: (x[0], -x[1])):
            line = lines[ln - 1]
            ev = 'Event_Dig_%s_%s' % (cls.replace('Dig_', '', 1), name)
            props = props_of(ev)
            if props is None:
                print('no event', ev)
                continue
            start = col - 1
            m = re.search(r'(\w+)\.%s\s*\+=\s*' % name, line[max(0, start - 40):])
            # locate the match nearest to col
            ms = [mm for mm in re.finditer(r'(\w+)\.%s\s*\+=\s*' % name, line) if abs(mm.start(1) - (start - len(mm.group(1)) - 1)) <= 1 or mm.start() <= start <= mm.end()]
            if not ms:
                print('cannot parse', path, ln, line.strip())
                continue
            mm = ms[0]
            rest = line[mm.end():]
            # statement ends at the first ';' at depth 0
            depth, end = 0, None
            for i, c in enumerate(rest):
                if c in '({[':
                    depth += 1
                elif c in ')}]':
                    depth -= 1
                elif c == ';' and depth == 0:
                    end = i
                    break
            if end is None:
                print('multi-line handler, fix by hand', path, ln)
                continue
            rhs = rest[:end]
            new = 'Dig_TestBus.On<%s>(%s, %s);' % (ev, mm.group(1), convert(rhs, props, ev))
            line = line[:mm.start()] + new + rest[end + 1:]
            lines[ln - 1] = line
        open(p, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
        print('rewrote', path)


if __name__ == '__main__':
    main()
