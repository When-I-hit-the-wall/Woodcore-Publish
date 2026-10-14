#import "/commands.typ": *

// woodcore:object heading title
== Setzungen
// woodcore:/object title
// woodcore:shared settlements

// woodcore:object text p1
Setzungen sollen keine schädlichen Auswirkungen auf das Gebäude und die Umgebung (angrenzende Bauten, Leitungen, Strassen usw.) haben. Um dies zu gewährleisten, werden folgende zulässige Grenzwerte für das Setzungsverhalten festgelegt:
// woodcore:/object p1

// woodcore:object doc-table settlements-table
#doc-table(
  columns: (
    (id: "kind", title: [Setzung]),
    (id: "limit", title: [Grenzwert], unit: "mm", kind: "number"),
    (id: "basis", title: [Bezug / Gültigkeit]),
  ),
  hidden: (),
  rows: (
    (kind: [Absolute Setzung], limit: [[…]], basis: [[ab Fertigstellung der Decke Untergeschoss]]),
    (kind: [Differentielle Setzung], limit: [[…]], basis: [[bezogen auf eine Länge von … m]]),
  ),
  caption: [Grenzwerte der Setzungen],
)
// woodcore:/object settlements-table
// woodcore:/shared settlements
