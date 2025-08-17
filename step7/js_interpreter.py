class JSInterpreter:
    def __init__(self, dom_root): self.dom_root = dom_root
    def execute(self, js):
        for line in [l.strip() for l in (js or "").split(";") if l.strip()]:
            if "document.getElementById" in line and "innerHTML" in line and "=" in line:
                try:
                    left,right=line.split("=",1)
                    eid=left.split('"')[1]; val=right.split('"')[1]
                    n=self._find(self.dom_root,eid)
                    if n: n.text=val
                except Exception: pass
    def _find(self, n, eid):
        if not n: return None
        if n.attributes.get("id")==eid: return n
        for c in n.children:
            f=self._find(c,eid)
            if f: return f
        return None
