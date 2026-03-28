#!/usr/bin/env python3
"""pratt_parser - Pratt parser for mathematical expressions with AST."""
import sys, re, math, json

def tokenize(s):
    return [t for t in re.findall(r'\d+\.?\d*|[+\-*/^()!]|\w+', s)]

class Parser:
    def __init__(self, tokens): self.tokens=tokens; self.pos=0
    def peek(self): return self.tokens[self.pos] if self.pos<len(self.tokens) else None
    def consume(self): t=self.peek(); self.pos+=1; return t
    def parse(self, rbp=0):
        t=self.consume()
        left=self.nud(t)
        while self.peek() and self.lbp(self.peek())>rbp:
            t=self.consume()
            left=self.led(t, left)
        return left
    def nud(self, t):
        if t=='(': e=self.parse(); self.consume(); return e
        if t=='-': return ('neg',self.parse(70))
        if t.replace('.','').isdigit(): return float(t)
        return ('var',t)
    def led(self, t, left):
        bp={'+':(50,50),'-':(50,50),'*':(60,60),'/':(60,60),'^':(80,79)}
        if t in bp: return (t, left, self.parse(bp[t][1]))
        if t=='!': return ('!', left)
        return (t, left)
    def lbp(self, t):
        return {'+':50,'-':50,'*':60,'/':60,'^':80,'!':90}.get(t,0)

def eval_ast(node, env=None):
    if env is None: env={'pi':math.pi,'e':math.e}
    if isinstance(node,(int,float)): return node
    if isinstance(node,tuple):
        if node[0]=='var': return env.get(node[1],0)
        if node[0]=='neg': return -eval_ast(node[1],env)
        if node[0]=='!': return math.factorial(int(eval_ast(node[1],env)))
        a,b=eval_ast(node[1],env),eval_ast(node[2],env) if len(node)>2 else (0,)
        ops={'+':lambda a,b:a+b,'-':lambda a,b:a-b,'*':lambda a,b:a*b,'/':lambda a,b:a/b,'^':lambda a,b:a**b}
        return ops[node[0]](a,b)
    return node

def ast_str(node, depth=0):
    indent='  '*depth
    if isinstance(node,(int,float)): return f"{indent}{node}"
    if isinstance(node,tuple):
        lines=[f"{indent}{node[0]}"]
        for child in node[1:]:
            lines.append(ast_str(child,depth+1))
        return '\n'.join(lines)
    return f"{indent}{node}"

def main():
    args=sys.argv[1:]
    if not args or '-h' in args:
        print("Usage: pratt_parser.py EXPR [--ast]"); return
    expr=' '.join(a for a in args if a!='--ast')
    tokens=tokenize(expr)
    ast=Parser(tokens).parse()
    if '--ast' in args:
        print(ast_str(ast))
    result=eval_ast(ast)
    print(f"  {expr} = {result}")

if __name__=='__main__': main()
