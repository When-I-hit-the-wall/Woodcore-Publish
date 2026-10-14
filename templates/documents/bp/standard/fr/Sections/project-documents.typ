#import "/commands.typ": *

// woodcore:object heading title
== Documents du projet
// woodcore:/object title
// woodcore:shared project-documents

// woodcore:object text p1
Les documents suivants font foi pour le présent document, dans l'état indiqué.
// woodcore:/object p1

// woodcore:object doc-table project-documents-table
#doc-table(
  columns: (
    (id: "no", title: [N°], kind: "number"),
    (id: "category", title: [Catégorie]),
    (id: "document", title: [Document]),
    (id: "status", title: [État (indice, date)]),
  ),
  hidden: (),
  rows: (
    (no: 1, category: [Plans d'architecte], document: [[Plans et maquette 3D de l'architecte]], status: [[…]]),
    (no: 2, category: [Géologie], document: [[Rapport géotechnique (auteur)]], status: [[…]]),
  ),
  caption: [Documents du projet],
)
// woodcore:/object project-documents-table
// woodcore:/shared project-documents
