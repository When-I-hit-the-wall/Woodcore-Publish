#import "/commands.typ": *

// woodcore:object heading title
== Dimensions principales
// woodcore:/object title

// woodcore:object text p1
Les dimensions principales des éléments porteurs sont consignées dans les plans du concept de la structure et reposent sur le dimensionnement statique de l'ouvrage.
// woodcore:/object p1

// woodcore:object table main-dimensions-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Position*], [*Élément*], [*Matériau / classe de résistance*], [*Dimensions*]),  // woodcore:hidden 5=[Remarque]
    table.hline(stroke: 0.5pt),
    [[…]], [[Poutre principale]], [[…]], [[…]],  // woodcore:hidden 5=[]
    [[…]], [[Poteau]], [[…]], [[…]],  // woodcore:hidden 5=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Éléments porteurs principaux],
)
// woodcore:/object main-dimensions-table
