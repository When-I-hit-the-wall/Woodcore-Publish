#import "/commands.typ": *

// woodcore:object heading title
== Bemessungssituationen
// woodcore:/object title

// woodcore:object text p1
Die betrachteten Bemessungssituationen schliessen alle vorhersehbaren Bedingungen ein, die während der Ausführung und Nutzung auftreten können (SIA 260, Ziffer 4.2.1). Sie werden in andauernde, vorübergehende und aussergewöhnliche Situationen eingeteilt; Bauzustände können als andauernde oder vorübergehende Bemessungssituationen betrachtet werden (Ziffern 4.2.2 und 4.2.3).
// woodcore:/object p1

// woodcore:object table design-situations-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Situation*], [*Beschreibung*], [*Massgebende Lastfälle*]),
    table.hline(stroke: 0.5pt),
    [Andauernd], [[Normale Nutzung]], [[…]],
    [Vorübergehend], [[Bauzustände]], [[…]],
    [Aussergewöhnlich], [[Erdbeben, Brand, Anprall]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Bemessungssituationen],
)
// woodcore:/object design-situations-table
