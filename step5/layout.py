def _px(v, default=0):
    if v is None: return default
    if isinstance(v, (int,float)): return float(v)
    s = str(v).strip()
    if s.endswith("px"): s = s[:-2]
    try: return float(s)
    except: return default

class LBox:
    def __init__(self, node):
        self.node = node; self.children=[]; self.x=0; self.y=0; self.w=0; self.h=0; self.content_w=0

def _measure(node, containing_width):
    style = node.styles or {}
    pad_l=_px(style.get("padding-left",6)); pad_r=_px(style.get("padding-right",6))
    bor=_px(style.get("border-width",0)); mar_l=_px(style.get("margin-left",0)); mar_r=_px(style.get("margin-right",0))
    declared = style.get("width", None)
    if declared is not None:
        content_w = max(0.0, _px(declared))
        total_w = content_w + pad_l + pad_r + 2*bor
    else:
        total_w = max(0.0, containing_width - mar_l - mar_r)
        content_w = max(0.0, total_w - pad_l - pad_r - 2*bor)
    return total_w, content_w, pad_l, pad_r, bor, mar_l, mar_r

def build_layout_tree(dom_root, viewport_width=800):
    if dom_root is None: return None
    root = LBox(dom_root)
    def walk(node, box, x, y, max_w):
        total_w, content_w, pad_l, pad_r, bor, mar_l, mar_r = _measure(node, max_w)
        box.x = x + mar_l; box.y = y; box.w = total_w; box.content_w = content_w
        ty = y + _px(node.styles.get("padding-top",4)) + _px(node.styles.get("border-width",0))
        height = _px(node.styles.get("padding-top",4)) + _px(node.styles.get("padding-bottom",4)) + 2*_px(node.styles.get("border-width",0))
        for c in node.children:
            cb = LBox(c); box.children.append(cb)
            ty = walk(c, cb, box.x + _px(node.styles.get("border-width",0)) + pad_l, ty, content_w)
            height = max(height, ty - y)
        box.h = height + _px(node.styles.get("margin-bottom",8))
        return box.y + box.h
    walk(dom_root, root, 10, 10, viewport_width-20)
    return root

def layout_to_string(box, indent=0):
    if box is None: return ""
    pad = "  " * indent
    line = f'{pad}<{box.node.tag}> x={box.x:.0f} y={box.y:.0f} w={box.w:.0f} h={box.h:.0f}'
    out = [line]
    for c in box.children: out.append(layout_to_string(c, indent+1))
    return "\n".join(out)
