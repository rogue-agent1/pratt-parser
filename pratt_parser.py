#!/usr/bin/env python3
"""pratt_parser - Top-down operator precedence (Pratt) parser."""
import argparse, re

class Token:
    def __init__(self, type, value): self.type,self.value=type,value
    def __repr__(self): return f"Token({self.type},{self.value})"

def tokenize(text):
    tokens=[]
    for m in re.finditer(r'\d+\.?\d*|[+\-*/^()]|[a-zA-Z_]\w*',text):
        v=m.group()
        if re.match(r'\d',v): tokens.append(Token('NUM',float(v)))
        elif v in '+-*/^()': tokens.append(Token(v,v))
        else: tokens.append(Token('ID',v))
    tokens.append(Token('EOF',None)); return tokens

class Parser:
    def __init__(self, tokens): self.tokens=tokens; self.pos=0
    def peek(self): return self.tokens[self.pos]
    def advance(self): t=self.tokens[self.pos]; self.pos+=1; return t
    def expect(self, type):
        t=self.advance()
        if t.type!=type: raise SyntaxError(f"Expected {type}, got {t.type}")
        return t
    def nud(self, token):
        if token.type=='NUM': return ('num',token.value)
        if token.type=='ID': return ('var',token.value)
        if token.type=='(':
            expr=self.expression(0); self.expect(')'); return expr
        if token.type=='-': return ('neg',self.expression(70))
        if token.type=='+': return self.expression(70)
        raise SyntaxError(f"Unexpected {token}")
    def led(self, left, token):
        bp={'+':(50,51),'-':(50,51),'*':(60,61),'/':(60,61),'^':(80,79)}
        _,rbp=bp.get(token.type,(0,0))
        return ('binop',token.value,left,self.expression(rbp))
    def lbp(self, token):
        bp={'+':(50,51),'-':(50,51),'*':(60,61),'/':(60,61),'^':(80,79)}
        return bp.get(token.type,(0,0))[0]
    def expression(self, rbp=0):
        t=self.advance(); left=self.nud(t)
        while rbp<self.lbp(self.peek()):
            t=self.advance(); left=self.led(left,t)
        return left

def evaluate(ast):
    if ast[0]=='num': return ast[1]
    if ast[0]=='var': return {'pi':3.14159265,'e':2.71828183}.get(ast[1],0)
    if ast[0]=='neg': return -evaluate(ast[1])
    if ast[0]=='binop':
        l,r=evaluate(ast[2]),evaluate(ast[3])
        return {'+':l+r,'-':l-r,'*':l*r,'/':l/r if r else float('inf'),'^':l**r}[ast[1]]
    return 0

def main():
    p=argparse.ArgumentParser(description="Pratt parser")
    p.add_argument("expr",nargs="?",default="2+3*4^2-1")
    p.add_argument("--ast",action="store_true")
    args=p.parse_args()
    tokens=tokenize(args.expr)
    parser=Parser(tokens)
    ast=parser.expression()
    if args.ast: print(f"AST: {ast}")
    print(f"{args.expr} = {evaluate(ast)}")

if __name__=="__main__":
    main()
