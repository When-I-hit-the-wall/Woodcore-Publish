#import "/commands.typ": *

// woodcore:object heading title
== Wärmeschutz und Feuchteschutz
// woodcore:/object title

// woodcore:object text p1
Die maximalen Wärmedurchgangskoeffizienten $U_"max"$ nach der Norm #cite-norm(norm: "SIA 180") sind einzuhalten. Für den Nachweis über Einzelbauteilanforderungen gelten für Neubauten die Werte der kantonalen Energiegesetzgebung [Kanton, Verordnung]. [Angestrebtes Label (Minergie …) oder keines.]
// woodcore:/object p1

// woodcore:object doc-table u-values-table
#doc-table(
  columns: (
    (id: "element", title: [Bauteil]),
    (id: "against", title: [Gegen]),
    (id: "U", title: [Wärmedurchgangskoeffizient $U$], unit: "W/(m²K)", kind: "number"),
    (id: "basis", title: [Grundlage]),
  ),
  hidden: (),
  rows: (
    (element: [Dach], against: [Aussenluft], U: [[…]], basis: [[kantonale Verordnung]]),
    (element: [Aussenwand], against: [Aussenluft], U: [[…]], basis: [[kantonale Verordnung]]),
  ),
  caption: [Grenzwerte der Wärmedurchgangskoeffizienten],
)
// woodcore:/object u-values-table
