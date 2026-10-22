#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
=== Erddruck und Wasserdruck
// woodcore:/object title

// woodcore:object table earth-water-table
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Erddruck], [[Erddruckbeiwerte, Raumlast des Bodens, Erdauflasten, Berechnungsannahmen.]],
    [Wasserdruck], [[Bemessungswasserstände (siehe «Baugrund»), Behandlung als ständige oder veränderliche Einwirkung.]],
    table.hline(stroke: 1pt),
  ),
  caption: [Einwirkungen aus dem Baugrund],
)
// woodcore:/object earth-water-table
