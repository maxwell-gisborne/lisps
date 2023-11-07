#!/bin/env python

# -- ADDED: --
#  - the \logging, \ast, and \stack controll tokens
#  - the anatation system
#  - added strings
#  - split atom
#  - basic pyeval

# Have scope be something you can pass around,
# as a dynamicaly built namespace, and a replacement for objects

# tail call elminination and recursion optimisation
# (define fact (lambda (n) (cond (= n 1) n True (* n (fact (- n 1))))))
# (fact 425) ok (fact 425) exseads recursion limit
# (define fact-2 (lambda (n acc)
#                 (cond (= n 1) acc True (fact-2 (- n 1) (* acc n)))))
# (fact-2 595 1) ok (fact-2 596 1) exseads recursion limit


import readline
from pathlib import Path
import regex_spm as rem

py_eval = eval

LOGGING = False


def log(*args, **kwargs):
    if LOGGING:
        print(*args, **kwargs)


def N_at_a_time(N):
    def generator(iter):
        N = 2
        c = 0
        buf = []
        for i in iter:
            c += 1
            buf.append(i)
            if c == N:
                c = 0
                yield tuple(buf)
                buf = []
    return generator


two_at_a_time = N_at_a_time(2)


def read(string: str):
    return build_ast(tokenize(wordify(string)))


def wordify(string: str):
    class Mode:
        normal = 0
        quote = 1

    buffer = ''
    quote_string = None
    mode = Mode.normal
    for key in string:
        match mode:
            case Mode.normal:
                if key in {' ', '\n', '\t'}:
                    if buffer != '':
                        yield buffer
                        buffer = ''
                elif key in {'(', ')'}:
                    if buffer != '':
                        yield buffer
                        buffer = ''
                    yield key
                elif key in {'"', "'"}:
                    if buffer != '':
                        yield buffer
                    quote_string = key
                    mode = Mode.quote
                else:
                    buffer += key
            case Mode.quote:
                if key == quote_string:
                    yield '"' + buffer + '"'
                    buffer = ''
                    mode = Mode.normal
                else:
                    buffer += key

    else:
        if buffer != '':
            yield buffer


def tokenize(words):
    for word in words:
        match rem.fullmatch_in(word):
            case r'\(':
                yield ('bracket', 'open')
            case r'\)':
                yield ('bracket', 'close')
            case r'(True)|(true)':
                yield ('bool', True)
            case r'(False)|(false)':
                yield ('bool', False)
            case r'\d+':
                yield ('intiger', int(word))
            case r'(\d*?\.\d+)|(\d+\.\d*?)':
                a, *b = word.split('.')
                a = '0' if a == '' else a
                b = '0' if len(b) == 0 else ''.join(b)
                word = f'{a}.{b}'
                yield ('decimal', float(word))
            case r'"[^"]*"':
                yield ('string', word[1:-1])
            case r'\\\S+':
                yield ('control', word[1:])
            case _:
                yield ('word', word)


def tuplify(stack):
    return tuple(tuplify(s)
                 if isinstance(s, list) else s
                 for s in stack)


def build_ast(tokens):
    stack = [[]]
    for t in tokens:
        match t:
            case ('bracket', 'open'):
                stack.append(list())
            case ('bracket', 'close'):
                closing_fragment = stack.pop()
                if len(stack) == 0:
                    print('Read Error, unmatched brackets')
                    break
                stack[-1].append(tuple(c for c in closing_fragment))
            case ('intiger', i):
                stack[-1].append(('value', 'intiger', i))
            case ('decimal', f):
                stack[-1].append(('value', 'decimal', f))
            case ('word', w):
                stack[-1].append(w)
            case ('bool', b):
                stack[-1].append(('value', 'bool', b))
            case ('string', string):
                stack[-1].append(('value', 'string', string))

            case ('control', 'ast'):
                print(stack)
            case ('control', 'logging'):
                global LOGGING
                LOGGING = not LOGGING
                print('Logging =', LOGGING)
            case ('control', word):
                stack[-1].append(('control', word))

            case _:
                print('unknown read')

    if len(stack) == 0:
        return ()
    assert len(stack) == 1,  'read error, unclosed perens'

    ast = stack[0]
    if len(ast) > 1:
        return tuple(ast)
    if len(ast) == 1:
        return ast[0]


