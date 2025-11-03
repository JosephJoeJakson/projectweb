# Step 6 — Layout (hérité de S4/S5) : on garde le moteur de layout identique
from math import ceil

def _px(v, default=0.0):
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s.endswith('px'):
        s = s[:-2]
    try:
        return float(s)
    except:
        return default

def _strut_font_size(node):
    try:
        return _px((node.styles or {}).get('font-size', 16), 16.0)
    except Exception:
        return 16.0

def _line_height(node):
    return ceil(1.2 * _strut_font_size(node))

def _text_width(text, node):
    if not text:
        return 0.0
    fs = _strut_font_size(node)
    return 0.6 * fs * len(text)

def _is_inline(node):
    disp = (node.styles or {}).get('display', '').lower()
    if disp in ('inline', 'inline-block'):
        return True
    return node.tag in ('span', 'a', 'b', 'i', 'em', 'strong')

class LBox:
    def __init__(self, node):
        self.node = node
        self.children = []
        self.x = 0.0; self.y = 0.0; self.w = 0.0; self.h = 0.0
        self.content_w = 0.0
        self.positioned = False
        self.is_inline = False

def _box_metrics(node, containing_width):
    st = node.styles or {}
    pad_l = _px(st.get('padding-left', 0))
    pad_r = _px(st.get('padding-right', 0))
    pad_t = _px(st.get('padding-top', 0))
    pad_b = _px(st.get('padding-bottom', 0))
    bor = _px(st.get('border-width', 0))
    mar_l = _px(st.get('margin-left', 0))
    mar_r = _px(st.get('margin-right', 0))
    mar_t = _px(st.get('margin-top', 0))
    mar_b = _px(st.get('margin-bottom', 0))
    declared_w = st.get('width', None)

    if declared_w is not None:
        content_w = max(0.0, _px(declared_w))
        total_w = content_w + pad_l + pad_r + 2*bor
    else:
        total_w = max(0.0, containing_width - mar_l - mar_r)
        content_w = max(0.0, total_w - pad_l - pad_r - 2*bor)

    return total_w, content_w, (pad_l, pad_r, pad_t, pad_b), bor, (mar_l, mar_r, mar_t, mar_b)

def _position_offsets(node):
    st = node.styles or {}
    top = st.get('top'); left = st.get('left')
    return _px(top, 0.0), _px(left, 0.0)

def build_layout_tree(dom_root, viewport_width=800):
    if dom_root is None:
        return None

    def walk(node, cur_x, cur_y, max_w, positioned_ancestor):
        box = LBox(node)
        st = node.styles or {}
        pos = (st.get('position') or 'static').lower()
        box.is_inline = _is_inline(node)

        total_w, content_w, pads, bor, mars = _box_metrics(node, max_w)
        pad_l, pad_r, pad_t, pad_b = pads
        mar_l, mar_r, mar_t, mar_b = mars

        line_h = _line_height(node) if box.is_inline or node.tag in ('p',) else 0

        if pos == 'absolute':
            box.positioned = True
            base_x = positioned_ancestor.x if positioned_ancestor else 0.0
            base_y = positioned_ancestor.y if positioned_ancestor else 0.0
            off_t, off_l = _position_offsets(node)
            box.x = base_x + off_l + mar_l
            box.y = base_y + off_t + mar_t
            box.w = total_w
            content_h = line_h if node.text.strip() else 0.0
            box.h = pad_t + content_h + pad_b + 2*bor
            for c in getattr(node, 'children', []):
                child = walk(c, box.x + pad_l + bor, box.y + pad_t + bor, content_w, positioned_ancestor=box)
                if child: box.children.append(child)
            return box

        x = cur_x + mar_l
        y = cur_y + mar_t
        box.x = x; box.y = y; box.w = total_w
        content_x = x + bor + pad_l; content_y = y + bor + pad_t

        if not box.is_inline:
            cursor_y = content_y
            for c in getattr(node, 'children', []):
                child = walk(c, content_x, cursor_y, content_w, positioned_ancestor)
                if child:
                    box.children.append(child)
                    cursor_y = max(cursor_y, child.y + child.h)
            content_h = cursor_y - content_y
            if node.text.strip():
                content_h += max(line_h, 0)
            box.h = (pad_t + content_h + pad_b + 2*bor) + mar_b
        else:
            tx = content_x; ty = content_y
            remaining = content_w
            text = node.text.strip()
            if text:
                words = text.split()
                line_h = max(line_h, _line_height(node))
                used_h = line_h; cur_w = 0.0
                for w in words:
                    ww = 0.6 * _line_height(node) * len(w + ' ')
                    if ww > remaining and cur_w > 0.0:
                        ty += line_h; used_h += line_h; remaining = content_w; cur_w = 0.0
                    remaining -= ww; cur_w += ww
                content_h = used_h
            else:
                content_h = 0.0
            child_y = ty
            for c in getattr(node, 'children', []):
                child = walk(c, content_x, child_y, content_w, positioned_ancestor)
                if child:
                    box.children.append(child)
                    child_y = max(child_y, child.y + child.h)
            content_h = max(content_h, child_y - content_y)
            box.h = (pad_t + content_h + pad_b + 2*bor) + mar_b

        if pos == 'relative':
            off_t, off_l = _position_offsets(node)
            box.x += off_l; box.y += off_t

        return box

    return walk(dom_root, 10.0, 10.0, viewport_width - 20.0, positioned_ancestor=None)
