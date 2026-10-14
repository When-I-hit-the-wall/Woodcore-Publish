# Les charges

Les charges ne se saisissent pas dans l'onglet Positions : elles viennent du **classeur des charges**, tout fichier `.xlsm` ou `.xlsx` du dossier du projet dont le nom contient `Belastungsannahmen`. Chaque cas de charge est une **feuille** de ce classeur, reconnue à son préfixe.

| Préfixe | Charge | Qui calcule |
|---|---|---|
| `SL-` | la neige, SIA 261 chapitre 5 | Excel ; Woodcore lit les valeurs et les formules |
| `EL+AL-` | les charges permanentes, couche par couche | Woodcore, à partir des couches saisies |
| `WL-` | le vent, SIA 261 chapitre 6 | Excel ; Woodcore lit les forces et enveloppe les forces locales |

**Copier une feuille ajoute un cas de charge** : `SL-Dach2` est un deuxième toit, sans rien écrire ailleurs. Le nom de la feuille devient le nom du cas dans le rapport.

> [!warning]
> Woodcore lit les valeurs qu'Excel a **calculées et enregistrées**. Enregistrez toujours le classeur dans Excel avant d'importer.

## Imprimer un cas de charge

Un cas s'imprime en entier avec `#show-calc` : la charge de neige de la feuille `SL`, la formule en lettres puis en chiffres, chaque valeur avec sa norme.

{{example show-calc-1}}

La section `004-einwirkungen.typ` d'un nouveau projet imprime déjà tous les cas de chaque charge avec une boucle ; nommez-les un par un pour choisir le niveau de chacun.

## Les charges utiles

Les charges utiles viennent du tableau 8 de la SIA 261, sans classeur : on nomme la catégorie de la surface.

```typ
#show-live-load("A1")
```
