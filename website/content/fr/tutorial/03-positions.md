# Décrire les positions

Une **position** est un élément de la structure — une poutre, un poteau, un panneau — tel que le plan de position le numérote. Les positions se saisissent dans l'onglet **Positions** de Woodcore, une ligne par élément ; elles sont enregistrées dans `Woodcore-Datei/positions.json`.

> [!note]
> Un projet plus ancien qui contient un `Positionen.xlsx` : à sa première ouverture, Woodcore importe le classeur une fois, puis le déplace dans `_Archiv/` — il n'est jamais supprimé et n'est plus lu ensuite. Le bouton **Importer depuis Excel…** de l'onglet Positions reste disponible pour reprendre un classeur plus tard.

## Les champs

Seuls le numéro et le type sont obligatoires ; tout le reste est facultatif.

| Champ | Contenu | Exemple |
|---|---|---|
| numéro (`position`) | le numéro, obligatoire | `T001` |
| type (`type`) | le type d'élément, obligatoire | `Träger` |
| matériau (`material`) | le matériau | `Fichte` |
| classe de résistance (`resistance class`) | la classe de résistance | `C24` |
| type de section (`section type`) | le type de section : `rec`, `cir`, `pla`, `clt`, ou un profilé d'acier de la SZS C5 (`IPE`, `HEA`, `ROR` …) | `rec` |
| dimension (`dimension`) | la taille de la section, lue selon son type | `100/200` |
| unité (`units`) | l'unité de la section : mm, cm ou m | `mm` |
| classe d'humidité (`moisture class`) | la classe d'humidité : 1, 2 ou 3 | `2` |
| description (`description`) | un texte libre | `Chevron, axe 3` |

Le numéro commence par la lettre du type — `T` pour une poutre, `S` pour un poteau, `D` pour une dalle — suivie du caractère de numérotation de l'étage et d'un numéro : `T001` est la poutre 01 du rez-de-chaussée. L'onglet propose le prochain numéro libre.

> [!tip]
> La dimension se lit selon le type de section : `rec` sa largeur et sa hauteur, `100/200` ; `cir` son diamètre, `200` ; `pla` l'épaisseur d'une plaque, `22` ; `clt` ses couches, `20/30/20/30/20` ; un profilé d'acier la taille de sa désignation, `200` pour IPE 200 ou `101.6x10` pour ROR 101.6×10, en mm. Un type vide laisse la dimension en texte descriptif, comme `180` pour un panneau. **Une section que Woodcore ne sait pas lire n'arrête pas l'export** : elle devient un avertissement.

## Dans le rapport

Chaque position apparaît dans la liste des matériaux du rapport sans rien écrire : la section `003-baustoffe.typ` parcourt toutes les positions avec `#member`, qui imprime la ligne d'une position au niveau 1 — et, pour le bois à section rectangulaire ou ronde, inscrit au passage ce que lisent les vérifications de la SIA 265 (étape 7). Si une position n'a pas de section ou de classe, `#member` dit ce qu'il ne peut pas calculer, et l'on donne alors les valeurs dans l'appel : `grade:`, `moisture-class:`, `b:`, `h:`.

{{example member-3}}

Une position ajoutée ou modifiée dans l'onglet arrive dans le rapport aussitôt : l'export suit l'enregistrement.
