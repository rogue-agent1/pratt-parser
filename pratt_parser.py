#!/usr/bin/env python3
"""Pratt parser — top-down operator precedence parsing.

Elegant expression parsing technique by Vaughan Pratt (1973). Handles
prefix/infix/postfix operators, precedence, associativity, grouping,
function calls, ternary operators, and indexing.

Usage: python pratt_parser.py [EXPR] [--test]
"""

import sys, re
from dataclasses import dataclass
from typing import Any

# --- AST ---
@dataclass
class Num: value: float
@dataclass
class Str: value: str
@dataclass
class Var: name: str
@dataclass
class Unary: op: str; operand: Any
@dataclass
class Binary: op: str; left: Any; right: Any
@dataclass
class Ternary: cond: Any; then_: Any; else_: Any
@dataclass
class Call: func: Any; args: list
@dataclass
class Index: obj: Any; idx: Any

# --- Tokenizer ---
TOKEN_RE = re.compile(r'''
    (\d+\.?\d*) |       # number
    ("(?:[^"\\]|\\.)*") | # string
    ([a-zA-Z_]\w*) |    # identifier
    (<=|>=|==|!=|&&|\|\||[+\-*/%^<>!()=,\[\]?:]) | # operators
    (\s+)                # whitespace
''', re.VERBOSE)

def tokenize(source):
    tokens = []
    for m in TOKEN_RE.finditer(source):
        num, string, ident, op, ws = m.groups()
        if ws: continue
        if num: tokens.append(('NUM', float(num)))
        elif string: tokens.append(('STR', string[1:-1]))
        elif ident: tokens.append(('ID', ident))
        elif op: tokens.append(('OP', op))
    tokens.append(('EOF', None))
    return tokens

# --- Parser ---
class PrattParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def peek(self):
        return self.tokens[self.pos]
    
    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok
    
    def expect(self, kind, value=None):
        tok = self.advance()
        if tok[0] != kind or (value is not None and tok[1] != value):
            raise SyntaxError(f"Expected ({kind}, {value}), got {tok}")
        return tok
    
    def parse(self, rbp=0):
        """Parse expression with right binding power rbp."""
        left = self.nud()
        while rbp < self.lbp():
            left = self.led(left)
        return left
    
    def lbp(self):
        """Left binding power of current token."""
        tok = self.peek()
        if tok[0] == 'OP':
            return {
                '?': 5, '||': 10, '&&': 15,
                '==': 20, '!=': 20, '<': 25, '>': 25, '<=': 25, '>=': 25,
                '+': 30, '-': 30, '*': 40, '/': 40, '%': 40,
                '^': 50, '(': 60, '[': 60,
            }.get(tok[1], 0)
        return 0
    
    def nud(self):
        """Null denotation — prefix."""
        tok = self.advance()
        if tok[0] == 'NUM':
            return Num(tok[1])
        if tok[0] == 'STR':
            return Str(tok[1])
        if tok[0] == 'ID':
            return Var(tok[1])
        if tok[0] == 'OP' and tok[1] == '(':
            expr = self.parse(0)
            self.expect('OP', ')')
            return expr
        if tok[0] == 'OP' and tok[1] in ('-', '!'):
            operand = self.parse(45)  # higher than binary
            return Unary(tok[1], operand)
        raise SyntaxError(f"Unexpected token: {tok}")
    
    def led(self, left):
        """Left denotation — infix/postfix."""
        tok = self.advance()
        if tok[0] == 'OP':
            if tok[1] == '?':
                then_ = self.parse(0)
                self.expect('OP', ':')
                else_ = self.parse(4)  # right-assoc
                return Ternary(left, then_, else_)
            if tok[1] == '(':
                # Function call
                args = []
                if self.peek() != ('OP', ')'):
                    args.append(self.parse(0))
                    while self.peek() == ('OP', ','):
                        self.advance()
                        args.append(self.parse(0))
                self.expect('OP', ')')
                return Call(left, args)
            if tok[1] == '[':
                idx = self.parse(0)
                self.expect('OP', ']')
                return Index(left, idx)
            if tok[1] == '^':
                # Right-associative
                right = self.parse(49)
                return Binary(tok[1], left, right)
            # Left-associative binary
            bp = {
                '||': 10, '&&': 15,
                '==': 20, '!=': 20, '<': 25, '>': 25, '<=': 25, '>=': 25,
                '+': 30, '-': 30, '*': 40, '/': 40, '%': 40,
            }.get(tok[1], 30)
            right = self.parse(bp)
            return Binary(tok[1], left, right)
        raise SyntaxError(f"Unexpected infix: {tok}")

