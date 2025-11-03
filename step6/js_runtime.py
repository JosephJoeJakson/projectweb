
# Step 6 — Mini JavaScript runtime (subset) + DOM bindings
from typing import Any, Dict, List, Optional, Callable
import re

class JSEvalError(Exception): pass

_TOKEN_SPEC = [
    ('NUMBER',   r'\d+(?:\.\d+)?'),
    ('STRING',   r'"[^"\\]*"|\'[^\'\\]*\''),
    ('LET',      r'let\b|var\b|const\b'),
    ('IF',       r'if\b'),
    ('ELSE',     r'else\b'),
    ('TRUE',     r'true\b'),
    ('FALSE',    r'false\b'),
    ('NULL',     r'null\b'),
    ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'),
    ('OP',       r'===|==|=|\.|,|\(|\)|\{|\}|;'),
    ('WS',       r'[\s\r\n\t]+'),
]
_TOKEN_RE = re.compile('|'.join('(?P<%s>%s)' % t for t in _TOKEN_SPEC))

class Token:
    def __init__(self, kind, val):
        self.kind = kind; self.val = val
    def __repr__(self): return f'{self.kind}:{self.val}'

def tokenize(src: str) -> List['Token']:
    out = []
    for m in _TOKEN_RE.finditer(src or ''):
        k = m.lastgroup; v = m.group()
        if k == 'WS': continue
        out.append(Token(k, v))
    return out

class Parser:
    def __init__(self, toks: List['Token']):
        self.toks = toks; self.i = 0
    def peek(self, *kinds):
        if self.i >= len(self.toks): return None
        t = self.toks[self.i]
        return t if (not kinds or t.kind in kinds or t.val in kinds) else None
    def want(self, *kinds):
        t = self.peek(*kinds)
        if not t: raise JSEvalError('Unexpected token')
        self.i += 1; return t
    def program(self):
        stmts = []
        while self.peek():
            if self.peek('OP') and self.peek().val == '}': break
            stmts.append(self.statement())
            if self.peek('OP') and self.peek().val == ';': self.i += 1
        return ('prog', stmts)
    def statement(self):
        if self.peek('LET'):
            self.want('LET'); ident = self.want('ID').val
            if self.peek('OP') and self.peek().val == '=':
                self.want('OP'); expr = self.expr(); return ('decl', ident, expr)
            return ('decl', ident, None)
        if self.peek('IF'):
            self.want('IF'); self.want('OP'); cond = self.expr(); self.want('OP')
            then = self.block(); els = None
            if self.peek('ELSE'): self.want('ELSE'); els = self.block()
            return ('if', cond, then, els)
        node = self.expr(); return ('expr', node)
    def block(self):
        if self.peek('OP') and self.peek().val == '{':
            self.want('OP'); body = self.program(); self.want('OP'); return body
        else:
            return ('prog', [self.statement()])
    def expr(self):
        node = self.member()
        if self.peek('OP') and self.peek().val == '=' and self._assignable(node):
            self.want('OP'); rhs = self.expr(); return ('assign', node, rhs)
        return node
    def _assignable(self, node):
        return node[0] in ('id','member')
    def member(self):
        node = self.primary()
        while self.peek('OP') and self.peek().val in ('.','('):
            if self.peek().val == '.':
                self.want('OP'); name = self.want('ID').val; node = ('member', node, name)
            else:
                self.want('OP'); args = []
                if not (self.peek('OP') and self.peek().val == ')'):
                    args.append(self.expr())
                    while self.peek('OP') and self.peek().val == ',':
                        self.want('OP'); args.append(self.expr())
                self.want('OP'); node = ('call', node, args)
        return node
    def primary(self):
        if self.peek('NUMBER'): return ('num', float(self.want('NUMBER').val))
        if self.peek('STRING'):
            raw = self.want('STRING').val
            return ('str', raw[1:-1]) if len(raw)>=2 else ('str', raw)
        if self.peek('TRUE'): self.want('TRUE'); return ('bool', True)
        if self.peek('FALSE'): self.want('FALSE'); return ('bool', False)
        if self.peek('NULL'): self.want('NULL'); return ('null', None)
        if self.peek('ID'): return ('id', self.want('ID').val)
        if self.peek('OP') and self.peek().val == '(':
            self.want('OP'); e = self.expr(); self.want('OP'); return e
        raise JSEvalError('Invalid primary')

class JSFunction:
    def __init__(self, pyfunc): self.pyfunc = pyfunc
    def __call__(self, *a): return self.pyfunc(*a)
class JSEnvironment:
    def __init__(self, parent=None):
        self.parent = parent; self.vars = {}
    def get(self, name):
        if name in self.vars: return self.vars[name]
        if self.parent: return self.parent.get(name)
        raise JSEvalError('Undefined ' + name)
    def set(self, name, val): self.vars[name] = val; return val

