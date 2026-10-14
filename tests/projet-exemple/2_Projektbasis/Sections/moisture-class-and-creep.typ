#import "/commands.typ": *

// woodcore:object heading title
== Holzfeuchte und Kriechen
// woodcore:/object title

// woodcore:object doc-choice moisture-class
#doc-choice(
  label: [Feuchteklasse (SIA 265, Tab. 3)],
  options: (
    (id: "1", label: [Feuchteklasse 1: mittlere Holzfeuchte ≤ 12 %, vor der Witterung geschützt]),
    (id: "2", label: [Feuchteklasse 2: > 12 bis 20 %, teilweise vor der Witterung geschützt oder direkt bewittert]),
    (id: "3", label: [Feuchteklasse 3: > 20 %, feucht oder unter Wasser]),
  ),
  selected: "1",
)
// woodcore:/object moisture-class

// woodcore:object doc-table moisture-factors
#doc-table(
  columns: (
    (id: "item", title: [Element]),
    (id: "text", title: [Beschreibung], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Reduktion der Festigkeit $η_w$], text: [[gemäss gewählter Feuchteklasse (SIA 265, Tab. 4)]]),
    (item: [Reduktion der Steifigkeit $η_w$], text: [[gemäss gewählter Feuchteklasse (SIA 265, Tab. 4)]]),
    (item: [Kriechzahl φ, auf Gebrauchsfeuchte vorkonditioniertes Holz], text: [[…]]),
    (item: [Kriechzahl φ, angetrocknet oder feucht eingebautes Holz], text: [[…]]),
  ),
  caption: [Feuchte- und Kriechbeiwerte],
  header: false,
)
// woodcore:/object moisture-factors
