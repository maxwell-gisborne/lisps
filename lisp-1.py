import regex_spm as rem


def read(string: str):
    words = string.replace('(', ' ( ').replace(')', ' ) ').split()
    tokens = []
    for word in words:
        match rem.fullmatch_in(word):
            case r'\(':
                tokens.append(('bracket', 'open'))
            case r'\)':
                tokens.append(('bracket', 'close'))
            case r'\d+':
                tokens.append(('intiger', int(word)))
            case r'\d*?.\d+':
                tokens.append(('decimal', float(word)))
            case r'\S+':
                tokens.append(('word', word))
            case _:
                print('unknown')

    stack = []
    current = []
    for t in tokens:
        match t:
            case ('bracket', 'open'):
                stack.append(current)
                current = list()
            case ('bracket', 'close'):
                stack[-1].append(current)
                current = stack.pop()
            case ('intiger', i):
                current.append(('value', 'intiger', i))
            case ('decimal', f):
                current.append(('value', 'decimal', f))
            case ('word', w):
                current.append(w)

    def tuplify(stack):
        return tuple(tuplify(s)
                     if isinstance(s, list) else s
                     for s in stack)
    current = tuplify(current)

    if len(stack) != 0:
        print('remaining elements on read stack?')
    if len(current) == 1:
        return current[0]
    return current


def eval(expr, e):
    # print('EVALING', expr)
    match expr:  # special forms
        case ():
            return ()
        case ('value', *_) | '+' | '*':
            return expr
        case ('lambda', arglist, *body):
            return ('lambda', arglist, *body)
        case ('let', letlist, *body):
            # print('Let', letlist, body)
            e.add({k: eval(v, e) for k, v in letlist})
            for b in body:
                result = eval(b, e)
            e.pop()
            return result
        case ('quote', *a):
            return a
        case ('define', word, value):
            return e.set(word, eval(value, e))
        case ('cond', *_):
            pass
        case ('list', *body):
            return ('list', *(eval(b, e) for b in body))
        case str():
            return e.get(expr)
    head, *tail = [eval(s, e) for s in expr]
    return apply(head, tail, e)


def apply(func, args, e):
    #print('Applying', func, 'TO', args)
    match func:
        case ('lambda', arglist, *body):
            if len(arglist) != len(args):
                return ('Error', f'Incorrect arity, expected {len(arglist)} recived {len(args)}', (func, args))
            return eval(('let', tuple(zip(arglist, args)), *body), e)

        case '+':
            acc = 0
            t = 'intiger'
            for _, type, value in args:
                assert type in {'intiger', 'decimal'}
                if type == 'decimal':
                    t = 'decimal'
                acc += value
            return ('value', t, acc)

        case '*':
            acc = 1
            t = 'intiger'
            for _, type, value in args:
                assert type in {'intiger', 'decimal'}
                if type == 'decimal':
                    t = 'decimal'
                acc *= value
            return ('value', t, acc)

        case _:
            return ('Error', 'Unknown functype', func, args)
    return ()


class Enviroment:
    def __init__(self):
        self.stack = []
        self.add()

    def get(self, key):
        for scope in reversed(self.stack):
            val = scope.get(key)
            if val is not None:
                return val
        return None

    def set(self, key, val):
        self.stack[-1][key] = val
        return val

    def add(self, scope=None):
        self.stack.append(scope or dict())

    def pop(self):
        return self.stack.pop()

    def __repr__(self):
        lines = ['Enviroment:']
        lines.append(len(lines[-1])*'-')
        for sn, s in enumerate(self.stack):
            lines.append('\tScope: ' + str(sn))
            for k, v in s.items():
                lines.append(f'\t\t{k}: {v}')
        return '\n'.join(lines)


def display(expr):
    line = ''
    match expr:
        case ('value', type, value):
            line += str(value) + ' [' + type + ']'
        case _:
            line += str(expr)
    return line


e = Enviroment()
while True:
    inp = read(input('> '))
    val = eval(inp, e)
    print(display(val))
