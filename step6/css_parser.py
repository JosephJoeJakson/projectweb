# Step 6 — Parser CSS (hérité de S3) + application au DOM (spécificité)
import re

def _strip_comments(s: str) -> str:
    return re.sub(r'/\*.*?\*/', '', s, flags=re.DOTALL)

def _parse_declarations(body: str):
    decls = {}
    for d in body.split(';'):
        if not d or ':' not in d: continue
        k, v = d.split(':', 1)
        k = k.strip().lower()
        v = v.strip()
        if not k: continue
        decls[k] = v
    return decls

def _specificity_for_selector(sel: str):
    sel = (sel or '').strip()
    a = sel.count('#')
    b = sel.count('.')
    c = 0
    m = re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*', sel)
    if m: c = 1
    return (a, b, c)

def _split_selectors(sel_group: str):
    return [s.strip() for s in sel_group.split(',') if s.strip()]

class CSSParser:
    def __init__(self):
        self.rules = []

    def parse_css(self, css: str):
        self.rules = []
        if not css: return self.rules
        css = _strip_comments(css)
        order = 0
        for m in re.finditer(r'([^{]+)\{([^}]*)\}', css):
            sel_group = m.group(1).strip()
            body = m.group(2)
            decls = _parse_declarations(body)
            selectors = _split_selectors(sel_group)
            if not selectors: continue
            specificities = {s: _specificity_for_selector(s) for s in selectors}
            rule = {'selectors': selectors, 'style': decls, 'order': order, 'specificities': specificities}
            self.rules.append(rule)
            for s in selectors:
                self.rules.append({'selector': s, 'style': decls, 'order': order, 'specificity': specificities[s]})
            order += 1
        return self.rules

def _classes(attrs):
    cl = (attrs.get('class') or '').strip()
    return [c for c in cl.split() if c]

def _match(node, sel: str) -> bool:
    sel = (sel or '').strip()
    if not sel: return False
    tag = (node.tag or '').lower()
    attrs = getattr(node, 'attributes', {}) or {}

    m = re.match(r'^([a-zA-Z][a-zA-Z0-9_-]*)', sel)
    if m:
        if tag != m.group(1).lower():
            return False
        remainder = sel[m.end():]
    else:
        remainder = sel

    for part in re.finditer(r'([.#])([a-zA-Z0-9_-]+)', remainder):
        kind, name = part.group(1), part.group(2)
        if kind == '#':
            if attrs.get('id') != name:
                return False
        else:
            if name not in _classes(attrs):
                return False
    return True

def apply_css_to_dom(dom_root, rules):
    if dom_root is None: return

    def walk(node):
        if getattr(node, 'styles', None) is None:
            node.styles = {}
        matches = []
        for r in rules:
            sel = r.get('selector')
            if not sel: continue
            if _match(node, sel):
                matches.append(r)
        matches.sort(key=lambda r: (r.get('specificity', (0,0,0)), r.get('order', 0)))
        for r in matches:
            for k, v in (r.get('style') or {}).items():
                node.styles[k] = v
        for c in getattr(node, 'children', []):
            walk(c)

    walk(dom_root)
