#!/usr/bin/env python3
"""Pratt parser for expressions. Zero dependencies."""
import re, sys

class Token:
    def __init__(self, type, value):
        self.type = type; self.value = value
    def __repr__(self): return f"Token({self.type}, {self.value!r})"

def tokenize(text):
    tokens = []
    i = 0
    while i < len(text):
        if text[i].isspace(): i += 1; continue
        if text[i].isdigit() or (text[i] == '.' and i+1 < len(text) and text[i+1].isdigit()):
            j = i
            while j < len(text) and (text[j].isdigit() or text[j] == '.'): j += 1
            tokens.append(Token("NUM", float(text[i:j]))); i = j
        elif text[i].isalpha():
            j = i
            while j < len(text) and text[j].isalnum(): j += 1
            tokens.append(Token("ID", text[i:j])); i = j
        elif text[i:i+2] in ("==","!=","<=",">=","&&","||"):
            tokens.append(Token("OP", text[i:i+2])); i += 2
        elif text[i] in "+-*/%^()!<>,":
            tokens.append(Token("OP", text[i])); i += 1
        else: i += 1
    tokens.append(Token("EOF", None))
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens; self.pos = 0

    def peek(self): return self.tokens[self.pos]
    def advance(self): t = self.tokens[self.pos]; self.pos += 1; return t

    def parse(self, rbp=0):
        t = self.advance()
        left = self.nud(t)
        while rbp < self.lbp(self.peek()):
            t = self.advance()
            left = self.led(t, left)
        return left

    def nud(self, t):
        if t.type == "NUM": return ("num", t.value)
        if t.type == "ID": return ("id", t.value)
        if t.value == "(":
            expr = self.parse(0)
            self.advance()  # consume )
            return expr
        if t.value == "-": return ("neg", self.parse(70))
        if t.value == "!": return ("not", self.parse(70))
        raise SyntaxError(f"Unexpected {t}")

    def led(self, t, left):
        bp = {"+":50,"-":50,"*":60,"/":60,"%":60,"^":80,
              "==":30,"!=":30,"<":40,">":40,"<=":40,">=":40,
              "&&":20,"||":10}
        if t.value == "^":  # right-associative
            return ("op", t.value, left, self.parse(bp[t.value]-1))
        if t.value in bp:
            return ("op", t.value, left, self.parse(bp[t.value]))
        if t.value == "(":  # function call
            args = []
            while self.peek().value != ")":
                args.append(self.parse(0))
                if self.peek().value == ",": self.advance()
            self.advance()
            return ("call", left, args)
        raise SyntaxError(f"Unexpected {t}")

    def lbp(self, t):
        bp = {"+":50,"-":50,"*":60,"/":60,"%":60,"^":80,
              "==":30,"!=":30,"<":40,">":40,"<=":40,">=":40,
              "&&":20,"||":10,"(":90}
        return bp.get(t.value, 0)

import math
BUILTINS = {"sqrt": math.sqrt, "abs": abs, "sin": math.sin, "cos": math.cos,
            "max": max, "min": min, "log": math.log}

def evaluate(ast, env=None):
    env = env or {}
    if ast[0] == "num": return ast[1]
    if ast[0] == "id": return env.get(ast[1], BUILTINS.get(ast[1], 0))
    if ast[0] == "neg": return -evaluate(ast[1], env)
    if ast[0] == "not": return not evaluate(ast[1], env)
    if ast[0] == "op":
        _, op, l, r = ast
        a, b = evaluate(l, env), evaluate(r, env)
        ops = {"+":lambda:a+b,"-":lambda:a-b,"*":lambda:a*b,"/":lambda:a/b,
               "%":lambda:a%b,"^":lambda:a**b,"==":lambda:a==b,"!=":lambda:a!=b,
               "<":lambda:a<b,">":lambda:a>b,"<=":lambda:a<=b,">=":lambda:a>=b,
               "&&":lambda:a and b,"||":lambda:a or b}
        return ops[op]()
    if ast[0] == "call":
        fn = evaluate(ast[1], env)
        args = [evaluate(a, env) for a in ast[2]]
        return fn(*args)

def calc(expr, env=None):
    return evaluate(Parser(tokenize(expr)).parse(), env)

if __name__ == "__main__":
    expr = " ".join(sys.argv[1:]) or "2 + 3 * 4 ^ 2"
    print(f"{expr} = {calc(expr)}")