def eval(expr, e):
    log('EVALING', expr)
    match expr:  # special forms
        case ():
            return ()
        case ('control', 'stack'):
            print(e)
            return ()
        case ('annatation', *tail):
            if len(tail) == 0:
                return ('annatation', ())
            body = tail[-1]
            comments = tail[:-1]
            return ('annatation', *comments, eval(body, e))
        case  ('value', *_) | '+' | '-' | '*' | '/' | 'display' | '=' | 'get-annatation' | 'split-atom' | 'py-call':
            return expr
        case ('cond', *body):
            return apply('cond', body, e)
        case ('if', cond, *branches):
            if len(branches) == 1:
                happy_path, sad_path = branches[1], ()
            elif len(branches) == 2:
                happy_path, sad_path = branches
            else:
                return ('Error', 'if needs 1 conndition and 1 or 2 branches')
            return apply('cond', (
                         cond, happy_path,
                         ('value', 'bool', True), sad_path), e)
        case ('lambda', arglist, *body):
            return ('lambda', arglist, *body)
        case ('let', letlist, *body):
            log('Let', letlist, body)
            e.add({k: eval(v, e) for k, v in letlist})
            for b in body:
                result = eval(b, e)
            e.pop()
            return result
        case ('quote', *a):
            if len(a) != 1:
                return ('Error', 'Quote takes one argument')
            return a[0]
        case ('define', word, value):
            return e.set(word, eval(value, e))
        case ('list', *body):
            return ('list', *(eval(b, e) for b in body))
        case str():
            return e.get(expr) or ('Error', 'unbound variable', expr)
    head, *tail = [eval(s, e) for s in expr]
    return apply(head, tail, e)


def type_of(expr):
    if is_error(expr):
        return expr
    assert expr[0] == 'value', expr
    return expr[1]


def value_of(expr):
    assert expr[0] == 'value', expr
    return expr[2]


def is_error(expr):
    return expr[0] == 'Error'


def apply(func, args, e):
    log('Applying', func, 'TO', args)
    match func:
        case ('Error', *_):
            return (*func, 'from function application')

        case 'get-annatation':
            if len(args) != 1:
                return ('Error', 'get-annatation takes one argument')
            ann = args[0]
            assert len(ann) >= 2, 'Malformed Annatation'
            if ann[0] != 'annatation':
                return ('Error', 'get-annatation called on non-anatation')
            comments = ann[2:]
            return ('list', *comments)

        case 'split-atom':
            if len(args) != 1:
                return ('Error', 'split-atom takes one argument')
            return ('list', *args[0])

        case 'py-call':
            func, *poss_args = args
            py_args = [str(value_of(a)) for a in poss_args]
            try:
                call_line = f'{func}({", ".join(py_args)})'
                log(10*' '+call_line)
                result = py_eval(call_line)
            except Exception as e:
                return ('Error', 'python error:', e)

            match type(result):
                case int(n):
                    return ('value', 'intiger', n)
                case float(f):
                    return ('value', 'decimal', f)
                case str(s):
                    return ('value', 'string', s)
                case bool(b):
                    return ('value', 'bool', b)
                case _:
                    return ('value', 'pyval', result)

        case ('lambda', arglist, *body):
            if len(arglist) != len(args):
                return ('Error', f'Incorrect arity, expected {len(arglist)} recived {len(args)}', (func, args))
            return eval(('let', tuple(zip(arglist, args)), *body), e)

        case '=':
            a, b = args
            t, a_rule, b_rule = equalise_types(type_of(a), type_of(b))
            if is_error(t):
                return (*t, 'in =')
            a = apply_promotion_rule(a_rule, a)
            b = apply_promotion_rule(b_rule, b)
            return ('value', 'bool', value_of(a) == value_of(b))

        case 'cond':
            for cond, body in two_at_a_time(args):
                b = eval(cond, e)
                if type_of(b) != 'bool':
                    return ('Error', 'branshes of cond must eval to bool', b)
                if value_of(b):
                    return eval(body, e)
            return ('Error', 'no condition matched')

        case '+':
            acc = ('value', 'intiger', 0)
            for number in args:
                t, acc_rule, number_rule = equalise_types(type_of(acc), type_of(number))
                acc = apply_promotion_rule(acc_rule, acc)
                value = apply_promotion_rule(number_rule, number)
                acc = ('value', type_of(acc), value_of(acc) + value_of(number))
            return acc

        case '-':
            if len(args) == 0:
                return ('value', 'intiger', 0)

            acc = args[0]
            for number in args[1:]:
                t, acc_rule, number_rule = equalise_types(type_of(acc), type_of(number))
                acc = apply_promotion_rule(acc_rule, acc)
                value = apply_promotion_rule(number_rule, number)
                acc = ('value', type_of(acc), value_of(acc) - value_of(number))
            return acc

        case '*':
            acc = ('value', 'intiger', 1)
            for number in args:
                t, acc_rule, number_rule = equalise_types(type_of(acc), type_of(number))
                acc = apply_promotion_rule(acc_rule, acc)
                value = apply_promotion_rule(number_rule, number)
                acc = ('value', type_of(acc), value_of(acc) * value_of(number))
            return acc

        case '/':
            if len(args) == 0:
                return ('value', 'intiger', 1)

            numerator = args[0]
            if len(args) == 1:
                return numerator

            if is_error(numerator):
                return (*numerator, 'from numerator of division')

            if len(args) == 2:
                denominator = args[1]
            else:
                denominator = apply('*', args[1:], e)

            if is_error(denominator):
                return (*denominator, 'from denominator of division')

            t, denominator_rule, numerator_rule = equalise_types(
                    type_of(denominator), type_of(numerator))

            if is_error(t):
                return (*t, 'from division')

            numerator = apply_promotion_rule(numerator_rule, numerator)
            denominator = apply_promotion_rule(denominator_rule, denominator)

            _, tn, vn = numerator
            _, td, vd = denominator

            if vd == 0:
                return ('Error', 'division by zero')

            if t == 'decimal':
                return ('value', t, vn/vd)

            f, r = divmod(vn, vd)
            if r == 0:
                return ('value', 'intiger', f)
            else:
                return ('value', 'decimal', vn/vd)

        case 'display':
            return display(*args)
        case ():
            return ()
        case _:
            return ('Error', 'Unknown functype', func, args)
    return ()


