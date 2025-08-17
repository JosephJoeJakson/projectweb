from html.parser import HTMLParser as _HTMLParser

class DOMNode:
    def __init__(self, tag, parent=None):
        self.tag = tag
        self.parent = parent
        self.children = []
        self.attributes = {}
        self.text = ""
        self.styles = {}

def dom_to_string(node, indent=0):
    if not node: return ""
    pad = "  " * indent
    attr = ""
    if node.attributes:
        attr = " " + " ".join(f'{k}="{v}"' for k, v in node.attributes.items())
    out = f"{pad}<{node.tag}{attr}>"
    if node.text.strip():
        out += " " + node.text.strip()
    lines = [out]
    for c in node.children:
        lines.append(dom_to_string(c, indent+1))
    lines.append(f"{pad}</{node.tag}>")
    return "\n".join(lines)

class MiniHTMLParser(_HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = None
        self.cur = None

    def handle_starttag(self, tag, attrs):
        node = DOMNode(tag, self.cur)
        node.attributes = dict(attrs)
        if self.cur: self.cur.children.append(node)
        else: self.root = node
        self.cur = node

    def handle_endtag(self, tag):
        if self.cur and self.cur.parent:
            self.cur = self.cur.parent

    def handle_data(self, data):
        if self.cur:
            txt = data.strip()
            if txt:
                if self.cur.text and not self.cur.text.endswith(" "):
                    self.cur.text += " "
                self.cur.text += txt

def parse_html(html):
    p = MiniHTMLParser(); p.feed(html or ""); return p.root
