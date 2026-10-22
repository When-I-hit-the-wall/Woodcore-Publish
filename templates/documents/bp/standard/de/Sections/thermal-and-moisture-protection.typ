#import "/commands.typ": *

// woodcore:object heading title
== Wärmeschutz und Feuchteschutz
// woodcore:/object title

// woodcore:object text p1
Die maximalen Wärmedurchgangskoeffizienten $U_"max"$ nach der Norm #cite-norm(norm: "SIA 180") sind einzuhalten. Für den Nachweis über Einzelbauteilanforderungen gelten für Neubauten die Werte der kantonalen Energiegesetzgebung [Kanton, Verordnung]. [Angestrebtes Label (Minergie …) oder keines.]
// woodcore:/object p1

// woodcore:object table u-values-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, right, left),
    table.hline(stroke: 1pt),
    table.header([*Bauteil*], [*Gegen*], [*Wärmedurchgangskoeffizient $U$*], [*Grundlage*]),
    table.hline(stroke: 0.5pt),
    [Dach], [Aussenluft], [[…]], [[kantonale Verordnung]],
    [Aussenwand], [Aussenluft], [[…]], [[kantonale Verordnung]],
    table.hline(stroke: 1pt),
  ),
  caption: [Grenzwerte der Wärmedurchgangskoeffizienten],
)
// woodcore:/object u-values-table
