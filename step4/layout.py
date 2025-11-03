
# Step 4 — Layout Engine : box model + block/inline + position: static/relative/absolute
# Modèle volontairement simplifié pour l'enseignement.

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

# ------------- Utils -------------
def _px(v, default: float = 0.0) -> float:
    """Parse a CSS length "12px" → 12.0. Accepts numbers. None → default."""
    if v is None:
        return float(default)
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s.endswith("px"):
        s = s[:-2]
    try:
        return float(s)
    except Exception:
        return float(default)

def _display_for_tag(tag: str) -> str:
    # very small default mapping
    inline_tags = {"span","a","strong","em","b","i","u","small","img"}
    return "inline" if tag in inline_tags else "block"

def _style(node) -> Dict[str, Any]:
    return getattr(node, "styles", {}) or {}

def _children(node):
    return getattr(node, "children", []) or []

# ------------- Data model -------------
@dataclass
class Dimensions:
    content_w: float = 0
    content_h: float = 0
    padding_top: float = 0
    padding_right: float = 0
    padding_bottom: float = 0
    padding_left: float = 0
    border_top: float = 0
    border_right: float = 0
    border_bottom: float = 0
    border_left: float = 0
    margin_top: float = 0
    margin_right: float = 0
    margin_bottom: float = 0
    margin_left: float = 0

    @property
    def total_w(self) -> float:
        return (self.margin_left + self.border_left + self.padding_left +
                self.content_w +
                self.padding_right + self.border_right + self.margin_right)

    @property
    def total_h(self) -> float:
        return (self.margin_top + self.border_top + self.padding_top +
                self.content_h +
                self.padding_bottom + self.border_bottom + self.margin_bottom)

@dataclass
class LayoutBox:
    node: Any
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0
    dims: Dimensions = field(default_factory=Dimensions)
    children: List['LayoutBox'] = field(default_factory=list)
    position: str = "static"
    display: str = "block"

    def add_child(self, child: 'LayoutBox'):
        self.children.append(child)

# ------------- Core API -------------
def build_layout_tree(dom_root, viewport_width: float = 800) -> LayoutBox:
    """Build + layout the tree. Returns the root LayoutBox positioned at (0,0)."""
    root = _layout_node(dom_root, viewport_width, 0, 0, containing_block=None)
    return root

# ------------- Layout algorithms -------------
def _compute_box_model(node, containing_width: float) -> Dimensions:
    st = _style(node)
    d = Dimensions()
    # margin
    d.margin_top = _px(st.get("margin-top"))
    d.margin_right = _px(st.get("margin-right"))
    d.margin_bottom = _px(st.get("margin-bottom"))
    d.margin_left = _px(st.get("margin-left"))
    # padding
    d.padding_top = _px(st.get("padding-top"))
    d.padding_right = _px(st.get("padding-right"))
    d.padding_bottom = _px(st.get("padding-bottom"))
    d.padding_left = _px(st.get("padding-left"))
    # border (treat width only)
    d.border_top = _px(st.get("border-top-width"))
    d.border_right = _px(st.get("border-right-width"))
    d.border_bottom = _px(st.get("border-bottom-width"))
    d.border_left = _px(st.get("border-left-width"))
    # width/height (content)
    declared_w = st.get("width")
    if declared_w:
        d.content_w = max(0.0, _px(declared_w))
    else:
        # default: fill available width for block elements, shrink for inline
        pass  # computed later depending on display
    declared_h = st.get("height")
    if declared_h:
        d.content_h = max(0.0, _px(declared_h))
    return d

def _layout_node(node, avail_w: float, cur_x: float, cur_y: float, containing_block: Optional[LayoutBox]) -> LayoutBox:
    st = _style(node)
    display = st.get("display", _display_for_tag(getattr(node,"tag","div")))
    position = st.get("position", "static")

    # Create box
    box = LayoutBox(node=node, position=position, display=display)
    box.dims = _compute_box_model(node, avail_w)

    # Determine containing block for absolute
    positioned_ancestor = containing_block
    if position != "static":
        # climb to nearest positioned ancestor (not static)
        pa = containing_block
        while pa is not None and pa.position == "static":
            pa = _get_parent_layout(pa)
        positioned_ancestor = pa or containing_block

    # Layout based on display
    if display == "block":
        _layout_block(node, box, avail_w, cur_x, cur_y, containing_block)
    else:
        _layout_inline(node, box, avail_w, cur_x, cur_y, containing_block)

    # Positioning adjustments
    if position == "relative":
        top = _px(st.get("top"))
        left = _px(st.get("left"))
        right = _px(st.get("right"))
        bottom = _px(st.get("bottom"))
        # Only use top/left if provided; simplistic
        box.x += left - right
        box.y += top - bottom
    elif position == "absolute":
        ref = positioned_ancestor or containing_block
        ref_x = 0 if ref is None else ref.x
        ref_y = 0 if ref is None else ref.y
        # Resolve offsets relative to ref padding box (simplified)
        top = st.get("top"); left = st.get("left"); right = st.get("right"); bottom = st.get("bottom")
        if left is not None:
            box.x = ref_x + _px(left)
        elif right is not None and ref is not None:
            box.x = ref_x + (ref.w - box.w - _px(right))
        if top is not None:
            box.y = ref_y + _px(top)
        elif bottom is not None and ref is not None:
            box.y = ref_y + (ref.h - box.h - _px(bottom))

    return box

