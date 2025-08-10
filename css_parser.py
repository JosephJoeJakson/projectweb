import re

class CSSParser:
    def __init__(self):
        self.rules = []
    
    def parse_css(self, css_content):
        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Split into rules
        rule_pattern = re.compile(r'([^{]+)\{([^}]*)\}')
        for match in rule_pattern.finditer(css_content):
            selectors = [s.strip() for s in match.group(1).split(',')]
            declarations = self._parse_declarations(match.group(2))
            
            for selector in selectors:
                self.rules.append({
                    'selector': selector,
                    'style': declarations
                })
        return self.rules
    
    def _parse_declarations(self, declarations_str):
        declarations = {}
        for decl in declarations_str.split(';'):
            decl = decl.strip()
            if not decl:
                continue
            try:
                prop, value = decl.split(':', 1)
                declarations[prop.strip()] = value.strip()
            except ValueError:
                continue
        return declarations
    
    def apply_styles(self, dom_node, rules):
        if not dom_node:
            return
        
        for rule in rules:
            selector = rule['selector']
            if self._matches_selector(dom_node, selector):
                for prop, value in rule['style'].items():
                    dom_node.styles[prop] = value
        
        for child in dom_node.children:
            self.apply_styles(child, rules)
    
    def _matches_selector(self, node, selector):
        # Simple selector matching
        if selector.startswith('.'):
            class_name = selector[1:]
            return 'class' in node.attributes and class_name in node.attributes['class'].split()
        elif selector.startswith('#'):
            id_name = selector[1:]
            return 'id' in node.attributes and id_name == node.attributes['id']
        elif selector == 'body' and node.tag == 'body':
            return True
        else:
            return selector == node.tag