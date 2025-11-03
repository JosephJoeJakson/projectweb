
# Step 5 — Rendering Tkinter: backgrounds, borders, text + simple z-index
import sys
import tkinter as tk
from tkinter.font import Font
from typing import Any, List, Tuple

from html_parser import parse_html
from css_parser import CSSParser, apply_css_to_dom
from layout import build_layout_tree

# ---------- Style helpers ----------
def _get(node, name, default=None):
    try:
        return (node.styles or {}).get(name, default)
    except Exception:
        return default

def _px(v, default=0.0):
    if v is None: return float(default)
    if isinstance(v, (int, float)): return float(v)
    s = str(v).strip()
    if s.endswith("px"): s = s[:-2]
    try: return float(s)
    except: return float(default)

def _color(v, default=None):
    if not v: return default
    s = str(v).strip()
    # Accept e.g. "#rrggbb" or color names; Tkinter will resolve common names.
    return s

def _font_for(node):
    fam = _get(node, "font-family", "TkDefaultFont")
    size = int(_px(_get(node, "font-size", 12), 12))
    weight = "bold" if str(_get(node, "font-weight", "")).lower() in ("bold","700","800","900") else "normal"
    slant = "italic" if str(_get(node, "font-style", "")).lower() == "italic" else "roman"
    return (fam, size, weight)

# ---------- Render primitives ----------
def _draw_background(canvas: tk.Canvas, box) -> None:
    st = getattr(box.node, "styles", {}) or {}
    bg = _color(st.get("background-color"))
    if not bg: return
    d = box.dims
    # Paint to the padding-box (CSS default)
    x0 = box.x - d.padding_left - d.border_left
    y0 = box.y - d.padding_top - d.border_top
    x1 = box.x + box.w + d.padding_right + d.border_right - (d.padding_left + d.border_left)
    y1 = box.y + box.h + d.padding_bottom + d.border_bottom - (d.padding_top + d.border_top)
    canvas.create_rectangle(x0, y0, x1, y1, outline="", fill=bg)

def _draw_borders(canvas: tk.Canvas, box) -> None:
    st = getattr(box.node, "styles", {}) or {}
    d = box.dims

    # Colors
    col = _color(st.get("border-color"), "#000")
    col_top    = _color(st.get("border-top-color"), col)
    col_right  = _color(st.get("border-right-color"), col)
    col_bottom = _color(st.get("border-bottom-color"), col)
    col_left   = _color(st.get("border-left-color"), col)

    # Widths
    wt = _px(st.get("border-top-width"), d.border_top or 0)
    wr = _px(st.get("border-right-width"), d.border_right or 0)
    wb = _px(st.get("border-bottom-width"), d.border_bottom or 0)
    wl = _px(st.get("border-left-width"), d.border_left or 0)

    x = box.x
    y = box.y
    w = box.w
    h = box.h

    # Top
    if wt > 0:
        canvas.create_rectangle(x - wl, y - wt, x + w + wr, y, outline="", fill=col_top)
    # Bottom
    if wb > 0:
        canvas.create_rectangle(x - wl, y + h, x + w + wr, y + h + wb, outline="", fill=col_bottom)
    # Left
    if wl > 0:
        canvas.create_rectangle(x - wl, y - wt, x, y + h + wb, outline="", fill=col_left)
    # Right
    if wr > 0:
        canvas.create_rectangle(x + w, y - wt, x + w + wr, y + h + wb, outline="", fill=col_right)

def _content_box_xy(box):
    d = box.dims
    return (box.x, box.y)

def _content_box_wh(box):
    d = box.dims
    return (box.w, box.h)

def _draw_text(canvas: tk.Canvas, box) -> None:
    node = box.node
    text = (getattr(node, "text", "") or "").strip()
    if not text: return

    x, y = _content_box_xy(box)
    w, h = _content_box_wh(box)

    fill = _color(_get(node, "color"), "#000")
    font_tuple = _font_for(node)

    # Use wraplength so long lines don’t overflow; it is in pixels.
    canvas.create_text(x, y, anchor="nw", text=text, fill=fill, font=font_tuple, width=max(1, int(w)))

