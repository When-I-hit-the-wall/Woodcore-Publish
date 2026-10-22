#import "/commands.typ": *

// woodcore:object heading title
== Sensibilité au bruit des locaux selon SIA 181
// woodcore:/object title

// woodcore:object table noise-sensitivity-table
#figure(
  table(
    columns: (auto, auto),
    align: (left, left),
    table.hline(stroke: 1pt),
    table.header([*Local*], [*Sensibilité au bruit*]),
    table.hline(stroke: 0.5pt),
    [[Local technique, dépôt]], [Aucune],
    [[Chambres, salle de séminaire]], [Moyenne],
    table.hline(stroke: 1pt),
  ),
  caption: [Sensibilité au bruit des locaux],
)
// woodcore:/object noise-sensitivity-table
