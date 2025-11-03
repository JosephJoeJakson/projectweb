# Step 5 — Parseur HTML (hérité de S2/S3) : DOM + récupération d'erreurs basiques
from html.parser import HTMLParser as _HTMLParser

class DOMNode:
    def __init__(self, tag, parent=None):
        self.tag = (tag or '').lower()
        self.parent = parent
        self.children = []
        self.attributes = {}
        self.text = ""
        self.styles = {}

SELF_CLOSING = {'br','img','hr','meta','link','input','source'}
AUTO_CLOSE_ON_START = {'p','li'}

class _MiniHTMLParser(_HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = DOMNode('document', None)
        self.cur = self.root
        self.errors = []

    def handle_starttag(self, tag, attrs):
        tag = (tag or '').lower()
        if self.cur.tag == tag and tag in AUTO_CLOSE_ON_START and self.cur.parent:
            self.errors.append(f"Auto-fermeture de <{tag}> avant nouvelle ouverture.")
            self.cur = self.cur.parent
        node = DOMNode(tag, self.cur)
        node.attributes = dict(attrs or [])
        self.cur.children.append(node)
        if tag not in SELF_CLOSING:
            self.cur = node

    def handle_endtag(self, tag):
        tag = (tag or '').lower()
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is None:
            self.errors.append(f"Balise fermante orpheline </{tag}> ignorée.")
            return
        self.cur = n.parent if n.parent else self.root

    def handle_data(self, data):
        if not data or self.cur is None: return
        txt = data.strip()
        if not txt: return
        if self.cur.text and not self.cur.text.endswith(" "):
            self.cur.text += " "
        self.cur.text += txt

def parse_html(html: str):
    p = _MiniHTMLParser()
    try:
        p.feed(html or "")
        while p.cur and p.cur.parent:
            if p.cur.tag not in SELF_CLOSING:
                p.errors.append(f"Balise <{p.cur.tag}> non fermée — auto-fermeture en fin de document.")
            p.cur = p.cur.parent
    except Exception as e:
        p.errors.append(f"Erreur de parsing: {e!r}")
    return p.root, p.errors
