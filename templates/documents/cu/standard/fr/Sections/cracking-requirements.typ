#import "/commands.typ": *

// woodcore:object heading title
== Exigences relatives à la fissuration
// woodcore:/object title

// woodcore:object text p1
La norme SIA 262 distingue trois niveaux d'exigences relatives à la fissuration : normales lorsque les fissures sont tolérées et qu'aucune exigence particulière d'étanchéité ou d'aspect n'est posée ; accrues lorsqu'il existe des exigences particulières de fonctionnalité et d'aspect et qu'une bonne répartition des fissures est recherchée ; élevées lorsqu'une limitation des ouvertures de fissures est souhaitée. Ces exigences valent pour les sollicitations de contrainte imposée (retrait, p. ex.) comme pour celles de flexion ; des exigences accrues ou élevées réduisent les contraintes admissibles de l'acier et augmentent la quantité d'armature.
// woodcore:/object p1

// woodcore:object doc-table cracking-requirements-table
#doc-table(
  columns: (
    (id: "area", title: [Zone]),
    (id: "level", title: [Exigence]),
    (id: "wm", title: [Ouverture moyenne $w_m$], unit: "mm", kind: "number"),
    (id: "wmax", title: [Ouverture maximale $w_"max"$], unit: "mm", kind: "number"),
  ),
  hidden: ("wm", "wmax"),
  rows: (
    (area: [[Général]], level: [Normale], wm: 0.7, wmax: 1.2),
    (area: [[Béton apparent]], level: [Accrues], wm: 0.5, wmax: 0.9),
  ),
  caption: [Exigences par zone],
  notes: (
    [Ouvertures de fissures attendues pour les trois niveaux : $w_m$ = 0.7 / 0.5 / 0.25 mm et $w_"max"$ = 1.2 / 0.9 / 0.4 mm ($w_"max"$ = 1.7 · $w_m$, valeur à 95 %), d'après le modèle du tirant (documentation SIA D 0182).],
  ),
)
// woodcore:/object cracking-requirements-table
