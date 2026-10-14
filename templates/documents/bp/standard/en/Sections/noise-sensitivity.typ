#import "/commands.typ": *

// woodcore:object heading title
== Noise sensitivity of rooms in accordance with SIA 181
// woodcore:/object title

// woodcore:object doc-table noise-sensitivity-table
#doc-table(
  columns: (
    (id: "room", title: [Room]),
    (id: "sensitivity", title: [Noise sensitivity]),
  ),
  hidden: (),
  rows: (
    (room: [[Plant room, storage]], sensitivity: [None]),
    (room: [[Bedrooms, seminar room]], sensitivity: [Medium]),
  ),
  caption: [Noise sensitivity of rooms],
)
// woodcore:/object noise-sensitivity-table
