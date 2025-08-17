from html.parser import HTMLParser as _HTMLParser

class DOMNode:
    def __init__(self, tag, parent=None):
        self.tag = tag; self.parent=parent
        self.children=[]; self.attributes={}; self.text=""; self.styles={}

class MiniHTMLParser(_HTMLParser):
    def __init__(self): super().__init__(); self.root=None; self.cur=None
    def handle_starttag(self, tag, attrs):
        n=DOMNode(tag,self.cur); n.attributes=dict(attrs)
        if self.cur: self.cur.children.append(n)
        else: self.root=n
        self.cur=n
    def handle_endtag(self, tag):
        if self.cur and self.cur.parent: self.cur=self.cur.parent
    def handle_data(self, data):
        if self.cur:
            t=data.strip()
            if t:
                if self.cur.text and not self.cur.text.endswith(" "): self.cur.text+=" "
                self.cur.text+=t

def parse_html(html):
    p=MiniHTMLParser(); p.feed(html or ""); return p.root