# We keep a weak map from node to layout for traversing ancestors when needed
_NODE_TO_LAYOUT: Dict[int, LayoutBox] = {}

def _remember_layout(box: LayoutBox):
    _NODE_TO_LAYOUT[id(box.node)] = box

def _get_parent_layout(box: Optional[LayoutBox]) -> Optional[LayoutBox]:
    if box is None: return None
    parent = getattr(box.node, "parent", None)
    if parent is None: return None
    return _NODE_TO_LAYOUT.get(id(parent))

def _layout_block(node, box: LayoutBox, avail_w: float, cur_x: float, cur_y: float, containing_block: Optional[LayoutBox]):
    st = _style(node)
    d = box.dims

    # Compute content width:
    if d.content_w == 0:
        # fill available width minus horizontal non-content space
        non_content = d.padding_left + d.border_left + d.padding_right + d.border_right + d.margin_left + d.margin_right
        content_w = max(0.0, avail_w - non_content)
        d.content_w = content_w

    # Place this block (x,y for the content box)
    box.x = cur_x + d.margin_left + d.border_left + d.padding_left
    box.y = cur_y + d.margin_top + d.border_top + d.padding_top

    # Children layout: stack vertically
    child_y = box.y
    max_child_w = 0.0
    for child in _children(node):
        child_box = _layout_node(child, d.content_w, box.x, child_y, containing_block=box)
        box.add_child(child_box)
        _remember_layout(child_box)
        child_y = child_box.y + child_box.h + _get_extra_box_space(child_box)  # already includes margins
        max_child_w = max(max_child_w, child_box.w)

    # Compute content height
    if d.content_h == 0:
        # compute based on last child's bottom relative to content top
        if box.children:
            last = box.children[-1]
            bottom = last.y + last.h - box.y
            d.content_h = max(0.0, bottom)
        else:
            d.content_h = 0.0

    # Width/height of the border box
    box.w = d.content_w + d.padding_left + d.padding_right + d.border_left + d.border_right
    box.h = d.content_h + d.padding_top + d.padding_bottom + d.border_top + d.border_bottom

def _get_extra_box_space(box: LayoutBox) -> float:
    # Return bottom margin+border+padding already included in box.h? For stacking, we only need margin-bottom.
    return box.dims.margin_bottom

def _layout_inline(node, box: LayoutBox, avail_w: float, cur_x: float, cur_y: float, containing_block: Optional[LayoutBox]):
    # Naive text measurement: every character = 8px width, 16px line-height.
    st = _style(node)
    d = box.dims
    char_w = 8.0
    line_h = 16.0

    text = (getattr(node, "text", "") or "").replace("\\n", " ")
    # include inline children as words (we keep it simple: measure text only)
    words = [w for w in text.split(" ") if w != ""]
    x = cur_x + d.margin_left + d.border_left + d.padding_left
    y = cur_y + d.margin_top + d.border_top + d.padding_top
    max_x = x
    used_h = line_h
    space_w = char_w  # one space
    current_x = x
    for i, w in enumerate(words):
        w_w = len(w) * char_w
        if i != 0 and current_x + space_w + w_w > cur_x + avail_w - (d.margin_right + d.border_right + d.padding_right):
            # wrap
            y += line_h
            used_h += line_h
            current_x = x
        if i != 0:
            current_x += space_w
        current_x += w_w
        max_x = max(max_x, current_x)

    content_w = max(0.0, max_x - x)
    content_h = used_h if words else 0.0
    if d.content_w == 0:
        d.content_w = content_w
    if d.content_h == 0:
        d.content_h = content_h

    box.x = x
    box.y = y
    box.w = d.content_w + d.padding_left + d.padding_right + d.border_left + d.border_right
    box.h = d.content_h + d.padding_top + d.padding_bottom + d.border_top + d.border_bottom

def layout_to_string(box: LayoutBox, indent: int = 0) -> str:
    if box is None:
        return ""
    pad = "  " * indent
    node = box.node
    attrs = getattr(node, "attributes", {}) or {}
    st = _style(node)
    cls = attrs.get("class"); _id = attrs.get("id")
    head = f'{pad}<{getattr(node,"tag","?")} id={_id} class={cls} display={box.display} position={box.position}> x={box.x:.0f} y={box.y:.0f} w={box.w:.0f} h={box.h:.0f}'
    lines = [head]
    for c in box.children:
        lines.append(layout_to_string(c, indent+1))
    lines.append(f"{pad}</{getattr(node,'tag','?')}>")
    return "\n".join(lines)
