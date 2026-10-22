#import "/commands.typ": *

// woodcore:object heading title
== Horizontale Auslenkungen
// woodcore:/object title

// woodcore:object text p1
Die horizontalen Auslenkungen infolge der veränderlichen Einwirkungen werden auf die Richtwerte der Norm SIA 260, Anhang A, Tabelle 4 begrenzt; h bezeichnet die Stockwerkshöhe, H die Gebäudehöhe. Für die Bemessungssituation Erdbeben sind die horizontalen Auslenkungen pro Stockwerk bei Einbauten mit sprödem bzw. duktilem Verhalten auf 1/500 bzw. 1/200 der Stockwerkshöhe zu begrenzen (Ziffer 4.4.4.5).
// woodcore:/object p1

// woodcore:object table horizontal-limits-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, center, left),
    table.hline(stroke: 1pt),
    table.header([*Kriterium*], [*Grenzwert*], [*Lastfall (SIA 260, Tab. 4)*]),
    table.hline(stroke: 0.5pt),
    [Einbauten mit sprödem Verhalten], [$u <= h \/ 500$], [selten (20)],
    [Einbauten mit duktilem Verhalten], [$u <= h \/ 200$], [häufig (21)],
    [Nutzung und Betrieb], [$u <= H \/ 300$], [häufig (21)],
    [Aussehen], [$u <= h \/ 250$], [quasi-ständig (22)],
    table.hline(stroke: 1pt),
  ),
  caption: [Zulässige horizontale Auslenkungen],
)
// woodcore:/object horizontal-limits-table
