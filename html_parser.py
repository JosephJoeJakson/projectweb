from html.parser import HTMLParser as _HTMLParser

class DOMNode:
    def __init__(self, tag, parent=None):
        self.tag = tag
        self.parent = parent
        self.children = []
        self.attributes = {}
        self.text = ""
        self.styles = {}

    def __repr__(self, indent=0):
        res = "  " * indent + f"<{self.tag}"
        if self.attributes:
            res += " " + " ".join(f'{k}="{v}"' for k, v in self.attributes.items())
        res += ">"
        if self.text:
            res += self.text
        if self.children:
            res += "\n"
            res += "\n".join(child.__repr__(indent+1) for child in self.children)
            res += "\n" + "  " * indent
        res += f"</{self.tag}>"
        return res

class MiniHTMLParser(_HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = None
        self.current_node = None

    def handle_starttag(self, tag, attrs):
        if not self.root:
            node = DOMNode(tag)
            self.root = node
            self.current_node = node
        else:
            node = DOMNode(tag, self.current_node)
            self.current_node.children.append(node)
            self.current_node = node
        self.current_node.attributes = dict(attrs)

    def handle_endtag(self, tag):
        if self.current_node and self.current_node.parent:
            self.current_node = self.current_node.parent

    def handle_data(self, data):
        if self.current_node:
            chunk = data.strip()
            if chunk:
                if self.current_node.text and not self.current_node.text.endswith(" "):
                    self.current_node.text += " "
                self.current_node.text += chunk

    def get_dom(self):
        return self.root

def parse_html(html_content):
    parser = MiniHTMLParser()
    parser.feed(html_content or "")
    return parser.get_dom()
