# Step 4 — Layout Engine : box model, block/inline, position: static/relative/absolute
# Usage:
#   python browser.py path/to/file.html [path/to/file.css]
#
# Affiche un arbre de layout (x,y,w,h) avec marges/paddings/bordures et positions.
# Cette étape ne dessine rien (le rendu viendra en S5).

import sys
from tkinter import Tk, filedialog
from html_parser import parse_html
from css_parser import CSSParser, apply_css_to_dom
from layout import build_layout_tree, layout_to_string

def pick_file(title, patterns):
    Tk().withdraw()
    return filedialog.askopenfilename(title=title, filetypes=patterns)

def main():
    if len(sys.argv) >= 2:
        html_path = sys.argv[1]
    else:
        html_path = pick_file("Choisir un fichier HTML", [("Fichiers HTML","*.html;*.htm"), ("Tous","*.*")])
        if not html_path:
            print("Aucun fichier HTML choisi."); return

    css_path = sys.argv[2] if len(sys.argv) >= 3 else pick_file("Choisir un fichier CSS (facultatif)", [("Fichiers CSS","*.css"), ("Tous","*.*")])

    html = open(html_path, "r", encoding="utf-8", errors="ignore").read()
    dom_root, errors = parse_html(html)

    css = ""
    if css_path:
        css = open(css_path, "r", encoding="utf-8", errors="ignore").read()

    parser = CSSParser()
    rules = parser.parse_css(css)
    apply_css_to_dom(dom_root, rules)

    layout_root = build_layout_tree(dom_root, viewport_width=800)

    print("=== LAYOUT (positions & tailles) ===")
    print(layout_to_string(layout_root))

    out = html_path + ".layout.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(layout_to_string(layout_root))
    print(f"\nLayout sauvegardé → {out}")

    if errors:
        print("\n=== Avertissements parsing HTML ===")
        for e in errors:
            print("-", e)

if __name__ == "__main__":
    main()
