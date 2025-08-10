class JSInterpreter:
    def __init__(self, dom_root):
        self.dom_root = dom_root
        self.variables = {}
    
    def execute(self, js_code):
        # Very simple JS interpreter for demo purposes
        lines = [line.strip() for line in js_code.split(';') if line.strip()]
        for line in lines:
            if 'document.getElementById' in line and 'innerHTML' in line:
                # Handle simple DOM manipulation
                parts = line.split('"')
                if len(parts) >= 3:
                    element_id = parts[1]
                    new_content = parts[3] if len(parts) > 3 else ''
                    element = self._find_element_by_id(self.dom_root, element_id)
                    if element:
                        element.text = new_content
    
    def _find_element_by_id(self, node, element_id):
        if not node:
            return None
        if 'id' in node.attributes and node.attributes['id'] == element_id:
            return node
        for child in node.children:
            found = self._find_element_by_id(child, element_id)
            if found:
                return found
        return None