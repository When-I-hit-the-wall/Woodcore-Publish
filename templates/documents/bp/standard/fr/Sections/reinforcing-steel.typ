#import "/commands.typ": *

// woodcore:object heading title
== Acier d'armature
// woodcore:/object title

// woodcore:object table reinforcing-steel-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Désignation*], [*Limite d'élasticité caractéristique $f_"sk"$*], [*Limite d'élasticité de calcul $f_"sd"$*], [*Module d'élasticité $E_s$*], [*Poids volumique $gamma$*]),
    table.hline(stroke: 0.5pt),
    [B500B], [500], [[…]], [[…]], [78.5],
    table.hline(stroke: 1pt),
  ),
  caption: [Acier d'armature (SIA 262)],
)
// woodcore:/object reinforcing-steel-table

// woodcore:object text reinforcing-steel-table-notes
Valeurs de calcul selon la norme SIA 262:2025.
// woodcore:/object reinforcing-steel-table-notes
