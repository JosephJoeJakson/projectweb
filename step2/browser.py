import tkinter as tk
from tkinter import filedialog, messagebox
import os
from html_parser import parse_html, dom_to_string

class Browser:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Browser – Step 2 (HTML parsing)")
        self.dom = None

        top = tk.Frame(root); top.pack(side=tk.TOP, fill=tk.X)
        self.url_entry = tk.Entry(top); self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=4)
        self.url_entry.bind("<Return>", self.load_url)
        tk.Button(top, text="Load", command=self.load_url).pack(side=tk.LEFT, padx=4, pady=4)

        self.source_text = tk.Text(root, height=16); self.source_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(root, bg="white"); self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def load_url(self, event=None):
        url = self.url_entry.get().strip()
        if not url:
            path = filedialog.askopenfilename(title="Open HTML", filetypes=(("HTML","*.html;*.htm"),("All","*.*")))
            if not path: return
            url = path; self.url_entry.delete(0, tk.END); self.url_entry.insert(0, path)
        if not os.path.exists(url):
            messagebox.showerror("Error", f"File not found:\n{url}"); return

        with open(url, "r", encoding="utf-8") as f:
            html = f.read()

        self.dom = parse_html(html)
        self.source_text.delete("1.0", tk.END)
        self.source_text.insert(tk.END, html + "\n\n----- DOM -----\n" + dom_to_string(self.dom))
        self.canvas.delete("all")  # rendering comes later

if __name__ == "__main__":
    root = tk.Tk(); root.geometry("900x700")
    Browser(root); root.mainloop()
