#import "/commands.typ": *

// woodcore:object heading title
== Documents du projet
// woodcore:/object title
// woodcore:shared project-documents

// woodcore:object text p1
Les documents suivants font foi pour le présent document, dans l'état indiqué.
// woodcore:/object p1

// woodcore:object table project-documents-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (right, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*N°*], [*Catégorie*], [*Document*], [*État (indice, date)*]),
    table.hline(stroke: 0.5pt),
    [1], [Plans d'architecte], [[Plans et maquette 3D de l'architecte]], [[…]],
    [2], [Géologie], [[Rapport géotechnique (auteur)]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Documents du projet],
)
// woodcore:/object project-documents-table
// woodcore:/shared project-documents
