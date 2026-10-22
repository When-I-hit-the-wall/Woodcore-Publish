#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Feuerwiderstand der Bauteile
// woodcore:/object title

// woodcore:object table fire-resistance-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Kategorie*], [*Bereich / Bauteil*], [*Grundlage*], [*Anforderung*], [*Ausführung / Werte*]),
    table.hline(stroke: 0.5pt),
    [Tragwerk], [[Untergeschoss – Erdgeschoss]], [VKF 15-15], [R 60], [[…]],
    [Brandabschnitte], [[Decke über Erdgeschoss]], [VKF 15-15], [REI 60], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Feuerwiderstand der Bauteile],
)
// woodcore:/object fire-resistance-table
