#import "/commands.typ": *

// woodcore:object heading title
== Description de l'objet
// woodcore:/object title

// woodcore:object table fire-object-table
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Affectation], [[…]],
    [Nombre de places ou de lits], [[…]],
    [Nombre d'étages et hauteur totale], [[…]],
    [Bâtiments voisins], [[…]],
    [Disponibilité de l'eau d'extinction], [[…]],
    [Concept retenu (constructif / technique)], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Description de l'objet pour la protection incendie],
)
// woodcore:/object fire-object-table

// woodcore:object text fire-building-height
*Catégorie de hauteur du bâtiment (AEAI)* :
- Bâtiment de faible hauteur (jusqu'à 11 m)
- Bâtiment de hauteur moyenne (jusqu'à 30 m)
- Bâtiment élevé (plus de 30 m)
// woodcore:/object fire-building-height
