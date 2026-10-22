#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Holzfeuchte und Kriechen
// woodcore:/object title

// woodcore:object text moisture-class
*Feuchteklasse (SIA 265, Tab. 3)*: Feuchteklasse 1: mittlere Holzfeuchte ≤ 12 %, vor der Witterung geschützt
// woodcore:/object moisture-class

// woodcore:object table moisture-factors
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Reduktion der Festigkeit $η_w$], [[gemäss gewählter Feuchteklasse (SIA 265, Tab. 4)]],
    [Reduktion der Steifigkeit $η_w$], [[gemäss gewählter Feuchteklasse (SIA 265, Tab. 4)]],
    [Kriechzahl φ, auf Gebrauchsfeuchte vorkonditioniertes Holz], [[…]],
    [Kriechzahl φ, angetrocknet oder feucht eingebautes Holz], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Feuchte- und Kriechbeiwerte],
)
// woodcore:/object moisture-factors
