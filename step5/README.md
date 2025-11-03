# Step 5 — Rendering avec Tkinter (Cours S5)

**Objectif livrable :** convertir l'arbre de **layout** en **rendu visuel** sur un **Canvas Tkinter** :
- Dessiner **arrière-plans**, **bordures** et **texte**.
- Respecter les positions/tailles issues du layout.
- Implémenter un **z-index** simple : tri des boîtes par `(z-index, ordre)` avant peinture.

**Fichiers**
- `browser.py` — fenêtre Tkinter, charge HTML/CSS, calcule layout, appelle `render_layout` et redessine au resize.
- `html_parser.py` — DOM + récup d'erreurs (hérité de S2/S3).
- `css_parser.py` — parser + spécificité (hérité de S3), application au DOM.
- `layout.py` — moteur de layout (hérité de S4).
- `render.py` — peinture Tkinter (background, border, text) + `z-index`.
