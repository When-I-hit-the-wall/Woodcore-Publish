#import "/commands.typ": *

// woodcore:object heading title
== Dimensions principales
// woodcore:/object title

// woodcore:object text p1
Les dimensions principales des éléments porteurs sont consignées dans les plans du concept de la structure et reposent sur le dimensionnement statique de l'ouvrage.
// woodcore:/object p1

// woodcore:object doc-table main-dimensions-table
#doc-table(
  columns: (
    (id: "position", title: [Position]),
    (id: "member", title: [Élément]),
    (id: "material", title: [Matériau / classe de résistance]),
    (id: "section", title: [Dimensions]),
    (id: "remark", title: [Remarque]),
  ),
  hidden: ("remark",),
  rows: (
    (position: [[…]], member: [[Poutre principale]], material: [[…]], section: [[…]], remark: []),
    (position: [[…]], member: [[Poteau]], material: [[…]], section: [[…]], remark: []),
  ),
  caption: [Éléments porteurs principaux],
)
// woodcore:/object main-dimensions-table
