#!/usr/bin/env python3
"""pratt_parser - Pratt parser for expression parsing with operator precedence."""
import sys, re

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

def tokenize(expr):
    tokens = []
    i = 0
    while i < len(expr):
        if expr[i].isspace():
            i += 1
        elif expr[i].isdigit() or (expr[i] == '.' and i+1 < len(expr) and expr[i+1].isdigit()):
            j = i
            while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                j += 1
            tokens.append(Token("NUM", float(expr[i:j])))
            i = j
        elif expr[i] in "+-*/^%":
            tokens.append(Token("OP", expr[i]))
            i += 1
        elif expr[i] == '(':
            tokens.append(Token("LPAREN", "("))
            i += 1
        elif expr[i] == ')':
            tokens.append(Token("RPAREN", ")"))
            i += 1
        else:
            raise SyntaxError(f"Unknown char: {expr[i]}")
    tokens.append(Token("EOF", None))
    return tokens

PREC = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2, '^': 3}
RIGHT_ASSOC = {'^'}

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    def peek(self):
        return self.tokens[self.pos]
    def advance(self):
        t = self.tokens[self.pos]
        self.pos += 1
        return t
    def parse(self, min_prec=0):
        left = self.parse_prefix()
        while self.peek().type == "OP" and PREC.get(self.peek().value, -1) >= min_prec:
            op = self.advance().value
            prec = PREC[op]
            next_prec = prec if op in RIGHT_ASSOC else prec + 1
            right = self.parse(next_prec)
            left = ("binop", op, left, right)
        return left
    def parse_prefix(self):
        t = self.peek()
        if t.type == "NUM":
            self.advance()
            return ("num", t.value)
        if t.type == "OP" and t.value == "-":
            self.advance()
            operand = self.parse(3)
            return ("neg", operand)
        if t.type == "LPAREN":
            self.advance()
            expr = self.parse(0)
            assert self.advance().type == "RPAREN"
            return expr
        raise SyntaxError(f"Unexpected: {t.type}")

def evaluate(ast):
    if ast[0] == "num":
        return ast[1]
    if ast[0] == "neg":
        return -evaluate(ast[1])
    if ast[0] == "binop":
        _, op, l, r = ast
        lv, rv = evaluate(l), evaluate(r)
        if op == '+': return lv + rv
        if op == '-': return lv - rv
        if op == '*': return lv * rv
        if op == '/': return lv / rv
        if op == '^': return lv ** rv
        if op == '%': return lv % rv
    raise ValueError(f"Unknown: {ast}")

def calc(expr):
    return evaluate(Parser(tokenize(expr)).parse())

def test():
    assert calc("2 + 3 * 4") == 14
    assert calc("(2 + 3) * 4") == 20
    assert calc("2 ^ 3 ^ 2") == 512  # right-assoc: 2^(3^2)=2^9
    assert calc("-5 + 3") == -2
    assert abs(calc("10 / 3") - 10/3) < 1e-9
    assert calc("7 % 3") == 1
    print("OK: pratt_parser")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Usage: pratt_parser.py test")
