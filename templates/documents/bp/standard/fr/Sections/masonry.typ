#import "/commands.typ": *

// woodcore:object heading title
== Maçonnerie
// woodcore:/object title

// woodcore:object table masonry-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, right, right),
    table.hline(stroke: 1pt),
    table.header([*Désignation*], [*Résistance à la compression de calcul $f_"xd"$*], [*Module d'élasticité de calcul $E_"xd"$*]),  // woodcore:hidden 4=[Autres valeurs caractéristiques]
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]],  // woodcore:hidden 4=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Maçonnerie (SIA 266)],
)
// woodcore:/object masonry-table
