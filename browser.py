import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from html_parser import parse_html
from css_parser import CSSParser
from layout import build_layout_tree
from render import Renderer
from js_interpreter import JSInterpreter

class MiniBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Browser")
        
        # Create UI
        self.create_ui()
        
        # Initialize components
        self.css_parser = CSSParser()
        self.current_dom = None
        self.current_layout = None
    
    def create_ui(self):
        # URL bar
        self.url_frame = tk.Frame(self.root)
        self.url_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.url_label = tk.Label(self.url_frame, text="URL:")
        self.url_label.pack(side=tk.LEFT)
        
        self.url_entry = tk.Entry(self.url_frame)
        self.url_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.url_entry.bind("<Return>", self.load_url)
        
        self.load_button = tk.Button(self.url_frame, text="Load", command=self.load_url)
        self.load_button.pack(side=tk.LEFT)
        
        # View tabs
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(expand=True, fill=tk.BOTH)
        
        # Browser view tab
        self.browser_tab = tk.Frame(self.tab_control)
        self.tab_control.add(self.browser_tab, text="Browser")
        
        self.renderer = Renderer(self.browser_tab)
        
        # HTML source tab
        self.source_tab = tk.Frame(self.tab_control)
        self.tab_control.add(self.source_tab, text="Source")
        
        self.source_text = ScrolledText(self.source_tab, wrap=tk.WORD)
        self.source_text.pack(expand=True, fill=tk.BOTH)
    
    def load_url(self, event=None):
        url = self.url_entry.get()
        
        if url.startswith("file://"):
            file_path = url[7:]
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # For simplicity, we'll just handle local files
            file_path = filedialog.askopenfilename(
                title="Open HTML File",
                filetypes=(("HTML Files", "*.html"), ("All Files", "*.*")))
            if not file_path:
                return
            
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, f"file://{file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        self.source_text.delete(1.0, tk.END)
        self.source_text.insert(tk.END, content)
        
        self.render_content(content)
    
    def render_content(self, html_content):
        # Parse HTML
        self.current_dom = parse_html(html_content)
        
        # Find and parse CSS
        css_rules = []
        if self.current_dom:
            # Find <style> tags
            style_nodes = self._find_nodes_by_tag(self.current_dom, 'style')
            for node in style_nodes:
                css_content = node.text
                css_rules.extend(self.css_parser.parse_css(css_content))
            
            # Find external CSS (simplified)
            link_nodes = self._find_nodes_by_tag(self.current_dom, 'link')
            for node in link_nodes:
                if node.attributes.get('rel') == 'stylesheet':
                    # In a real browser, we'd fetch this file
                    pass
        
        # Apply CSS styles
        if self.current_dom and css_rules:
            self.css_parser.apply_styles(self.current_dom, css_rules)
        
        # Build layout
        self.current_layout = build_layout_tree(self.current_dom)
        
        # Render
        self.renderer.render_layout(self.current_layout)
        
        # Find and execute JavaScript (very simplified)
        script_nodes = self._find_nodes_by_tag(self.current_dom, 'script')
        for node in script_nodes:
            if node.text:
                js_interpreter = JSInterpreter(self.current_dom)
                js_interpreter.execute(node.text)
                
                # Re-render if DOM was modified
                self.current_layout = build_layout_tree(self.current_dom)
                self.renderer.render_layout(self.current_layout)
    
    def _find_nodes_by_tag(self, node, tag_name):
        nodes = []
        if node.tag == tag_name:
            nodes.append(node)
        for child in node.children:
            nodes.extend(self._find_nodes_by_tag(child, tag_name))
        return nodes

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1024x768")
    browser = MiniBrowser(root)
    root.mainloop()