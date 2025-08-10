from html_parser import DOMNode
from tkinter import font as tkfont
import math

class LayoutBox:
    def __init__(self, dom_node):
        self.dom_node = dom_node
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.children = []
        self.content_width = 0
        self.line_height = 20  # Default line height
    
    def layout(self, containing_block):
        self._calculate_width(containing_block)
        self._calculate_position(containing_block)
        self._calculate_height()
        self._layout_children()
    
    def _calculate_width(self, containing_block):
        style = self.dom_node.styles
        
        # Get box model properties
        margin_left = self._parse_px(style.get('margin-left', '0'))
        margin_right = self._parse_px(style.get('margin-right', '0'))
        padding_left = self._parse_px(style.get('padding-left', '0'))
        padding_right = self._parse_px(style.get('padding-right', '0'))
        border_left = self._parse_px(style.get('border-left-width', '0'))
        border_right = self._parse_px(style.get('border-right-width', '0'))
        
        # Calculate available width
        available_width = containing_block.content_width - margin_left - margin_right
        
        if 'width' in style:
            self.width = min(self._parse_px(style['width']), available_width)
        else:
            self.width = available_width
        
        self.content_width = max(0, self.width - padding_left - padding_right - border_left - border_right)
    
    def _calculate_position(self, containing_block):
        style = self.dom_node.styles
        
        margin_top = self._parse_px(style.get('margin-top', '0'))
        margin_left = self._parse_px(style.get('margin-left', '0'))
        
        # Block-level positioning (simple flow layout)
        self.x = containing_block.x + margin_left
        self.y = containing_block.y + containing_block.height + margin_top
    
    def _calculate_height(self):
        style = self.dom_node.styles
        
        if 'height' in style:
            self.height = self._parse_px(style['height'])
        else:
            # Calculate text height based on content
            text = self.dom_node.text or ''
            font_size = self._parse_px(style.get('font-size', '16px'))
            self.line_height = font_size * 1.2  # Standard line-height ratio
            
            # Approximate number of lines needed
            avg_char_width = font_size * 0.6  # Approximate character width
            if self.content_width > 0 and avg_char_width > 0:
                chars_per_line = max(10, self.content_width / avg_char_width)
                num_lines = math.ceil(len(text) / chars_per_line)
            else:
                num_lines = 1
            
            padding_top = self._parse_px(style.get('padding-top', '0'))
            padding_bottom = self._parse_px(style.get('padding-bottom', '0'))
            border_top = self._parse_px(style.get('border-top-width', '0'))
            border_bottom = self._parse_px(style.get('border-bottom-width', '0'))
            
            content_height = num_lines * self.line_height
            self.height = content_height + padding_top + padding_bottom + border_top + border_bottom
    
    def _layout_children(self):
        for child in self.dom_node.children:
            child_box = LayoutBox(child)
            child_box.layout(self)
            self.children.append(child_box)
            self.height += child_box.height  # Accumulate children's height
    
    def _parse_px(self, value):
        """Convert CSS pixel value to float"""
        if isinstance(value, str):
            if value.endswith('px'):
                return float(value[:-2])
            try:
                return float(value)
            except ValueError:
                return 0
        elif isinstance(value, (int, float)):
            return float(value)
        return 0

def build_layout_tree(dom_node):
    if not dom_node:
        return None
    
    # Create viewport with reasonable defaults
    viewport_node = DOMNode('viewport')
    viewport_node.styles = {
        'width': '800',
        'height': '600'
    }
    
    viewport = LayoutBox(viewport_node)
    viewport.width = 800
    viewport.height = 600
    viewport.content_width = 800  # Content width matches viewport width
    
    root_box = LayoutBox(dom_node)
    root_box.layout(viewport)
    return root_box