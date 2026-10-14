# Calculer dans le rapport

Tout ne vient pas de l'export : une valeur tirée d'une fiche de fabricant, une vérification écrite à la main. Woodcore calcule ces lignes dans le rapport lui-même, avec leurs unités, et les imprime comme le reste.

## Des variables et des formules

`#var` écrit une variable et l'imprime ; `#eq` évalue une formule qui **nomme** les variables, l'imprime en lettres puis en chiffres, et convertit les unités :

{{example eq-2}}

Une variable garde son nom pour toute la suite du document : la ligne suivante peut la nommer à son tour. Plusieurs déclarations tiennent sur une ligne avec `#var-line`, et `level: 0` déclare une valeur sans l'imprimer.

## Une vérification

`#verify` compare les deux côtés d'une relation, imprime le signe qui est vrai, et marque la réponse ✔ ou ✘ :

{{example verify-1}}

## Vérifier un élément en bois

Les vérifications de la SIA 265, chapitre 4.2, se font en deux temps : `#member` décrit l'élément une fois — section, classe de résistance et classe d'humidité, lues de sa position —, puis une commande `verify-…` le vérifie pour chaque action.

{{example verify-compression-1}}

`verify-tension`, `verify-compression`, `verify-bending`, `verify-bending-normal`, `verify-shear` et les autres suivent la même forme ; l'effort normal est signé, la traction positive.

> [!note]
> Ce qui est calculé dans le rapport n'est pas tracé dans l'export : le texte autour doit dire d'où viennent les valeurs saisies à la main.
