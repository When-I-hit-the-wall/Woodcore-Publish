#import "/commands.typ": *

// woodcore:object heading title
== Acier de construction et assemblages
// woodcore:/object title

// woodcore:object table structural-steel-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, right, right),
    table.hline(stroke: 1pt),
    table.header([*Nuance*], [*Épaisseur*], [*Limite d'élasticité $f_y$*], [*Résistance à la traction $f_u$*]),  // woodcore:hidden 5=[Module d'élasticité $E_a$] 6=[Poids volumique $gamma$]
    table.hline(stroke: 0.5pt),
    [S235], [t ≤ 40 mm], [235], [360],  // woodcore:hidden 5=[210000] 6=[78.5]
    [S355], [t ≤ 40 mm], [355], [510],  // woodcore:hidden 5=[210000] 6=[78.5]
    table.hline(stroke: 1pt),
  ),
  caption: [Acier de construction (SIA 263)],
)
// woodcore:/object structural-steel-table

// woodcore:object table bolts-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, right, right, left),
    table.hline(stroke: 1pt),
    table.header([*Classe de résistance*], [*Limite d'élasticité $f_"yb"$*], [*Résistance à la traction $f_"ub"$*], [*Emploi*]),
    table.hline(stroke: 0.5pt),
    [4.6], [240], [400], [Boulons, tire-fonds],
    [8.8], [640], [800], [Vis à bois (classe minimale)],
    table.hline(stroke: 1pt),
  ),
  caption: [Boulons, tire-fonds et vis à bois (SIA 263)],
)
// woodcore:/object bolts-table

// woodcore:object text bolts-table-notes
Les broches (goujons) en acier S355 se calculent avec $f_(u,k)$ = 510 N/mm² (SN EN 14592).
// woodcore:/object bolts-table-notes
