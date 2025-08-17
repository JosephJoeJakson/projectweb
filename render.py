import tkinter as tk
from tkinter.font import Font

# Public API --------------------------------------------------------------

def render_layout(canvas: tk.Canvas, dom_root, css_rules):
    """
    Render the DOM tree to the given Tkinter canvas using a simple block layout.
    """
    canvas.delete("all")
    if dom_root is None:
        return

    # Apply CSS (very basic: tag, .class, #id)
    _apply_css(dom_root, css_rules)

    # Canvas size fallback if not realized yet
    try:
        total_width = int(canvas.winfo_width())
        total_height = int(canvas.winfo_height())
        if total_width <= 1: total_width = 800
        if total_height <= 1: total_height = 600
    except Exception:
        total_width, total_height = 800, 600

    # Page backdrop
    canvas.create_rectangle(0, 0, total_width, total_height, fill="white", outline="")

    # Lay out from (10, 10) inward with small page margins
    _paint_node(canvas, dom_root, x=10, y=10, max_width=total_width - 20)

def render(canvas: tk.Canvas, dom_root, css_rules):
    """Backward-compatible alias some earlier versions used."""
    render_layout(canvas, dom_root, css_rules)

# CSS application ---------------------------------------------------------

def _apply_css(node, rules):
    """Populate node.styles by applying simple rules (tag, .class, #id)."""
    if not hasattr(node, "styles") or node.styles is None:
        node.styles = {}

    for rule in rules or []:
        # Accept either 'selectors': [...] OR legacy 'selector': '...'
        sels = list(rule.get("selectors", []) or [])
        if not sels and "selector" in rule:
            sels = [rule["selector"]]
        for sel in sels:
            if _matches_selector(node, sel):
                for prop, val in (rule.get("style", {}) or {}).items():
                    node.styles[prop] = val

    # Default indentation for lists if author CSS didn't set it
    tag = getattr(node, "tag", "").lower()
    if tag in ("ul", "ol"):
        node.styles.setdefault("margin-left", "20px")
        node.styles.setdefault("margin-bottom", "8px")

    for child in getattr(node, "children", []) or []:
        _apply_css(child, rules)

def _matches_selector(node, selector: str) -> bool:
    selector = (selector or "").strip()
    if not selector:
        return False
    attrs = getattr(node, "attributes", {}) or {}
    tag = getattr(node, "tag", "").lower()

    if selector.startswith("."):
        cls = selector[1:]
        classes = (attrs.get("class") or "").split()
        return cls in classes
    if selector.startswith("#"):
        return attrs.get("id") == selector[1:]
    return tag == selector.lower()

# Utilities ---------------------------------------------------------------

def _get_style(node, name, default=None):
    styles = getattr(node, "styles", {}) or {}
    return styles.get(name, default)

def _px(value, default=0.0):
    if value is None:
        return float(default)
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s.endswith("px"):
        s = s[:-2]
    try:
        return float(s)
    except Exception:
        return float(default)

def _color(value, default=None):
    if value in (None, "", "transparent"):
        return default
    return str(value)

def _heading_font_size(tag):
    sizes = {"h1": 28, "h2": 24, "h3": 20, "h4": 18, "h5": 16, "h6": 15}
    return sizes.get(tag.lower(), None)

def _font_for(node):
    # base size & family
    base_size = int(_px(_get_style(node, "font-size", 14), 14))
    family = _get_style(node, "font-family", "Arial")

    # heading autosizes if not explicitly set
    tag = getattr(node, "tag", "").lower()
    if tag in ("h1","h2","h3","h4","h5","h6") and _get_style(node, "font-size", None) is None:
        base_size = _heading_font_size(tag) or base_size

    # bold/italic from tag or style
    weight = "normal"
    slant = "roman"
    if tag in ("b", "strong"):
        weight = "bold"
    if tag in ("i", "em"):
        slant = "italic"

    fw = (_get_style(node, "font-weight", "") or "").lower()
    if fw in ("bold", "700", "800", "900"):
        weight = "bold"
    fs = (_get_style(node, "font-style", "") or "").lower()
    if fs == "italic":
        slant = "italic"

    try:
        return Font(name=None, exists=False, family=family, size=base_size, weight=weight, slant=slant)
    except Exception:
        return Font(name=None, exists=False, family="Arial", size=base_size, weight=weight, slant=slant)

def _text_bbox(canvas, text, font):
    item = canvas.create_text(0, 0, anchor="nw", text=text, font=font, state="hidden")
    bbox = canvas.bbox(item)
    canvas.delete(item)
    return bbox or (0, 0, 0, 0)

