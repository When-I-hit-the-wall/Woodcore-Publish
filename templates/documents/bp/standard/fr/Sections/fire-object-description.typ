#import "/commands.typ": *

// woodcore:object heading title
== Description de l'objet
// woodcore:/object title

// woodcore:object doc-table fire-object-table
#doc-table(
  columns: (
    (id: "item", title: [Élément]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Affectation], text: [[…]]),
    (item: [Nombre de places ou de lits], text: [[…]]),
    (item: [Nombre d'étages et hauteur totale], text: [[…]]),
    (item: [Bâtiments voisins], text: [[…]]),
    (item: [Disponibilité de l'eau d'extinction], text: [[…]]),
    (item: [Concept retenu (constructif / technique)], text: [[…]]),
  ),
  caption: [Description de l'objet pour la protection incendie],
  header: false,
)
// woodcore:/object fire-object-table

// woodcore:object doc-choice fire-building-height
#doc-choice(
  label: [Catégorie de hauteur du bâtiment (AEAI)],
  options: (
    (id: "low", label: [Bâtiment de faible hauteur (jusqu'à 11 m)]),
    (id: "medium", label: [Bâtiment de hauteur moyenne (jusqu'à 30 m)]),
    (id: "high", label: [Bâtiment élevé (plus de 30 m)]),
  ),
  selected: none,
)
// woodcore:/object fire-building-height
