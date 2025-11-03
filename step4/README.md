# Step 4 — Layout Engine (Cours S4)

**Objectif livrable :** un **moteur de layout** calculant positions & tailles :
- **Box model** (margin, border, padding, content).
- **Flux normal** (blocs empilés verticalement).
- **Inline** simplifié (mesure texte naïve, retour à la ligne basique).
- **Positionnement** : `static` (défaut), `relative` (offset après layout), `absolute` (par rapport au bloc positionné ancêtre).
- Export texte via `layout_to_string()`.

**Fichiers**
- `browser.py` — charge HTML/CSS, applique les styles, génère l’arbre de layout et l’exporte en texte.
- `html_parser.py` — DOM + récupération d’erreurs (repris de S2/S3).
- `css_parser.py` — parse CSS + spécificité (repris de S3), application au DOM.
- `layout.py` — moteur de layout (ci-dessus).

> Remarque : le rendu (dessin) arrivera à l’étape **S5**.
