#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Tragkonzeptpläne
// woodcore:/object title

// woodcore:object table concept-drawings-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Plan-Nr.*], [*Titel*], [*Stand (Index, Datum)*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[Statische Angaben, Untergeschoss]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Tragkonzeptpläne],
)
// woodcore:/object concept-drawings-table