def _wrap_text(canvas, text, font, max_width):
    words = (text or "").split()
    if not words:
        return []
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        x1, y1, x2, y2 = _text_bbox(canvas, test, font)
        if (x2 - x1) <= max_width or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

# Measurement pass --------------------------------------------------------

def _measure_and_metrics(canvas, node, content_width):
    """Return (total_height, lines, line_height, text_height, font) for node."""
    pad_t = _px(_get_style(node, "padding-top", 4))
    pad_b = _px(_get_style(node, "padding-bottom", 4))
    border_w = _px(_get_style(node, "border-width", 0))

    font = _font_for(node)
    text = (getattr(node, "text", "") or "").strip()
    lines = _wrap_text(canvas, text, font, content_width) if text else []
    line_height = int(font.metrics("linespace") or 16)
    text_height = line_height * len(lines) if lines else 0

    children_total = 0.0
    for child in getattr(node, "children", []) or []:
        ch_total, *_ = _measure_and_metrics(canvas, child, content_width)
        children_total += ch_total

    total_height = border_w + pad_t + text_height + children_total + pad_b + border_w
    return total_height, lines, line_height, text_height, font

# Painting pass -----------------------------------------------------------

def _paint_node(canvas, node, x, y, max_width):
    """
    Paint one node and its subtree. Returns y of next line (after margin-bottom).
    """
    tag = getattr(node, "tag", "").lower()

    # Do not paint head/style/script
    if tag in ("head", "style", "script"):
        return y

    # Margins / padding / border
    margin_t = _px(_get_style(node, "margin-top", 0))
    margin_b = _px(_get_style(node, "margin-bottom", 8))  # simple block spacing
    margin_l = _px(_get_style(node, "margin-left", 0))
    margin_r = _px(_get_style(node, "margin-right", 0))

    pad_t = _px(_get_style(node, "padding-top", 4))
    pad_b = _px(_get_style(node, "padding-bottom", 4))
    pad_l = _px(_get_style(node, "padding-left", 6))
    pad_r = _px(_get_style(node, "padding-right", 6))

    border_w = _px(_get_style(node, "border-width", 0))
    border_color = _color(_get_style(node, "border-color", "#000"), "#000")
    bg = _color(_get_style(node, "background-color", None), None)

    # Width resolution
    declared_w = _get_style(node, "width", None)
    if declared_w is not None:
        content_width = max(0.0, _px(declared_w))
        total_w = content_width + pad_l + pad_r + 2 * border_w
    else:
        total_w = max(0.0, max_width - margin_l - margin_r)
        content_width = max(0.0, total_w - pad_l - pad_r - 2 * border_w)

    # Position after top/left margins
    cur_x = x + margin_l
    cur_y = y + margin_t

    # Measure first so we can paint backgrounds BEFORE children
    total_inner_h, lines, line_h, text_h, font = _measure_and_metrics(canvas, node, content_width)
    total_h = total_inner_h  # includes border+padding+text+children

    # Background & border FIRST
    x1, y1 = cur_x, cur_y
    x2, y2 = cur_x + total_w, cur_y + total_h
    if bg:
        canvas.create_rectangle(x1, y1, x2, y2, fill=bg, outline="")
    if border_w > 0:
        canvas.create_rectangle(x1, y1, x2, y2, outline=border_color, width=border_w)

    # Text drawing (with bullet for <li>)
    text_color = _color(_get_style(node, "color", "black"), "black")
    ty = cur_y + border_w + pad_t
    is_li = (tag == "li")

    if lines:
        if is_li:
            bullet_x = cur_x + border_w + max(2.0, pad_l * 0.3)
            bullet_y = ty
            canvas.create_text(bullet_x, bullet_y, anchor="nw", font=_font_for(node), fill=text_color, text="•")
            text_start_x = cur_x + border_w + pad_l + 12  # room for bullet
        else:
            text_start_x = cur_x + border_w + pad_l

        for line in lines:
            canvas.create_text(text_start_x, ty, anchor="nw", font=font, fill=text_color, text=line)
            ty += line_h

    # Then draw children on top
    child_y = cur_y + border_w + pad_t + text_h
    for child in getattr(node, "children", []) or []:
        child_y = _paint_node(canvas, child,
                              x=cur_x + border_w + pad_l,
                              y=child_y,
                              max_width=content_width)

    # Return next y after this block (including bottom margin)
    return y2 + margin_b
