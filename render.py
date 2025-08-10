import tkinter as tk
from tkinter.font import Font

class Renderer:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=800, height=600, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.default_font = Font(family="Arial", size=12)
    
    def render_layout(self, layout_box):
        self.canvas.delete("all")
        if layout_box:
            self._render_box(layout_box)
    
    def _render_box(self, box):
        if not box.dom_node:
            return

        style = box.dom_node.styles
        
        # Get background color
        bg_color = self._clean_color(style.get('background-color', 'white'))
        
        # Get border properties
        border_width = max(0, int(self._parse_px(style.get('border-width', '0'))))
        border_color = self._clean_color(style.get('border-color', 'black'))
        border_style = style.get('border-style', 'solid')
        
        # Draw background
        self.canvas.create_rectangle(
            box.x, box.y, 
            box.x + box.width, box.y + box.height,
            fill=bg_color,
            outline='' if border_width == 0 else border_color,
            width=border_width,
            dash=self._get_border_dash(border_style)
        )
        
        # Draw text
        if box.dom_node.text:
            text_color = self._clean_color(style.get('color', 'black'))
            font_size = int(self._parse_px(style.get('font-size', '12px')))
            font_family = style.get('font-family', 'Arial').strip('"\'')

            try:
                font = Font(family=font_family, size=font_size)
                self.canvas.create_text(
                    box.x + 10, box.y + 10,
                    text=box.dom_node.text,
                    anchor=tk.NW,
                    fill=text_color,
                    font=font,
                    width=box.width - 20
                )
            except tk.TclError:
                # Fallback to default font
                self.canvas.create_text(
                    box.x + 10, box.y + 10,
                    text=box.dom_node.text,
                    anchor=tk.NW,
                    fill=text_color,
                    font=self.default_font,
                    width=box.width - 20
                )
        
        # Render children
        for child in box.children:
            self._render_box(child)
    
    def _clean_color(self, color):
        if not color:
            return 'black'
        color = str(color).strip().strip('"\'')
        if color.startswith('#'):
            return color.lower()
        return color.lower()  # For named colors
    
    def _parse_px(self, value):
        if isinstance(value, str):
            if value.endswith('px'):
                return float(value[:-2])
            try:
                return float(value)
            except ValueError:
                return 0
        return value
    
    def _get_border_dash(self, style):
        if style == 'dashed':
            return (5, 5)
        elif style == 'dotted':
            return (2, 2)
        return None  # solid