class JSElement:
    def __init__(self, node, on_change):
        self.node = node; self.on_change = on_change; self.listeners = {}
        if getattr(node, 'styles', None) is None: node.styles = {}
    def setAttribute(self, k, v):
        if getattr(self.node, 'attributes', None) is None: self.node.attributes = {}
        self.node.attributes[k] = str(v); self.on_change()
    def appendChild(self, child):
        self.node.children.append(child.node if isinstance(child, JSElement) else child); self.on_change()
    def remove(self):
        if self.node.parent and self.node in self.node.parent.children:
            self.node.parent.children.remove(self.node); self.on_change()
    @property
    def textContent(self): return getattr(self.node, 'text', '')
    @textContent.setter
    def textContent(self, v): self.node.text = str(v); self.on_change()
    @property
    def style(self):
        class _Style:
            def __init__(self, node, on_change): self._n=node; self._on=on_change
            def __setattr__(self, k, v):
                if k in ('_n','_on'): return object.__setattr__(self,k,v)
                if self._n.styles is None: self._n.styles = {}
                self._n.styles[k.replace('_','-')] = str(v); self._on()
        return _Style(self.node, self.on_change)

class JSDocument:
    def __init__(self, dom_root, on_change):
        self.dom_root = dom_root; self.on_change = on_change
    def _wrap(self, node): return JSElement(node, self.on_change) if node else None
    def getElementById(self, _id):
        def walk(n):
            if getattr(n, 'attributes', {}).get('id') == _id: return n
            for c in getattr(n, 'children', []) or []:
                r = walk(c); 
                if r: return r
            return None
        return self._wrap(walk(self.dom_root))
    def querySelector(self, selector):
        if selector.startswith('#'): return self.getElementById(selector[1:])
        tag = selector.strip().lower()
        def walk(n):
            if getattr(n,'tag','').lower()==tag: return n
            for c in getattr(n,'children',[]) or []:
                r = walk(c); 
                if r: return r
            return None
        return self._wrap(walk(self.dom_root))

class JSRuntime:
    def __init__(self, dom_root, on_dom_change):
        self.dom_root = dom_root; self.on_dom_change = on_dom_change
        self.global_env = JSEnvironment(); self._install_builtins()
    def _install_builtins(self):
        self.global_env.set('console', {'log': JSFunction(lambda *a: None)})
        self.global_env.set('document', JSDocument(self.dom_root, self.on_dom_change))
    def eval(self, src: str):
        toks = tokenize(src); ast = Parser(toks).program(); return self._eval(ast, self.global_env)
    def _eval(self, node, env):
        t = node[0]
        if t=='prog':
            val=None
            for st in node[1]: val=self._eval(st, env)
            return val
        if t=='decl':
            _,name,expr = node; val=self._eval(expr, env) if expr is not None else None; return env.set(name, val)
        if t=='expr': return self._eval(node[1], env)
        if t=='if':
            _,cond,then,els = node
            if self._truthy(self._eval(cond, env)): return self._eval(then, env)
            return self._eval(els, env) if els else None
        if t=='assign':
            _, lhs, rhs = node; v=self._eval(rhs, env)
            if lhs[0]=='id': env.set(lhs[1], v); return v
            if lhs[0]=='member':
                target=self._eval(lhs[1], env); name=lhs[2]; self._set_prop(target,name,v); return v
            raise JSEvalError('Bad assignment')
        if t=='num': return node[1]
        if t=='str': return node[1]
        if t=='bool': return node[1]
        if t=='null': return None
        if t=='id': return env.get(node[1])
        if t=='member':
            target=self._eval(node[1], env); name=node[2]; return self._get_prop(target,name)
        if t=='call':
            callee=self._eval(node[1], env); args=[self._eval(a, env) for a in node[2]]
            if isinstance(callee, JSFunction): return callee(*args)
            if callable(callee): return callee(*args)
            raise JSEvalError('Not callable')
        raise JSEvalError('Unknown node')
    def _truthy(self, v): return bool(v)
    def _get_prop(self, obj, name):
        if isinstance(obj, JSElement):
            if name=='textContent': return obj.textContent
            if name=='style': return obj.style
            if name=='setAttribute': return JSFunction(lambda k,v: obj.setAttribute(k,v))
            if name=='appendChild': return JSFunction(lambda child: obj.appendChild(child))
            if name=='remove': return JSFunction(lambda : obj.remove())
            if name=='addEventListener':
                def _add(evt, fn):
                    obj.listeners.setdefault(evt, []).append(fn)
                return JSFunction(_add)
        if isinstance(obj, JSDocument):
            if name=='getElementById': return JSFunction(obj.getElementById)
            if name=='querySelector': return JSFunction(obj.querySelector)
        if isinstance(obj, dict) and name in obj: return obj[name]
        raise JSEvalError('No property '+name)
    def _set_prop(self, obj, name, v):
        if isinstance(obj, JSElement) and name=='textContent': obj.textContent=v; return
        if isinstance(obj, dict): obj[name]=v; return
        raise JSEvalError('Cannot set property')
def dispatch_click(jsrt: JSRuntime, el: JSElement):
    for fn in el.listeners.get('click', []):
        if isinstance(fn, JSFunction): fn()
        elif callable(fn): fn()
