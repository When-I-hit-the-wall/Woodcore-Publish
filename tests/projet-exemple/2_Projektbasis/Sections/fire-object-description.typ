#import "/commands.typ": *

// woodcore:object heading title
== Objektbeschrieb
// woodcore:/object title

// woodcore:object doc-table fire-object-table
#doc-table(
  columns: (
    (id: "item", title: [Element]),
    (id: "text", title: [Beschreibung], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Nutzung], text: [[…]]),
    (item: [Anzahl Plätze oder Betten], text: [[…]]),
    (item: [Anzahl Geschosse und Gesamthöhe], text: [[…]]),
    (item: [Nachbargebäude], text: [[…]]),
    (item: [Verfügbarkeit von Löschwasser], text: [[…]]),
    (item: [Gewähltes Konzept (baulich / technisch)], text: [[…]]),
  ),
  caption: [Objektbeschrieb für den Brandschutz],
  header: false,
)
// woodcore:/object fire-object-table

// woodcore:object doc-choice fire-building-height
#doc-choice(
  label: [Gebäudehöhenkategorie (VKF)],
  options: (
    (id: "low", label: [Gebäude geringer Höhe (bis 11 m)]),
    (id: "medium", label: [Gebäude mittlerer Höhe (bis 30 m)]),
    (id: "high", label: [Hochhaus (über 30 m)]),
  ),
  selected: none,
)
// woodcore:/object fire-building-height
