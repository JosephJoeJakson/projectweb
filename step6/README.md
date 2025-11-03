# Step 6 — JavaScript simple (Cours S6)

**Objectif livrable :** un bouton interactif qui modifie le contenu d'une `<div>` au clic.

## Ce qui est implémenté
- `document.getElementById(id).innerHTML = "..."` (écriture).
- `element.onclick = function(){ ... }` **ou** `element.addEventListener("click", function(){ ... })`.
- Détection de clics via le **Canvas** (zones cliquables générées pour `<button>` et éléments avec `class="btn"`).
- Re-render automatique après mutation du DOM.

> Remarque : c'est un **subset** pédagogique — pas de vrai tokenizer/parser ou variables générales (prévu en approfondissement).

## Fichiers
- `browser.py` — fenêtre Tkinter, charge HTML/CSS, exécute `<script>` inline, gère les clics et appelle l'interpréteur JS.
- `html_parser.py` — DOM + récup d'erreurs (hérité S2/S3).
- `css_parser.py` — parser + spécificité (hérité S3).
- `layout.py` — moteur de layout (hérité S4/S5).
- `render.py` — peinture + **hit testing** pour les éléments cliquables.
- `js_interpreter.py` — interpréteur JS minimal (innerHTML + onclick/addEventListener).

## Exemple d'usage (HTML simple)
```html
<div id="msg">Bonjour</div>
<button id="btn">Changer</button>
<script>
  document.getElementById("btn").onclick = function(){
    document.getElementById("msg").innerHTML = "Clic !";
  };
</script>
```
