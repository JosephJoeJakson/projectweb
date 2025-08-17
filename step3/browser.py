import tkinter as tk
from tkinter import filedialog, messagebox
import os, json
from html_parser import parse_html, dom_to_string
from css_parser import CSSParser

class Browser:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Browser – Step 3 (HTML + CSS)")
        self.dom = None
        self.css = CSSParser()

        top = tk.Frame(root); top.pack(side=tk.TOP, fill=tk.X)
        self.url_entry = tk.Entry(top); self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=4)
        self.url_entry.bind("<Return>", self.load_url)
        tk.Button(top, text="Load", command=self.load_url).pack(side=tk.LEFT, padx=4, pady=4)

        self.source_text = tk.Text(root, height=18); self.source_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(root, bg="white"); self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _walk(self, n):
        if not n: return
        yield n
        for c in n.children: yield from self._walk(c)

    def _apply_css(self, node, rules):
        node.styles = node.styles or {}
        for r in rules:
            sels = list(r.get("selectors", []) or [])
            if not sels and "selector" in r: sels = [r["selector"]]
            for sel in sels:
                if self._match(node, sel):
                    node.styles.update(r.get("style", {}))
        for c in node.children: self._apply_css(c, rules)

    def _match(self, node, sel):
        sel = (sel or "").strip()
        if not sel: return False
        tag = node.tag.lower()
        attrs = node.attributes
        if sel.startswith("."): return sel[1:] in (attrs.get("class") or "").split()
        if sel.startswith("#"): return attrs.get("id") == sel[1:]
        return tag == sel.lower()

    def load_url(self, event=None):
        url = self.url_entry.get().strip()
        if not url:
            path = filedialog.askopenfilename(title="Open HTML", filetypes=(("HTML","*.html;*.htm"),("All","*.*")))
            if not path: return
            url = path; self.url_entry.delete(0, tk.END); self.url_entry.insert(0, path)
        if not os.path.exists(url):
            messagebox.showerror("Error", f"File not found:\n{url}"); return

        with open(url, "r", encoding="utf-8") as f:
            html = f.read()

        self.dom = parse_html(html)
        self.css.rules = []

        # inline <style>
        for n in list(self._walk(self.dom)):
            if n.tag.lower() == "style" and n.text.strip():
                self.css.parse_css(n.text)

        # simple <link rel=stylesheet href="*.css"> same folder
        base = os.path.dirname(os.path.abspath(url))
        for n in list(self._walk(self.dom)):
            if n.tag.lower() == "link" and (n.attributes.get("rel") or "").lower() == "stylesheet":
                href = (n.attributes.get("href") or "").strip()
                if href:
                    path = href if os.path.isabs(href) else os.path.join(base, href)
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            self.css.parse_css(f.read())

        self._apply_css(self.dom, self.css.rules)

        self.source_text.delete("1.0", tk.END)
        self.source_text.insert(tk.END, html + "\n\n----- DOM -----\n" + dom_to_string(self.dom))
        self.source_text.insert(tk.END, "\n\n----- CSSOM -----\n" + json.dumps(self.css.rules, indent=2))
        self.canvas.delete("all")  # rendering comes later

if __name__ == "__main__":
    root = tk.Tk(); root.geometry("900x700")
    Browser(root); root.mainloop()
