# Step 6 — Rendu Tkinter + régions cliquables (pour onclick)
import tkinter as tk
from tkinter.font import Font

def _color(s, default=None):
    if not s: return default
    s = str(s).strip()
    return s

def _get(node, name, default=None):
    try:
        return (node.styles or {}).get(name, default)
    except Exception:
        return default

def _collect_boxes(root):
    out = []
    order = 0
    def walk(box):
        nonlocal order
        if not box: return
        try:
            z = int(float((box.node.styles or {}).get('z-index', 0)))
        except Exception:
            z = 0
        out.append((box, z, order)); order += 1
        for c in getattr(box, 'children', []):
            walk(c)
    walk(root)
    return out

def render_layout(canvas: tk.Canvas, layout_root):
    canvas.delete("all")
    if not layout_root: return []

    hit_regions = []  # (x1,y1,x2,y2,node) pour éléments cliquables
    flat = _collect_boxes(layout_root)
    flat.sort(key=lambda t: (t[1], t[2]))

    for (box, z, _ord) in flat:
        node = box.node
        st = node.styles or {}

        x1 = box.x; y1 = box.y
        h = max(0, box.h); w = max(0, box.w)

        bg = _color(_get(node, "background-color", None))
        bcol = _color(_get(node, "border-color", "black"))
        bw = float(_get(node, "border-width", 0) or 0)
        txt = (node.text or "").strip()
        col = _color(_get(node, "color", "black"))

        # Dessin
        if bg:
            canvas.create_rectangle(x1, y1, x1 + w, y1 + h, fill=bg, outline="")
        if bw > 0:
            canvas.create_rectangle(x1, y1, x1 + w, y1 + h, width=bw, outline=bcol)
        if txt:
            fs = int(float(_get(node, "font-size", 16) or 16))
            ff = str(_get(node, "font-family", "TkDefaultFont"))
            font = Font(family=ff, size=fs)
            pad_l = float(_get(node, "padding-left", 0) or 0)
            pad_t = float(_get(node, "padding-top", 0) or 0)
            bor = float(_get(node, "border-width", 0) or 0)
            canvas.create_text(x1 + bor + pad_l, y1 + bor + pad_t, anchor="nw", font=font, fill=col, text=txt)

        # Marquer comme cliquable si <button> ou class contient 'btn' (simplifié)
        try:
            attrs = node.attributes or {}
            classes = (attrs.get('class') or '').split()
            if node.tag == 'button' or 'btn' in classes:
                hit_regions.append((x1, y1, x1 + w, y1 + h, node))
        except Exception:
            pass

    return hit_regions


# ===== Step 6 additions: JS integration and click events =====
from js_runtime import JSRuntime, JSElement, dispatch_click
from layout import build_layout_tree

class Step6App(App):
    def __init__(self, html_path=None, css_path=None, viewport=(900,700)):
        super().__init__(html_path, css_path, viewport)
        self.jsrt = JSRuntime(self.layout_root.node, on_dom_change=self._on_dom_change)
        self._run_inline_scripts(self.layout_root.node)
        self._relayout_and_paint()
        self._install_click_bindings()
    def _run_inline_scripts(self, node):
        if getattr(node,'tag','').lower() == 'script':
            code = (getattr(node,'text','') or '').strip()
            if code:
                try: self.jsrt.eval(code)
                except Exception as e: print('JS error:', e)
        for c in getattr(node,'children',[]) or []: self._run_inline_scripts(c)
    def _on_dom_change(self):
        self._relayout_and_paint(); self._install_click_bindings()
    def _relayout_and_paint(self):
        w = int(self.canvas.winfo_width() or 900)
        self.layout_root = build_layout_tree(self.layout_root.node, viewport_width=w)
        render_layout(self.canvas, self.layout_root)
    def _install_click_bindings(self):
        self.canvas.tag_unbind('clickable', '<Button-1>'); self.canvas.dtag('all','clickable')
        def walk(b):
            _id = getattr(b.node,'attributes',{}).get('id')
            if _id:
                x0,y0,x1,y1 = b.x, b.y, b.x+b.w, b.y+b.h
                item = self.canvas.create_rectangle(x0,y0,x1,y1, outline='', fill='', tags=('clickable', _id))
            for c in getattr(b,'children',[]) or []: walk(c)
        walk(self.layout_root)
        self.canvas.tag_bind('clickable','<Button-1>', self._on_canvas_click)
    def _on_canvas_click(self, evt):
        items = self.canvas.find_overlapping(evt.x, evt.y, evt.x, evt.y)
        for it in items:
            tags = self.canvas.gettags(it)
            for t in tags:
                if t not in ('clickable',):
                    node = self._find_node_by_id(self.layout_root.node, t)
                    if node:
                        dispatch_click(self.jsrt, JSElement(node, self._on_dom_change))
                        return
    def _find_node_by_id(self, node, _id):
        if getattr(node,'attributes',{}).get('id') == _id: return node
        for c in getattr(node,'children',[]) or []:
            r = self._find_node_by_id(c, _id)
            if r: return r
        return None
