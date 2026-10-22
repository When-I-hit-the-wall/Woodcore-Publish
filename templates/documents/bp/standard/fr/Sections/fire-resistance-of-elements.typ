#import "/commands.typ": *

// woodcore:object heading title
== Résistance au feu des éléments de construction
// woodcore:/object title

// woodcore:object table fire-resistance-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Catégorie*], [*Zone / élément*], [*Base*], [*Exigence*], [*Exécution / valeurs*]),
    table.hline(stroke: 0.5pt),
    [Structure porteuse], [[Sous-sol – rez]], [AEAI 15-15], [R 60], [[…]],
    [Compartiments coupe-feu], [[Dalle sur rez]], [AEAI 15-15], [REI 60], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Résistance au feu des éléments de construction],
)
// woodcore:/object fire-resistance-table
