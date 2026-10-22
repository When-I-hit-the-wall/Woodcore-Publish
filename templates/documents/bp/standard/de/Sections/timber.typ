#import "/commands.typ": *

// woodcore:object heading title
== Holz und Holzwerkstoffe
// woodcore:/object title

// woodcore:object table timber-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Bezeichnung*], [*Biegung $f_"md"$*], [*Druck parallel zur Faser $f_(c,0,d)$*], [*Schub $f_"vd"$*], [*Mittlerer Elastizitätsmodul $E_(0,"mean")$*]),  // woodcore:hidden 6=[Charakteristische Rohdichte $rho_k$] 7=[Raumlast $gamma$]
    table.hline(stroke: 0.5pt),
    [C24], [14.1], [12.4], [1.5], [11000],  // woodcore:hidden 6=[350] 7=[5]
    [GL24h], [16.0], [16.0], [1.8], [11500],  // woodcore:hidden 6=[385] 7=[5]
    table.hline(stroke: 1pt),
  ),
  caption: [Vollholz und Brettschichtholz (SIA 265, Bemessungswerte für Feuchteklasse 1)],
)
// woodcore:/object timber-table

// woodcore:object text timber-table-notes
Die Festigkeits- und Steifigkeitseigenschaften, die Widerstandsbeiwerte und die Beiwerte zur Berücksichtigung der Lasteinwirkungsdauer werden nach den jeweils gültigen SIA-Normen angewendet. Für Holzwerkstoffe (Platten, Brettsperrholz) gelten die Werte der Norm SIA 265/1.
// woodcore:/object timber-table-notes
