---
id: 2026-10-11-argument-sep-var
titre: Argument `sep:` de #var, #eq et #var-unit — le séparateur sans var-line
status: active
cree: 2026-10-11
mis_a_jour: 2026-10-11
source: conversation du 11.10.2026 (projet Aufgabe2, fichiers Formules/*.typ)
docs: [docs/typst/formulas.md, docs/ui/tab-formulas.md]
---

# Argument `sep:` de #var, #eq et #var-unit — Spécification

## 1. Objectif

L'ingénieur écrivait `#var("b", 208, "mm") ;` pour séparer deux variables imprimées sur une même ligne. Depuis la v0.117, un `;` après l'appel fait de la ligne un texte, refusé par l'onglet «Formules» (`text_trailing`). Le seul moyen restant d'obtenir le séparateur était `#var-line[…]`, un conteneur que l'onglet ne sait pas écrire. Il veut que le séparateur soit **un argument de la commande elle-même**, comme le choix « en ligne / sur sa propre ligne » l'est déjà (`note:`).

## 2. Source

> « est-il possible de ne plus utiliser var-line? l'option d'afficher var en ligne ou sur sa ligne seule serait un argument de var » — puis, à la proposition `sep: ";"` : « yes add the sep argument ».

## 3. Décisions

- **D-01** — `sep:` est un argument nommé de `#var`, `#eq` et `#var-unit` (les trois commandes qui s'impriment en ligne et prennent `note:`). `#verify` et `#val` ne le prennent pas : ce sont des mots de leur phrase.
- **D-02** — `sep: none` par défaut (rien ne change pour un appel existant). Une chaîne (`";"`, `","`) est imprimée **juste après** la valeur et sa note, suivie d'un espace : `#var("b", 208, "mm", sep: ";")` remplace mot pour mot l'ancien `#var("b", 208, "mm") ;`.
- **D-03** — Le séparateur suit le niveau de la variable : à `level: 0` (ou un niveau qui la masque) il n'est pas imprimé — la raison d'être de var-line, conservée.
- **D-04** — Refusé (panic qui le dit) avec `note: "line"` (une ligne à part n'a pas de voisin à séparer) et à l'intérieur d'un `var-line`, qui écrit ses propres séparateurs (`var-line(sep:)`). Une valeur qui n'est ni `none` ni une chaîne est refusée.
- **D-05** — `var-line` **reste** : des rapports existants l'utilisent ; il n'est ni retiré ni déprécié dans ce lot.
- **D-06** — Woodcore : l'option «Séparateur» (`sep`, texte) dans le volet «Affichage» de `var`, `eq` et `var-unit` ; le refus `text_trailing` propose `sep: "…"` quand ce qui suit l'appel est un signe de ponctuation seul.

## 4. Critères d'acceptation

1. `#var("b", 208, "mm", sep: ";") #var("t", 8.5, "mm")` imprime `b = 208 mm; t = 8.5 mm` sur une ligne.
2. Un appel sans `sep:` imprime exactement comme avant (exemples gelés inchangés hors des nouveaux).
3. `sep:` avec `note: "line"`, dans un `var-line`, ou d'un autre type que chaîne : la compilation s'arrête sur un message qui le nomme.
4. Une variable à `level: 0` avec `sep:` n'imprime ni la valeur ni le séparateur.
5. L'onglet «Formules» relit un fichier contenant `sep:` sans le marquer illisible, et le réécrit à l'identique.
6. Le message `text_trailing` pour `#var(...) ;` propose `sep: ";"`.
7. `///`, `calc/i18n/commands.json` (fr/de), deux exemples compilés, `docs/typst/formulas.md`, CHANGELOG.