# ---------- Tree traversal & z-index ----------
def _flatten(box, out, order=[0]):
    if box is None: return
    order[0] += 1
    z = 0
    try:
        z = int(float((box.node.styles or {}).get("z-index", 0)))
    except Exception:
        z = 0
    out.append((z, order[0], box))
    for c in getattr(box, "children", []) or []:
        _flatten(c, out, order)

def render_layout(canvas: tk.Canvas, layout_root) -> None:
    if layout_root is None: return
    canvas.delete("all")

    flat: List[Tuple[int,int,Any]] = []
    _flatten(layout_root, flat)
    # Sort by z-index then document order
    flat.sort(key=lambda t: (t[0], t[1]))

    # First pass: backgrounds
    for _, _, b in flat:
        _draw_background(canvas, b)
    # Second: borders
    for _, _, b in flat:
        _draw_borders(canvas, b)
    # Third: text
    for _, _, b in flat:
        _draw_text(canvas, b)

# ---------- Demo / Tkinter integration ----------
class App:
    def __init__(self, html_path=None, css_path=None, viewport=(900, 700)):
        self.root = tk.Tk()
        self.root.title("Mini‑browser — Step 5 Rendering")
        self.canvas = tk.Canvas(self.root, width=viewport[0], height=viewport[1], bg="white")
        self.canvas.pack(fill="both", expand=True)

        # Load files (optional pickers if not provided)
        if not html_path:
            from tkinter.filedialog import askopenfilename
            html_path = askopenfilename(title="Choisir un fichier HTML", filetypes=[("HTML","*.html;*.htm"),("All","*.*")])
        css_text = ""
        if not css_path:
            # optional
            pass

        html_text = ""
        if html_path:
            with open(html_path, "r", encoding="utf-8") as f:
                html_text = f.read()
        if css_path:
            with open(css_path, "r", encoding="utf-8") as f:
                css_text = f.read()

        dom, _ = parse_html(html_text)

        # Apply CSS: file rules + inline style="..."
        parser = CSSParser()
        rules = parser.parse_css(css_text or "")
        apply_css_to_dom(dom, rules)
        self._merge_inline_styles(dom)

        # Compute layout (viewport width = current canvas width)
        vw = int(self.canvas.winfo_reqwidth() or 900)
        self.layout_root = build_layout_tree(dom, viewport_width=vw)

        # Initial render
        render_layout(self.canvas, self.layout_root)

        # Re-render on resize
        self.canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        # Recompute layout with new viewport width, then repaint
        w = max(200, int(event.width))
        # (Height is not required by our layout; we let content define scrollregion)
        # Rebuild DOM/styles? Keep same DOM, recompute layout:
        # For simplicity we don't re-parse; build_layout_tree is pure from DOM+styles.
        self.layout_root = build_layout_tree(self.layout_root.node, viewport_width=w)
        # Update scroll region to content bbox
        self.canvas.config(scrollregion=(0,0,max(w, int(self.layout_root.w + 40)), int(self.layout_root.h + 80)))
        render_layout(self.canvas, self.layout_root)

    def _merge_inline_styles(self, node):
        # Parse inline style="a:b; c:d" onto node.styles
        try:
            attrs = getattr(node, "attributes", {}) or {}
            style_attr = attrs.get("style")
            if style_attr:
                if node.styles is None:
                    node.styles = {}
                for p in style_attr.split(";"):
                    if ":" in p:
                        k, v = p.split(":", 1)
                        node.styles[k.strip()] = v.strip()
        except Exception:
            pass
        for c in getattr(node, "children", []) or []:
            self._merge_inline_styles(c)

def main():
    html = sys.argv[1] if len(sys.argv) >= 2 else None
    css  = sys.argv[2] if len(sys.argv) >= 3 else None
    App(html, css).root.mainloop()

if __name__ == "__main__":
    main()
