#import "/commands.typ": *

// woodcore:object heading title
== Schallschutz
// woodcore:/object title

// woodcore:object doc-table noise-objectives-table
#doc-table(
  columns: (
    (id: "item", title: [Element]),
    (id: "text", title: [Beschreibung], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Anforderungen], text: [Die Anforderungen der Norm SIA 181 sind einzuhalten. [Allfällige erhöhte Anforderungen, z. B. Decke zwischen Zimmern und Restaurant.]]),
    (item: [Lärmempfindlichkeit], text: [Empfindlichkeitsstufe gemäss Lärmschutz-Verordnung (LSV): [ES II, Zone …]. [Besondere zu berücksichtigende Lärmquellen.]]),
  ),
  caption: [Schallschutzziele],
  header: false,
)
// woodcore:/object noise-objectives-table
