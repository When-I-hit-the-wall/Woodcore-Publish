#import "/commands.typ": *

// woodcore:object heading title
== Résistance au feu des éléments de construction
// woodcore:/object title

// woodcore:object doc-table fire-resistance-table
#doc-table(
  columns: (
    (id: "category", title: [Catégorie]),
    (id: "zone", title: [Zone / élément]),
    (id: "basis", title: [Base]),
    (id: "requirement", title: [Exigence]),
    (id: "execution", title: [Exécution / valeurs]),
  ),
  hidden: (),
  rows: (
    (category: [Structure porteuse], zone: [[Sous-sol – rez]], basis: [AEAI 15-15], requirement: [R 60], execution: [[…]]),
    (category: [Compartiments coupe-feu], zone: [[Dalle sur rez]], basis: [AEAI 15-15], requirement: [REI 60], execution: [[…]]),
  ),
  caption: [Résistance au feu des éléments de construction],
)
// woodcore:/object fire-resistance-table
