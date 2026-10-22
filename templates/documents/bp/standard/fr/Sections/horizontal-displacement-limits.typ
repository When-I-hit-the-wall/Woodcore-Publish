#import "/commands.typ": *

// woodcore:object heading title
== Déplacements horizontaux
// woodcore:/object title

// woodcore:object text p1
Les déplacements horizontaux dus aux actions variables sont limités aux valeurs indicatives de la norme SIA 260, annexe A, tableau 4 ; h désigne la hauteur d'étage et H la hauteur du bâtiment. Pour la situation de projet séisme, les déplacements horizontaux par étage sont limités à 1/500, respectivement 1/200 de la hauteur d'étage en présence d'éléments incorporés fragiles, respectivement ductiles (ch. 4.4.4.5).
// woodcore:/object p1

// woodcore:object table horizontal-limits-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, center, left),
    table.hline(stroke: 1pt),
    table.header([*Critère*], [*Valeur limite*], [*Cas de charge (SIA 260, tab. 4)*]),
    table.hline(stroke: 0.5pt),
    [Éléments incorporés à caractère fragile], [$u <= h \/ 500$], [rare (20)],
    [Éléments incorporés à caractère ductile], [$u <= h \/ 200$], [fréquent (21)],
    [Utilisation et exploitation], [$u <= H \/ 300$], [fréquent (21)],
    [Aspect], [$u <= h \/ 250$], [quasi permanent (22)],
    table.hline(stroke: 1pt),
  ),
  caption: [Déplacements horizontaux limites],
)
// woodcore:/object horizontal-limits-table
