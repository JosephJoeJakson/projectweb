# Step 5 — Rendering avec Tkinter : peindre depuis l'arbre de layout (+ z-index simple)
# Usage:
#   python browser.py [path/to/file.html] [path/to/file.css]
#
# Fenêtre Tkinter avec un Canvas qui dessine la page calculée.

import sys
import tkinter as tk
from tkinter import filedialog
from html_parser import parse_html
from css_parser import CSSParser, apply_css_to_dom
from layout import build_layout_tree
from render import render_layout

def pick_file(title, patterns):
    root = tk.Tk(); root.withdraw()
    path = filedialog.askopenfilename(title=title, filetypes=patterns)
    root.destroy()
    return path

class App:
    def __init__(self, html_path=None, css_path=None):
        self.root = tk.Tk()
        self.root.title("Mini Browser — Step 5 (Rendering)")
        self.canvas = tk.Canvas(self.root, width=900, height=700, background="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        top = tk.Frame(self.root); top.place(x=0, y=0, relwidth=1.0)
        self.btn_reload = tk.Button(top, text="Ouvrir HTML/CSS", command=self.load_files)
        self.btn_reload.pack(side=tk.LEFT, padx=6, pady=6)

        self.html_path = html_path
        self.css_path = css_path
        self.dom_root = None
        self.layout_root = None
        self.rules = []

        self.root.bind("<Configure>", lambda e: self.render())

        if not self.html_path:
            self.load_files()
        else:
            self.compute()

    def load_files(self):
        self.html_path = pick_file("Choisir un fichier HTML", [("Fichiers HTML","*.html;*.htm"), ("Tous","*.*")])
        if not self.html_path: return
        self.css_path = pick_file("Choisir un fichier CSS (facultatif)", [("Fichiers CSS","*.css"), ("Tous","*.*")])
        self.compute()

    def compute(self):
        html = open(self.html_path, "r", encoding="utf-8", errors="ignore").read()
        self.dom_root, errors = parse_html(html)

        css = ""
        if self.css_path:
            css = open(self.css_path, "r", encoding="utf-8", errors="ignore").read()
        parser = CSSParser()
        self.rules = parser.parse_css(css)
        apply_css_to_dom(self.dom_root, self.rules)

        self.layout_root = build_layout_tree(self.dom_root, viewport_width=max(800, int(self.canvas.winfo_width() or 800)))
        self.render()

    def render(self):
        if self.layout_root is None: return
        w = max(800, int(self.canvas.winfo_width() or 800))
        h = max(600, int(self.canvas.winfo_height() or 600))
        self.canvas.config(scrollregion=(0,0,w,h))
        render_layout(self.canvas, self.layout_root)

def main():
    html = sys.argv[1] if len(sys.argv) >= 2 else None
    css = sys.argv[2] if len(sys.argv) >= 3 else None
    app = App(html, css)
    app.root.mainloop()

if __name__ == "__main__":
    main()
