#import "/commands.typ": *

// woodcore:object heading title
== Beton
// woodcore:/object title

// woodcore:object table concrete-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, left, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Bauteil*], [*Festigkeitsklasse*], [*Charakteristische Festigkeit $f_"ck"$*], [*Bemessungswert der Festigkeit $f_"cd"$*], [*Bemessungswert der Schubspannung $tau_"cd"$*], [*Raumlast $gamma$*]),  // woodcore:hidden 6=[Mittlerer Elastizitätsmodul $E_"cm"$]
    table.hline(stroke: 0.5pt),
    [[Bauteil]], [C25/30], [25], [[…]], [[…]], [25],  // woodcore:hidden 6=[[…]]
    [[Bauteil]], [C30/37], [30], [[…]], [[…]], [25],  // woodcore:hidden 6=[[…]]
    table.hline(stroke: 1pt),
  ),
  caption: [Stahlbeton (SIA 262)],
)
// woodcore:/object concrete-table

// woodcore:object text concrete-table-notes
Bemessungswerte nach der Norm SIA 262:2025. Die Anforderungen an die Dauerhaftigkeit (Expositionsklassen) sind im Abschnitt «Dauerhaftigkeit» festgehalten.
// woodcore:/object concrete-table-notes
