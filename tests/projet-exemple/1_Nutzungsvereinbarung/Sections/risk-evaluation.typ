#import "/commands.typ": *

// woodcore:object heading title
== Risikobewertung und Schutzziele
// woodcore:/object title

// woodcore:object text p1
Die Einwirkungen auf die Tragwerke werden nach der Norm SIA 261 berücksichtigt. Die Schutzziele und der Schutzgrad werden aufgrund einer Risikobewertung festgelegt (SIA 260, Ziffer 2.2.3). Die Schutzziele und die besonderen Risiken werden wie folgt behandelt:
// woodcore:/object p1

// woodcore:object doc-table hazards-table
#doc-table(
  columns: (
    (id: "hazard", title: [Gefährdung]),
    (id: "handling", title: [Behandlung]),
    (id: "remark", title: [Bemerkung]),
  ),
  hidden: (),
  rows: (
    (hazard: [Temperatur], handling: [Im Nachweis berücksichtigt], remark: [Die klimatischen Temperaturschwankungen werden bei der Bemessung der äusseren Aussteifungs- und Stabilisierungselemente berücksichtigt.]),
    (hazard: [Anprall], handling: [Im Nachweis berücksichtigt], remark: [Aussergewöhnliche Einwirkung nach der Norm SIA 261. [Fahrzeuge, Gabelstapler …]]),
    (hazard: [Brand], handling: [Im Nachweis berücksichtigt], remark: [Aussergewöhnliche Einwirkung nach der Norm SIA 261; die Anforderungen werden nach den schweizerischen Brandschutzvorschriften berücksichtigt.]),
    (hazard: [Erdbeben], handling: [Im Nachweis berücksichtigt], remark: [Aussergewöhnliche Einwirkung nach der Norm SIA 261.]),
    (hazard: [Explosion], handling: [Akzeptiertes Risiko], remark: [[Akzeptiertes Risiko / aussergewöhnliche Einwirkung.]]),
    (hazard: [Überschwemmung], handling: [Akzeptiertes Risiko], remark: [[Akzeptiertes Risiko / aussergewöhnliche Einwirkung.]]),
    (hazard: [Steinschlag], handling: [Nicht relevant], remark: [[…]]),
    (hazard: [Lawinen], handling: [Nicht relevant], remark: [[…]]),
    (hazard: [Vandalismus], handling: [Akzeptiertes Risiko], remark: [[…]]),
    (hazard: [Blitzschlag], handling: [Sache Dritter], remark: [Das Blitzschutzkonzept liegt nicht im Aufgabenbereich der Ingenieurin bzw. des Ingenieurs.]),
  ),
  caption: [Gefährdungen und besondere Risiken],
  notes: (
    [Als «akzeptiert» eingestufte Risiken werden im Abschnitt «Akzeptierte Risiken» aufgeführt.],
  ),
)
// woodcore:/object hazards-table
