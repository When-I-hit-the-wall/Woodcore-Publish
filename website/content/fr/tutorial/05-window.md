# Importer et explorer dans la fenêtre de Woodcore

Un projet s'ouvre dans la **fenêtre de Woodcore**. Elle importe les classeurs, montre ce qu'ils contiennent, et c'est là qu'on dessine ce qu'un classeur ne sait pas décrire.

## Importer Excel

Le bouton **Importer Excel** lit les classeurs de charges, calcule ce qui doit l'être, vérifie chaque fichier et écrit l'export dans `Statischer Bericht (typst)/_woodcore/data/`. Rien n'est écrit si quelque chose ne va pas : le message nomme alors la feuille et la cellule à corriger, et les données précédentes restent affichées.

> [!note]
> Un bandeau signale un classeur enregistré après le dernier import : il suffit d'importer à nouveau.

## Les onglets

| Onglet | Ce qu'on y fait |
|---|---|
| **Charges** | Parcourir chaque charge, cas et valeur, avec sa provenance jusqu'à la cellule Excel. Un double-clic copie l'appel Typst qui l'imprime. |
| **Plan de position** | Importer un document de l'architecte (PDF, image, SVG, DXF, DWG), le parcourir page par page, cocher les pages qui deviennent des plans, puis y poser les symboles STE des positions, avec les axes et l'échelle. Les feuilles de plans et la commande `#show-plan` s'y préparent aussi. |
| **Positions** | La source des positions : ajouter, modifier ou supprimer une position (`Woodcore-Datei/positions.json`) ; l'export suit aussitôt. **Importer depuis Excel…** reprend un ancien `Positionen.xlsx`. |
| **Modèles statiques** | Dessiner un système statique : barres, appuis, articulations, charges et cotes. |
| **Schémas** | Dessiner un détail d'assemblage à l'échelle réelle : les pièces, les moyens d'assemblage, les aides de construction, les cotes. |
| **Moyens d'assemblage** | Calculer la résistance d'un assemblage à broches selon la SIA 265, sur un schéma. |
| **Moments polaires** | Répartir N, V et M sur les moyens d'assemblage d'un schéma. |
| **Commandes** | La documentation de toutes les commandes du rapport, avec leurs exemples — celle de ce site. |

Ce qu'on dessine est enregistré dans `Woodcore-Datei/` et exporté aussitôt : le rapport le voit sans nouvel import.

## Copier un appel

Presque chaque ligne de la fenêtre propose l'appel qui l'imprime dans le rapport. Un double-clic le copie, un clic droit les liste tous. Par exemple, pour une position dessinée sur un plan :

```typ
#show-plan("Velo-Unterstand", highlight: "T001", detail: true)
```
