#import "/commands.typ": *

// woodcore:object heading title
=== Erddruck und Wasserdruck
// woodcore:/object title

// woodcore:object doc-table earth-water-table
#doc-table(
  columns: (
    (id: "item", title: [Element]),
    (id: "text", title: [Beschreibung], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Erddruck], text: [[Erddruckbeiwerte, Raumlast des Bodens, Erdauflasten, Berechnungsannahmen.]]),
    (item: [Wasserdruck], text: [[Bemessungswasserstände (siehe «Baugrund»), Behandlung als ständige oder veränderliche Einwirkung.]]),
  ),
  caption: [Einwirkungen aus dem Baugrund],
  header: false,
)
// woodcore:/object earth-water-table
