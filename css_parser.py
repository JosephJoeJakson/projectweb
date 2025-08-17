import re

class CSSParser:
    def __init__(self):
        self.rules = []

    def parse_css(self, css_content):
        """Parse very simple CSS into rules:
           {'selectors': ['h1', '.btn'], 'style': {'color':'red'}}"""
        if not css_content:
            return self.rules

        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)

        # Split into rules like "selector { decls }"
        rule_pattern = re.compile(r'([^{]+)\{([^}]*)\}')
        for match in rule_pattern.finditer(css_content):
            selectors = [s.strip() for s in match.group(1).split(',') if s.strip()]
            declarations = self._parse_declarations(match.group(2))
            if not selectors:
                continue

            # Primary (what render.py consumes)
            self.rules.append({'selectors': selectors, 'style': declarations})

            # Back-compat for any older code that expects single 'selector'
            for sel in selectors:
                self.rules.append({'selector': sel, 'style': declarations})
        return self.rules

    def _parse_declarations(self, declarations_str):
        declarations = {}
        for decl in declarations_str.split(';'):
            decl = decl.strip()
            if not decl:
                continue
            if ':' in decl:
                prop, value = decl.split(':', 1)
                declarations[prop.strip()] = value.strip()
        return declarations
