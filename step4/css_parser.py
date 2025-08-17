import re

class CSSParser:
    def __init__(self):
        self.rules = []

    def parse_css(self, css):
        if not css: return self.rules
        css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
        for m in re.finditer(r'([^{]+)\{([^}]*)\}', css):
            selectors = [s.strip() for s in m.group(1).split(',') if s.strip()]
            decls = {}
            for d in m.group(2).split(';'):
                d = d.strip()
                if not d or ':' not in d: continue
                k, v = d.split(':', 1)
                decls[k.strip()] = v.strip()
            if selectors:
                self.rules.append({'selectors': selectors, 'style': decls})
                for s in selectors:
                    self.rules.append({'selector': s, 'style': decls})
        return self.rules
