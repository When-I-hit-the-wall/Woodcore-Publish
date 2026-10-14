#import "/commands.typ": *

// woodcore:object heading title
== Lärmempfindlichkeit der Räume nach SIA 181
// woodcore:/object title

// woodcore:object doc-table noise-sensitivity-table
#doc-table(
  columns: (
    (id: "room", title: [Raum]),
    (id: "sensitivity", title: [Lärmempfindlichkeit]),
  ),
  hidden: (),
  rows: (
    (room: [[Technikraum, Lager]], sensitivity: [Keine]),
    (room: [[Zimmer, Seminarraum]], sensitivity: [Mittel]),
  ),
  caption: [Lärmempfindlichkeit der Räume],
)
// woodcore:/object noise-sensitivity-table
