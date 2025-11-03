# Step 6 — JavaScript simple : innerHTML + événements (onclick)
# Usage:
#   python browser.py [path/to/file.html] [path/to/file.css]
#
# Démo : un bouton qui change le texte d'une <div> au clic.

import sys
import tkinter as tk
from tkinter import filedialog
from html_parser import parse_html
from css_parser import CSSParser, apply_css_to_dom
from layout import build_layout_tree
from render import render_layout
from js_interpreter import JSInterpreter

def pick_file(title, patterns):
    root = tk.Tk(); root.withdraw()
    path = filedialog.askopenfilename(title=title, filetypes=patterns)
    root.destroy()
    return path

class App:
    def __init__(self, html_path=None, css_path=None):
        self.root = tk.Tk()
        self.root.title("Mini Browser — Step 6 (JavaScript)")
        self.canvas = tk.Canvas(self.root, width=900, height=700, background="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        top = tk.Frame(self.root); top.place(x=0, y=0, relwidth=1.0)
        tk.Button(top, text="Ouvrir HTML/CSS", command=self.load_files).pack(side=tk.LEFT, padx=6, pady=6)

        self.html_path = html_path
        self.css_path = css_path
        self.dom_root = None
        self.layout_root = None
        self.rules = []
        self.hit_regions = []  # [(x1,y1,x2,y2,node)]

        self.js = JSInterpreter(dom_root=None, refresh_callback=self.refresh)

        self.canvas.bind("<Button-1>", self.on_click)
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

        # Exécuter tous les <script> inline très simples: on scanne le DOM pour trouver du .text dans <script>
        def run_scripts(node):
            if node.tag == "script" and node.text.strip():
                self.js.dom_root = self.dom_root
                self.js.execute(node.text)
            for c in node.children:
                run_scripts(c)
        run_scripts(self.dom_root)

        self.layout_root = build_layout_tree(self.dom_root, viewport_width=max(800, int(self.canvas.winfo_width() or 800)))
        self.render()

    def render(self):
        if self.dom_root is None: return
        self.layout_root = build_layout_tree(self.dom_root, viewport_width=max(800, int(self.canvas.winfo_width() or 800)))
        self.hit_regions = render_layout(self.canvas, self.layout_root)
        # mettre à jour la cible DOM de l'interpréteur (au cas où)
        self.js.dom_root = self.dom_root

    def refresh(self):
        # callback appelé par le JS quand il modifie le DOM
        self.render()

    def _hit_test(self, x, y):
        # Retourne le node cliquable le plus haut dont la boîte contient (x,y)
        best = None
        for (x1,y1,x2,y2,node) in self.hit_regions:
            if x1 <= x <= x2 and y1 <= y <= y2:
                best = (x1,y1,x2,y2,node)  # on garde le dernier (dessiné par-dessus si z-index >)
        return best[4] if best else None

    def on_click(self, event):
        node = self._hit_test(event.x, event.y)
        if not node: return
        # On déclenche l'événement 'click' pour l'élément cliqué (si id présent)
        eid = (node.attributes or {}).get("id")
        if eid:
            self.js.trigger_click(eid)

def main():
    html = sys.argv[1] if len(sys.argv) >= 2 else None
    css = sys.argv[2] if len(sys.argv) >= 3 else None
    app = App(html, css)
    app.root.mainloop()

if __name__ == "__main__":
    main()
