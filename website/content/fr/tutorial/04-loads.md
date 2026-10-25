# Les charges

Les charges ne se saisissent pas dans l'onglet Positions : chaque cas de charge se saisit dans l'**onglet de sa charge**, sous **Actions** dans le volet de gauche, et s'enregistre comme un fichier de `Woodcore-Datei/loads/` (`wind/`, `snow/`, `dead/`).

| Onglet | Charge | Qui calcule |
|---|---|---|
| **Neige** | la neige, SIA 261 chapitre 5 | Woodcore, à partir du bâtiment, du lieu et de la toiture saisis |
| **Poids propre et surcharge** | les charges permanentes, couche par couche | Woodcore, à partir des couches saisies |
| **Vent** | le vent, SIA 261 chapitre 6 | Woodcore, à partir des données de base et du bâtiment de l'annexe C saisis |

**Un nouveau cas est un nouveau fichier** : « Nouveau » ou « Dupliquer » dans la liste de l'onglet ajoute un deuxième toit, sans rien écrire ailleurs. Le nom du cas est celui de son fichier et celui qu'on donne au rapport.

> [!warning]
> Woodcore n'ouvre aucun classeur de charges. Un fichier dont le nom contient `Belastungsannahmen`, resté dans le dossier du projet, n'est jamais lu : chaque export le signale par un avertissement qui le nomme et rappelle que les cas se saisissent dans les onglets.

## Imprimer un cas de charge

Un cas s'imprime en entier par le fichier que Woodcore écrit pour lui, `#include domain-file("snow-load", "SL")` : la charge de neige du cas `SL`, la formule en lettres puis en chiffres, chaque valeur avec sa norme.


La section `004-einwirkungen.typ` d'un nouveau projet imprime déjà tous les cas de chaque charge avec une boucle ; nommez-les un par un pour choisir le niveau de chacun.

## Les charges utiles

Les charges utiles viennent du tableau 8 de la SIA 261, sans rien saisir : on nomme la catégorie de la surface.

```typ
#include domain-file("live-load", "A1")
```
