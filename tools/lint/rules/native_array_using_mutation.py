"""Narrow lexical binding check; no C# semantic/type-inference dependency."""
import re
from engine import Rule

_LITERALS = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|\$*(?P<raw>"{3,})[\s\S]*?(?P=raw)|(?:\$@|@\$|@)"(?:[^"]|"")*"|\$?"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
_TOKENS = re.compile(r'@?[A-Za-z_]\w*|\+\+|--|<<=|>>=|\?\?=|[+*/%&|^\-]=|==|!=|=>|::|[^\s]')
_IDENT = re.compile(r'@?[A-Za-z_]\w*\Z')
_ASSIGN = {'=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=', '??=', '++', '--'}


def _mask(text):
    return _LITERALS.sub(lambda m: ''.join('\n' if c == '\n' else ' ' for c in m.group()), text)


def _end(tokens, start, opening, closing):
    depth = 0
    for i in range(start, len(tokens)):
        if tokens[i] == opening:
            depth += 1
        elif tokens[i] == closing:
            depth -= 1
            if depth == 0:
                return i
    return None


def _type(tokens, start):
    if start >= len(tokens) or not _IDENT.fullmatch(tokens[start]):
        return None
    name, i = tokens[start].lstrip('@'), start + 1
    while i + 1 < len(tokens) and tokens[i] in ('.', '::') and _IDENT.fullmatch(tokens[i + 1]):
        name, i = tokens[i + 1].lstrip('@'), i + 2
    if i < len(tokens) and tokens[i] == '<':
        last = _end(tokens, i, '<', '>')
        if last is None:
            return None
        i = last + 1
    return name, i


def _binding_names(tokens, name_index):
    names, closing = [tokens[name_index].lstrip('@')], []
    pairs = {'(': ')', '[': ']', '{': '}', '<': '>'}
    for i in range(name_index + 2, len(tokens)):
        token = tokens[i]
        if token in pairs:
            closing.append(pairs[token])
        elif closing and token == closing[-1]:
            closing.pop()
        elif not closing:
            if token in (';', ')'):
                break
            if token == ',' and i + 2 < len(tokens) and _IDENT.fullmatch(tokens[i + 1]) and tokens[i + 2] == '=':
                names.append(tokens[i + 1].lstrip('@'))
    return names


def scan(text):
    masked = _mask(text)
    matches = list(_TOKENS.finditer(masked))
    tokens = [m.group() for m in matches]
    scopes, pending, temporary, found = [{}], {}, [], []

    def lookup(name):
        name = name.lstrip('@')
        for end, bindings in reversed(temporary):
            if end >= i and name in bindings:
                return bindings[name]
        for bindings in reversed(scopes):
            if name in bindings:
                return bindings[name]
        return False, False

    def declaration(start, readonly):
        parsed = _type(tokens, start)
        if parsed is None:
            return None
        kind, name_index = parsed
        if name_index + 1 >= len(tokens) or not _IDENT.fullmatch(tokens[name_index]) or tokens[name_index + 1] != '=':
            return None
        is_array = kind == 'NativeArray'
        value = name_index + 2
        if kind == 'var' and value < len(tokens):
            if tokens[value] == 'new':
                inferred = _type(tokens, value + 1)
                is_array = inferred is not None and inferred[0] == 'NativeArray'
            elif _IDENT.fullmatch(tokens[value]):
                is_array = lookup(tokens[value])[0]
        return name_index, (is_array, readonly and is_array)

    i = 0
    while i < len(tokens):
        token = tokens[i]
        temporary[:] = [(end, binding) for end, binding in temporary if end >= i]
        if token == '{':
            scopes.append(pending.pop(i, {}))
        elif token == '}':
            if len(scopes) > 1:
                scopes.pop()
        elif token == 'using':
            parenthesized = i + 1 < len(tokens) and tokens[i + 1] == '('
            start = i + (2 if parenthesized else 1)
            declared = declaration(start, True)
            if declared:
                name_index, info = declared
                binding = {name: info for name in _binding_names(tokens, name_index)}
                if parenthesized:
                    last = _end(tokens, i + 1, '(', ')')
                    if last is not None and last + 1 < len(tokens):
                        if tokens[last + 1] == '{':
                            pending[last + 1] = binding
                        else:
                            end = next((j for j in range(last + 1, len(tokens)) if tokens[j] == ';'), len(tokens))
                            temporary.append((end, binding))
                else:
                    scopes[-1].update(binding)
                i = name_index + 1
                continue
        elif _IDENT.fullmatch(token) and (i == 0 or tokens[i - 1] not in ('.', '::')):
            declared = declaration(i, False)
            if declared:
                name_index, info = declared
                scopes[-1][tokens[name_index].lstrip('@')] = info
                i = name_index + 1
                continue
            if lookup(token)[1] and i + 1 < len(tokens) and tokens[i + 1] == '[':
                last = _end(tokens, i + 1, '[', ']')
                mutation = last is not None and last + 1 < len(tokens) and tokens[last + 1] in _ASSIGN
                if mutation or (i > 0 and tokens[i - 1] in ('++', '--')):
                    found.append(masked.count('\n', 0, matches[i].start()) + 1)
        i += 1
    return found


RULE = Rule(
    id='native-array-using-mutation', pattern=r'(?!)',
    why='A using NativeArray is readonly (CS1654); use a mutable local with try/finally disposal before indexed writes.',
    skill='native-array-using-mutation', exclude_dirs=(), scan=scan,
)
