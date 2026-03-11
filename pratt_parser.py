#!/usr/bin/env python3
"""Pratt Parser — top-down operator precedence parsing (Vaughan Pratt, 1973)."""
import re, sys

class Token:
    __slots__ = ('type', 'value')
    def __init__(self, t, v): self.type, self.value = t, v
    def __repr__(self): return f"Token({self.type}, {self.value!r})"

def tokenize(text):
    for m in re.finditer(r'\d+\.?\d*|[+\-*/^()!]|\w+', text):
        s = m.group()
        if re.match(r'\d', s): yield Token('NUM', float(s))
        elif s in '+-*/^()!': yield Token(s, s)
        else: yield Token('ID', s)
    yield Token('END', None)

class PrattParser:
    def __init__(self, tokens):
        self.tokens = iter(tokens); self.current = next(self.tokens)
    def advance(self):
        self.current = next(self.tokens); return self.current
    def parse(self, rbp=0):
        t = self.current; self.advance()
        left = self.nud(t)
        while rbp < self.lbp(self.current):
            t = self.current; self.advance()
            left = self.led(t, left)
        return left
    def nud(self, token):
        if token.type == 'NUM': return ('num', token.value)
        if token.type == 'ID': return ('var', token.value)
        if token.value == '(':
            expr = self.parse(0)
            assert self.current.value == ')'; self.advance()
            return expr
        if token.value == '-': return ('neg', self.parse(70))
        raise SyntaxError(f"Unexpected {token}")
    def led(self, token, left):
        ops = {'+': 10, '-': 10, '*': 20, '/': 20, '^': 30}
        if token.value in ops:
            rbp = ops[token.value] - (1 if token.value == '^' else 0)
            return ('binop', token.value, left, self.parse(rbp))
        if token.value == '!': return ('factorial', left)
        raise SyntaxError(f"Unexpected {token}")
    def lbp(self, token):
        return {'+':10,'-':10,'*':20,'/':20,'^':30,'!':40}.get(token.value, 0)

def parse(text):
    return PrattParser(tokenize(text)).parse()

if __name__ == "__main__":
    for expr in ["2 + 3 * 4", "2 ^ 3 ^ 2", "(1 + 2) * 3", "-5 + 3"]:
        print(f"{expr:20s} → {parse(expr)}")
