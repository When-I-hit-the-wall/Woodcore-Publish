#import "/commands.typ": *

// woodcore:object heading title
== Sensibilité au bruit des locaux selon SIA 181
// woodcore:/object title

// woodcore:object doc-table noise-sensitivity-table
#doc-table(
  columns: (
    (id: "room", title: [Local]),
    (id: "sensitivity", title: [Sensibilité au bruit]),
  ),
  hidden: (),
  rows: (
    (room: [[Local technique, dépôt]], sensitivity: [Aucune]),
    (room: [[Chambres, salle de séminaire]], sensitivity: [Moyenne]),
  ),
  caption: [Sensibilité au bruit des locaux],
)
// woodcore:/object noise-sensitivity-table
