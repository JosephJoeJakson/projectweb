import tkinter as tk
from tkinter.font import Font

def render_layout(canvas: tk.Canvas, dom_root, css_rules):
    canvas.delete("all")
    if dom_root is None: return
    _apply_css(dom_root, css_rules)
    try:
        w = max(800, int(canvas.winfo_width())); h = max(600, int(canvas.winfo_height()))
    except Exception:
        w, h = 800, 600
    canvas.create_rectangle(0,0,w,h, fill="white", outline="")
    _paint_node(canvas, dom_root, 10, 10, w-20)

def _apply_css(node, rules):
    node.styles = node.styles or {}
    for r in rules or []:
        sels=list(r.get("selectors",[]) or [])
        if not sels and "selector" in r: sels=[r["selector"]]
        for s in sels:
            if _match(node,s): node.styles.update(r.get("style",{}) or {})
    for c in getattr(node,"children",[]): _apply_css(c, rules)

def _match(node, sel):
    sel=(sel or "").strip()
    if not sel: return False
    tag=node.tag.lower(); attrs=node.attributes
    if sel.startswith("."): return sel[1:] in (attrs.get("class") or "").split()
    if sel.startswith("#"): return attrs.get("id")==sel[1:]
    return tag==sel.lower()

def _get(n, key, default=None): return (n.styles or {}).get(key, default)
def _px(v, d=0.0):
    if v is None: return float(d)
    if isinstance(v,(int,float)): return float(v)
    s=str(v).strip();  s=s[:-2] if s.endswith("px") else s
    try: return float(s)
    except: return float(d)
def _color(v, d=None): return d if v in (None,"","transparent") else str(v)

def _heading_size(tag): return {"h1":28,"h2":24,"h3":20,"h4":18,"h5":16,"h6":15}.get(tag, None)

def _font_for(node):
    size=int(_px(_get(node,"font-size",14),14)); fam=_get(node,"font-family","Arial")
    try: return Font(name=None, exists=False, family=fam, size=size)
    except: return Font(name=None, exists=False, family="Arial", size=size)

def _bbox(canvas, text, font):
    i=canvas.create_text(0,0,anchor="nw",text=text,font=font,state="hidden"); b=canvas.bbox(i); canvas.delete(i)
    return b or (0,0,0,0)

def _wrap(canvas, text, font, max_w):
    ws=(text or "").split()
    if not ws: return []
    lines=[]; cur=""
    for w in ws:
        t=(cur+" "+w).strip()
        x1,y1,x2,y2=_bbox(canvas,t,font)
        if (x2-x1) <= max_w or not cur: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines

def _paint_node(canvas, node, x, y, max_w):
    tag=node.tag.lower()
    if tag in ("head","style","script"): return y

    m_t=_px(_get(node,"margin-top",0)); m_b=_px(_get(node,"margin-bottom",8))
    m_l=_px(_get(node,"margin-left",0)); m_r=_px(_get(node,"margin-right",0))
    p_t=_px(_get(node,"padding-top",4)); p_b=_px(_get(node,"padding-bottom",4))
    p_l=_px(_get(node,"padding-left",6)); p_r=_px(_get(node,"padding-right",6))
    bw=_px(_get(node,"border-width",0)); bcol=_color(_get(node,"border-color","#000"),"#000")
    bg=_color(_get(node,"background-color",None),None)

    declared=_get(node,"width",None)
    if declared is not None:
        content_w=max(0.0,_px(declared)); total_w=content_w+p_l+p_r+2*bw
    else:
        total_w=max(0.0,max_w-m_l-m_r); content_w=max(0.0,total_w-p_l-p_r-2*bw)

    cur_x=x+m_l; cur_y=y+m_t

    font=_font_for(node); text=(node.text or "").strip()
    line_h=int(font.metrics("linespace") or 16)
    lines=_wrap(canvas,text,font,content_w); text_h=line_h*len(lines)

    x1,y1=cur_x,cur_y; x2,y2=cur_x+total_w,cur_y+(p_t+text_h+p_b+2*bw)
    if bg: canvas.create_rectangle(x1,y1,x2,y2,fill=bg,outline="")
    if bw>0: canvas.create_rectangle(x1,y1,x2,y2,outline=bcol,width=bw)

    ty=cur_y+bw+p_t
    for line in lines:
        canvas.create_text(cur_x+bw+p_l,ty,anchor="nw",font=font,fill=_color(_get(node,"color","black"),"black"),text=line)
        ty+=line_h

    child_y=cur_y+bw+p_t+text_h
    for c in node.children:
        child_y=_paint_node(canvas,c,cur_x+bw+p_l,child_y,content_w)

    return y2+m_b
