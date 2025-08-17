import tkinter as tk
from tkinter import filedialog, messagebox
import os
from urllib.parse import urlparse, unquote
from urllib.request import url2pathname

from html_parser import parse_html
from css_parser import CSSParser
from render import render_layout
from js_interpreter import JSInterpreter


class Browser:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Browser")
        self.current_dom = None
        self.css_parser = CSSParser()

        # URL bar + load button
        top = tk.Frame(root)
        top.pack(side=tk.TOP, fill=tk.X)
        self.url_entry = tk.Entry(top)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=4)
        self.url_entry.bind("<Return>", self.load_url)
        self.load_button = tk.Button(top, text="Load", command=self.load_url)
        self.load_button.pack(side=tk.LEFT, padx=4, pady=4)

        # Source viewer
        self.source_text = tk.Text(root, height=10)
        self.source_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Render surface
        self.render_canvas = tk.Canvas(root, bg="white")
        self.render_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Re-render on resize
        self.render_canvas.bind("<Configure>", lambda e: self._rerender())

    # -------- path & file helpers --------
    def _read_file(self, fp):
        with open(fp, 'r', encoding='utf-8') as f:
            return f.read()

    def _resolve_file_url(self, url):
        parsed = urlparse(url)
        path = url2pathname(unquote(parsed.path or ""))
        # Windows quirk: '/C:/x.html' -> 'C:/x.html'
        if os.name == "nt" and len(path) > 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        return path if path else None

    # -------- DOM utils --------
    def _walk(self, node):
        if node is None:
            return
        yield node
        for child in getattr(node, "children", []) or []:
            yield from self._walk(child)

    def _find_all(self, node, tagname):
        tagname = (tagname or "").lower()
        for n in self._walk(node):
            if getattr(n, "tag", "").lower() == tagname:
                yield n

    # -------- main actions --------
    def load_url(self, event=None):
        url = self.url_entry.get().strip()
        content = None
        file_path = None

        if not url:
            file_path = filedialog.askopenfilename(
                title="Open HTML File",
                filetypes=(("HTML Files", "*.html;*.htm"), ("All Files", "*.*")))
            if not file_path:
                return
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, f"file://{file_path}")
            content = self._read_file(file_path)

        elif url.lower().startswith("file:"):
            path = self._resolve_file_url(url)
            if not path or not os.path.exists(path):
                messagebox.showerror("Error", f"File not found:\n{url}")
                return
            file_path = path
            content = self._read_file(file_path)

        else:
            candidate = os.path.expanduser(url)
            if not os.path.isabs(candidate):
                candidate = os.path.abspath(candidate)
            if os.path.exists(candidate):
                file_path = candidate
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, f"file://{file_path}")
                content = self._read_file(file_path)
            else:
                messagebox.showerror("Error", f"Not a file path:\n{url}")
                return

        self.source_text.delete(1.0, tk.END)
        self.source_text.insert(tk.END, content)
        self.render_content(content, base_dir=os.path.dirname(file_path) if file_path else None)

    def _rerender(self):
        if self.current_dom is not None:
            render_layout(self.render_canvas, self.current_dom, self.css_parser.rules)

    def render_content(self, html_content, base_dir=None):
        # Reset CSS between pages
        self.css_parser.rules = []

        # Parse HTML to DOM
        self.current_dom = parse_html(html_content)

        # Load local <link rel="stylesheet"> files
        if base_dir:
            for link in self._find_all(self.current_dom, "link"):
                rel = (link.attributes.get("rel") or "").lower()
                href = (link.attributes.get("href") or "").strip()
                if rel == "stylesheet" and href and not href.lower().startswith(("http://", "https://")):
                    css_path = href if os.path.isabs(href) else os.path.normpath(os.path.join(base_dir, href))
                    if os.path.exists(css_path):
                        try:
                            self.css_parser.parse_css(self._read_file(css_path))
                        except Exception as e:
                            print(f"Failed to read CSS '{css_path}': {e}")

        # Inline <style> blocks
        for style_node in self._find_all(self.current_dom, "style"):
            css_text = style_node.text or ""
            if css_text.strip():
                self.css_parser.parse_css(css_text)

        # Execute very simple inline <script> blocks
        interpreter = JSInterpreter(self.current_dom)
        for script_node in self._find_all(self.current_dom, "script"):
            js = (script_node.text or "").strip()
            if js:
                try:
                    interpreter.execute(js)
                except Exception as e:
                    print(f"Script error: {e}")

        # Render
        self.render_canvas.delete("all")
        render_layout(self.render_canvas, self.current_dom, self.css_parser.rules)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x700")
    browser = Browser(root)
    root.mainloop()
