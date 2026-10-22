#import "/commands.typ": *

// woodcore:object heading title
== Risikobewertung und Schutzziele
// woodcore:/object title

// woodcore:object text p1
Die Einwirkungen auf die Tragwerke werden nach der Norm SIA 261 berücksichtigt. Die Schutzziele und der Schutzgrad werden aufgrund einer Risikobewertung festgelegt (SIA 260, Ziffer 2.2.3). Die Schutzziele und die besonderen Risiken werden wie folgt behandelt:
// woodcore:/object p1

// woodcore:object table hazards-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Gefährdung*], [*Behandlung*], [*Bemerkung*]),
    table.hline(stroke: 0.5pt),
    [Temperatur], [Im Nachweis berücksichtigt], [Die klimatischen Temperaturschwankungen werden bei der Bemessung der äusseren Aussteifungs- und Stabilisierungselemente berücksichtigt.],
    [Anprall], [Im Nachweis berücksichtigt], [Aussergewöhnliche Einwirkung nach der Norm SIA 261. [Fahrzeuge, Gabelstapler …]],
    [Brand], [Im Nachweis berücksichtigt], [Aussergewöhnliche Einwirkung nach der Norm SIA 261; die Anforderungen werden nach den schweizerischen Brandschutzvorschriften berücksichtigt.],
    [Erdbeben], [Im Nachweis berücksichtigt], [Aussergewöhnliche Einwirkung nach der Norm SIA 261.],
    [Explosion], [Akzeptiertes Risiko], [[Akzeptiertes Risiko / aussergewöhnliche Einwirkung.]],
    [Überschwemmung], [Akzeptiertes Risiko], [[Akzeptiertes Risiko / aussergewöhnliche Einwirkung.]],
    [Steinschlag], [Nicht relevant], [[…]],
    [Lawinen], [Nicht relevant], [[…]],
    [Vandalismus], [Akzeptiertes Risiko], [[…]],
    [Blitzschlag], [Sache Dritter], [Das Blitzschutzkonzept liegt nicht im Aufgabenbereich der Ingenieurin bzw. des Ingenieurs.],
    table.hline(stroke: 1pt),
  ),
  caption: [Gefährdungen und besondere Risiken],
)
// woodcore:/object hazards-table

// woodcore:object text hazards-table-notes
Als «akzeptiert» eingestufte Risiken werden im Abschnitt «Akzeptierte Risiken» aufgeführt.
// woodcore:/object hazards-table-notes
