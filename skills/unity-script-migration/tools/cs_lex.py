"""Tiny C# lexer: split source into (is_code, text) segments.

Strings, char literals and comments are not code. Interpolation holes ({...} inside $"...") are code, including nested strings.
"""
import re

CHAR_RE = re.compile(r"'(?:\\.[^'\n]{0,8}|[^'\\\n])'")


def lex(t):
    out = []
    n = len(t)

    def scan(i, until_brace):
        """Scan code from i. If until_brace, stop at the matching '}' (returns its index). Returns (index, segments)."""
        segs = []
        buf = []
        depth = 0

        def flush():
            if buf:
                segs.append((True, ''.join(buf)))
                buf.clear()

        while i < n:
            c = t[i]
            if t.startswith('//', i):
                flush()
                j = t.find('\n', i)
                j = n if j < 0 else j
                segs.append((False, t[i:j]))
                i = j
                continue
            if t.startswith('/*', i):
                flush()
                j = t.find('*/', i + 2)
                j = n if j < 0 else j + 2
                segs.append((False, t[i:j]))
                i = j
                continue
            if c == "'":
                m = CHAR_RE.match(t, i)
                if m:
                    flush()
                    segs.append((False, m.group(0)))
                    i = m.end()
                    continue
            prefix = None
            if t.startswith('$@"', i) or t.startswith('@$"', i):
                prefix = (True, True, 3)
            elif t.startswith('@"', i):
                prefix = (True, False, 2)
            elif t.startswith('$"', i):
                prefix = (False, True, 2)
            elif c == '"':
                prefix = (False, False, 1)
            if prefix:
                verbatim, interp, ln = prefix
                flush()
                i, parts = string(i, verbatim, interp, ln)
                segs.extend(parts)
                continue
            if until_brace:
                if c == '{':
                    depth += 1
                elif c == '}':
                    if depth == 0:
                        flush()
                        return i, segs
                    depth -= 1
            buf.append(c)
            i += 1
        flush()
        return i, segs

    def string(i, verbatim, interp, ln):
        parts = []
        buf = [t[i:i + ln]]
        i += ln
        while i < n:
            c = t[i]
            if verbatim:
                if c == '"':
                    if i + 1 < n and t[i + 1] == '"':
                        buf.append('""')
                        i += 2
                        continue
                    buf.append('"')
                    i += 1
                    break
            else:
                if c == '\\':
                    buf.append(t[i:i + 2])
                    i += 2
                    continue
                if c == '"' or c == '\n':
                    buf.append(c if c == '"' else '')
                    i += 1 if c == '"' else 0
                    break
            if interp and c == '{':
                if i + 1 < n and t[i + 1] == '{':
                    buf.append('{{')
                    i += 2
                    continue
                parts.append((False, ''.join(buf) + '{'))
                buf = []
                j, inner = scan(i + 1, True)
                parts.extend(inner)
                buf = ['}']
                i = j + 1
                continue
            if interp and c == '}' and i + 1 < n and t[i + 1] == '}':
                buf.append('}}')
                i += 2
                continue
            buf.append(c)
            i += 1
        parts.append((False, ''.join(buf)))
        return i, parts

    _, segs = scan(0, False)
    return segs


if __name__ == '__main__':
    sample = 'int a = 1; // DigAds\nvar s = $"x {Foo(a ? "DigAds" : "b")} DigAds {DigAds.X}"; DigAds.Y(); char c=\'"\'; var v=@"DigAds ""q"" "; /* DigAds */ DigAds.Z();'
    for code, x in lex(sample):
        print(code, repr(x))
    assert ''.join(x for _, x in lex(sample)) == sample