def parse(source):
    tokens = tokenize(source)
    parser = PrattParser(tokens)
    return parser.parse()

# --- Evaluator ---
def evaluate(node, env=None):
    if env is None:
        env = {}
    if isinstance(node, Num): return node.value
    if isinstance(node, Str): return node.value
    if isinstance(node, Var): return env.get(node.name, 0)
    if isinstance(node, Unary):
        val = evaluate(node.operand, env)
        if node.op == '-': return -val
        if node.op == '!': return 0 if val else 1
    if isinstance(node, Binary):
        l = evaluate(node.left, env)
        r = evaluate(node.right, env)
        ops = {'+': lambda: l+r, '-': lambda: l-r, '*': lambda: l*r,
               '/': lambda: l/r if r else 0, '%': lambda: l%r if r else 0,
               '^': lambda: l**r, '<': lambda: int(l<r), '>': lambda: int(l>r),
               '<=': lambda: int(l<=r), '>=': lambda: int(l>=r),
               '==': lambda: int(l==r), '!=': lambda: int(l!=r),
               '&&': lambda: int(l and r), '||': lambda: int(l or r)}
        return ops.get(node.op, lambda: 0)()
    if isinstance(node, Ternary):
        return evaluate(node.then_, env) if evaluate(node.cond, env) else evaluate(node.else_, env)
    if isinstance(node, Call):
        import math as m
        builtins = {'sqrt': m.sqrt, 'abs': abs, 'min': min, 'max': max, 'sin': m.sin, 'cos': m.cos}
        if isinstance(node.func, Var) and node.func.name in builtins:
            args = [evaluate(a, env) for a in node.args]
            return builtins[node.func.name](*args)
    return 0

# --- Tests ---
import math

def test_arithmetic():
    assert evaluate(parse("2 + 3 * 4")) == 14
    assert evaluate(parse("(2 + 3) * 4")) == 20
    assert evaluate(parse("10 - 2 - 3")) == 5  # left-assoc

def test_power():
    assert evaluate(parse("2 ^ 3 ^ 2")) == 512  # right-assoc: 2^(3^2)
    assert evaluate(parse("2 ^ 10")) == 1024

def test_unary():
    assert evaluate(parse("-5 + 3")) == -2
    assert evaluate(parse("!0")) == 1
    assert evaluate(parse("!1")) == 0

def test_comparison():
    assert evaluate(parse("3 < 5")) == 1
    assert evaluate(parse("5 <= 5")) == 1
    assert evaluate(parse("3 == 3")) == 1
    assert evaluate(parse("3 != 4")) == 1

def test_ternary():
    assert evaluate(parse("1 ? 10 : 20")) == 10
    assert evaluate(parse("0 ? 10 : 20")) == 20

def test_function_call():
    assert evaluate(parse("sqrt(16)")) == 4.0
    assert evaluate(parse("max(3, 7)")) == 7
    assert abs(evaluate(parse("sin(0)")) - 0) < 1e-10

def test_variables():
    assert evaluate(parse("x + y * 2"), {"x": 10, "y": 5}) == 20

def test_complex():
    assert evaluate(parse("2 + 3 * 4 ^ 2 - 1")) == 49  # 2 + 3*16 - 1

def test_logical():
    assert evaluate(parse("1 && 1")) == 1
    assert evaluate(parse("1 && 0")) == 0
    assert evaluate(parse("0 || 1")) == 1

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--test" in args or not args:
        test_arithmetic()
        test_power()
        test_unary()
        test_comparison()
        test_ternary()
        test_function_call()
        test_variables()
        test_complex()
        test_logical()
        print("All tests passed!")
    else:
        expr = " ".join(args)
        tree = parse(expr)
        print(f"AST: {tree}")
        print(f"Result: {evaluate(tree)}")
