class JSInterpreter:
    def __init__(self, dom_root):
        self.dom_root = dom_root

    def execute(self, js):
        # Support: document.getElementById("id").innerHTML = "text";
        for line in [l.strip() for l in (js or "").split(";") if l.strip()]:
            if "document.getElementById" in line and "innerHTML" in line and "=" in line:
                try:
                    left, right = line.split("=", 1)
                    eid = left.split('"')[1]
                    val = right.split('"')[1]
                    n = self._find(self.dom_root, eid)
                    if n: n.text = val
                except Exception:
                    pass

    def _find(self, node, eid):
        if not node: return None
        if node.attributes.get("id") == eid: return node
        for c in node.children:
            f = self._find(c, eid)
            if f: return f
        return None
