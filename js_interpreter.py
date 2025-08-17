class JSInterpreter:
    def __init__(self, dom_root):
        self.dom_root = dom_root
        self.variables = {}

    def execute(self, js_code):
        """
        Extremely tiny 'interpreter' that supports:
        document.getElementById("id").innerHTML = "text";
        """
        lines = [line.strip() for line in (js_code or "").split(';') if line.strip()]
        for line in lines:
            if 'document.getElementById' in line and 'innerHTML' in line and '=' in line:
                # Crude but effective: document.getElementById("x").innerHTML = "Hello";
                try:
                    left, right = line.split('=', 1)
                    # extract id
                    parts = left.split('"')
                    element_id = parts[1] if len(parts) >= 2 else None
                    # extract new content (between the first quotes on the right side)
                    rparts = right.split('"')
                    new_content = rparts[1] if len(rparts) >= 2 else ''
                    if element_id:
                        element = self._find_element_by_id(self.dom_root, element_id)
                        if element:
                            element.text = new_content
                except Exception:
                    pass

    def _find_element_by_id(self, node, element_id):
        if not node:
            return None
        if node.attributes.get('id') == element_id:
            return node
        for child in node.children:
            found = self._find_element_by_id(child, element_id)
            if found:
                return found
        return None
