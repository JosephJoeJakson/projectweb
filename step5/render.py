import tkinter as tk
from tkinter.font import Font

def render_layout(canvas: tk.Canvas, dom_root, css_rules):
    canvas.delete("all")
    if dom_root is None: return
    _apply_css(dom_root, css_rules)

    try:
        w = max(800, int(canvas.winfo_width()))
        h = max(600, int(canvas.winfo_height()))
    except Exception:
        w, h = 800, 600

    canvas.create_rectangle(0,0,w,h, fill="white", outline="")
    _paint_node(canvas, dom_root, x=10, y=10, max_width=w-20)

def _apply_css(node, rules):
    node.styles = node.styles or {}
    for r in rules or []:
        sels = list(r.get("selectors", []) or [])
        if not sels and "selector" in r: sels = [r["selector"]]
        for s in sels:
            if _match(node, s): node.styles.update(r.get("style", {}))
    for c in getattr(node, "children", []): _apply_css(c, rules)

def _match(node, sel):
    sel = (sel or "").strip()
    if not sel: return False
    tag = node.tag.lower(); attrs = node.attributes
    if sel.startswith("."): return sel[1:] in (attrs.get("class") or "").split()
    if sel.startswith("#"): return attrs.get("id") == sel[1:]
    return tag == sel.lower()

def _get(node, name, default=None):
    return (node.styles or {}).get(name, default)

def _px(v, default=0.0):
    if v is None: return float(default)
    if isinstance(v,(int,float)): return float(v)
    s = str(v).strip()
    if s.endswith("px"): s = s[:-2]
    try: return float(s)
    except: return float(default)

def _color(v, default=None):
    if v in (None,"","transparent"): return default
    return str(v)

def _font_for(node):
    size = int(_px(_get(node,"font-size",14),14))
    fam = _get(node,"font-family","Arial")
    try: return Font(name=None, exists=False, family=fam, size=size)
    except: return Font(name=None, exists=False, family="Arial", size=size)

def _measure(canvas, text, font, max_w):
    item = canvas.create_text(0,0, anchor="nw", text=text, font=font, state="hidden")
    bbox = canvas.bbox(item); canvas.delete(item)
    w = (bbox[2]-bbox[0]) if bbox else 0
    return w

def _wrap(canvas, text, font, max_w):
    words = (text or "").split()
    if not words: return []
    lines=[]; cur=""
    for w in words:
        t = (cur+" "+w).strip()
        if _measure(canvas, t, font, max_w) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines

def _paint_node(canvas, node, x, y, max_width):
    tag = node.tag.lower()
    if tag in ("head","style","script"): return y

    m_t=_px(_get(node,"margin-top",0)); m_b=_px(_get(node,"margin-bottom",8))
    m_l=_px(_get(node,"margin-left",0)); m_r=_px(_get(node,"margin-right",0))
    p_t=_px(_get(node,"padding-top",4)); p_b=_px(_get(node,"padding-bottom",4))
    p_l=_px(_get(node,"padding-left",6)); p_r=_px(_get(node,"padding-right",6))
    bw=_px(_get(node,"border-width",0))
    bcol=_color(_get(node,"border-color","#000"),"#000")
    bg=_color(_get(node,"background-color",None),None)

    declared = _get(node,"width",None)
    if declared is not None:
        content_w = max(0.0, _px(declared))
        total_w = content_w + p_l + p_r + 2*bw
    else:
        total_w = max(0.0, max_width - m_l - m_r)
        content_w = max(0.0, total_w - p_l - p_r - 2*bw)

    cur_x = x + m_l; cur_y = y + m_t

    text = (node.text or "").strip()
    font = _font_for(node)
    line_h = int(font.metrics("linespace") or 16)
    lines = _wrap(canvas, text, font, content_w)
    text_h = line_h * len(lines)

    # background & border
    x1,y1 = cur_x, cur_y
    x2,y2 = cur_x + total_w, cur_y + (p_t + text_h + p_b + 2*bw)
    if bg: canvas.create_rectangle(x1,y1,x2,y2, fill=bg, outline="")
    if bw>0: canvas.create_rectangle(x1,y1,x2,y2, outline=bcol, width=bw)

    # draw text
    ty = cur_y + bw + p_t
    for line in lines:
        canvas.create_text(cur_x + bw + p_l, ty, anchor="nw", font=font, fill=_color(_get(node,"color","black"),"black"), text=line)
        ty += line_h

    # children
    child_y = cur_y + bw + p_t + text_h
    for c in node.children:
        child_y = _paint_node(canvas, c, x=cur_x + bw + p_l, y=child_y, max_width=content_w)

    return y2 + m_b