type_graph = {
        'intiger': [('promotion-rule', 'decimal', lambda v: float(v))],
        'decimal': []
        }


def apply_promotion_rule(rule, value_expr):
    if rule is None:
        return value_expr
    rule_type,  target_type, promotor = rule
    assert rule_type == 'promotion-rule', rule_type
    log('applying promotion', target_type, value_expr)
    return (value_expr[0], target_type, promotor(value_expr[2]))


def equalise_types(t0, t1):
    if is_error(t0):
        return t0, (), ()
    if is_error(t1):
        return t1, (), ()
    if (t := t0) == t1:
        return t, None, None
    log('Equalising Types:', t0, t1)
    solutions = []
    t0_rules = type_graph.get(t0) or []
    t1_rules = type_graph.get(t1) or []
    for rule in t0_rules:
        if t1 == rule[1]:
            solutions.append((t, rule, None))
    for rule in t1_rules:
        if t0 == rule[1]:
            solutions.append((t, None, rule))
    if len(solutions) == 0:
        return ('Error', f'No type promotion solutions found between {t0} and {t1}'), (), ()

    t, r0, r1 = solutions[0]
    return t, r0, r1


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
        case ('annatation', *tail):
            if len(tail) == 0:
                line += 'emmpty annatation'
            else:
                body = tail[-1]
                comments = tail[:-1]
                line += display(body)
                if (c := len(comments)) > 0:
                    line += '*'
                    if c > 1:
                        line += str(c)
        case ('value', type, value):
            line += str(value) + ' [' + type + ']'
        case ('list', *body):
            line += '['
            line += ', '.join([display(e) for e in expr[1:]])
            line += ']'
        case str():
            line += expr
        case tuple():
            line += '(' + ' '.join([display(e) for e in expr]) + ')'
        case _:
            line += str(expr)
    return line


if __name__ == '__main__':
    histfile = Path('.lisp-3.histfile')
    histfile.touch()
    readline.read_history_file(histfile)
    readline.set_history_length(10000)
    try:
        e = Enviroment()
        while True:
            inp = read(input('> '))
            if inp is not None:
                val = eval(inp, e)
                print(display(val))
    finally:
        readline.write_history_file(histfile)
