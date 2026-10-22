#import "/commands.typ": *

// woodcore:object heading title
== Setzungen
// woodcore:/object title
// woodcore:shared settlements

// woodcore:object text p1
Setzungen sollen keine schädlichen Auswirkungen auf das Gebäude und die Umgebung (angrenzende Bauten, Leitungen, Strassen usw.) haben. Um dies zu gewährleisten, werden folgende zulässige Grenzwerte für das Setzungsverhalten festgelegt:
// woodcore:/object p1

// woodcore:object table settlements-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, right, left),
    table.hline(stroke: 1pt),
    table.header([*Setzung*], [*Grenzwert*], [*Bezug / Gültigkeit*]),
    table.hline(stroke: 0.5pt),
    [Absolute Setzung], [[…]], [[ab Fertigstellung der Decke Untergeschoss]],
    [Differentielle Setzung], [[…]], [[bezogen auf eine Länge von … m]],
    table.hline(stroke: 1pt),
  ),
  caption: [Grenzwerte der Setzungen],
)
// woodcore:/object settlements-table
// woodcore:/shared settlements
