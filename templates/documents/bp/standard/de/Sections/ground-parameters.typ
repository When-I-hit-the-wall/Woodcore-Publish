#import "/commands.typ": *

// woodcore:object heading title
== Baugrundkennwerte
// woodcore:/object title

// woodcore:object text p1
Die Baugrundkennwerte sind im geotechnischen Bericht [Verfasser, Datum] ersichtlich. Für die Bemessung werden folgende charakteristische Werte angenommen (vorsichtige Erwartungswerte nach SIA 260, Ziffer 3.3.3.5 und SIA 267):
// woodcore:/object p1

// woodcore:object table ground-parameters-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Schicht*], [*Raumlast $gamma$*], [*Reibungswinkel $phi'$*], [*Kohäsion $c'$*], [*Steifemodul $E_s$*]),  // woodcore:hidden 6=[Bemerkung]
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]], [[…]], [[…]],  // woodcore:hidden 6=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Charakteristische Baugrundkennwerte],
)
// woodcore:/object ground-parameters-table
