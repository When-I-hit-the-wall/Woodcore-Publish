#import "/commands.typ": *

// woodcore:object heading title
== Utilisation prévue
// woodcore:/object title

// woodcore:object doc-table intended-use-table
#doc-table(
  columns: (
    (id: "item", title: [Élément]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Utilisation], text: [[Affectations prévues (logement, bureau, enseignement, commerce, restaurant, salle polyvalente …).]]),
    (item: [Charges utiles], text: [Les charges utiles sont fixées par catégorie d'utilisation selon la norme SIA 261 (voir la section « Charges utiles »).]),
    (item: [Gabarits d'espace libre], text: [[Selon les plans d'avant-projet et la maquette 3D de l'architecte.]]),
  ),
  caption: [Utilisation prévue],
  header: false,
)
// woodcore:/object intended-use-table
