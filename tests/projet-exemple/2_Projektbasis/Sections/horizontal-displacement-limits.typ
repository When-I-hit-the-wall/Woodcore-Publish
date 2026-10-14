#import "/commands.typ": *

// woodcore:object heading title
== Horizontale Auslenkungen
// woodcore:/object title

// woodcore:object text p1
Die horizontalen Auslenkungen infolge der veränderlichen Einwirkungen werden auf die Richtwerte der Norm SIA 260, Anhang A, Tabelle 4 begrenzt; h bezeichnet die Stockwerkshöhe, H die Gebäudehöhe. Für die Bemessungssituation Erdbeben sind die horizontalen Auslenkungen pro Stockwerk bei Einbauten mit sprödem bzw. duktilem Verhalten auf 1/500 bzw. 1/200 der Stockwerkshöhe zu begrenzen (Ziffer 4.4.4.5).
// woodcore:/object p1

// woodcore:object doc-table horizontal-limits-table
#doc-table(
  columns: (
    (id: "criterion", title: [Kriterium]),
    (id: "limit", title: [Grenzwert], kind: "math"),
    (id: "load_case", title: [Lastfall (SIA 260, Tab. 4)]),
  ),
  hidden: (),
  rows: (
    (criterion: [Einbauten mit sprödem Verhalten], limit: [$u <= h \/ 500$], load_case: [selten (20)]),
    (criterion: [Einbauten mit duktilem Verhalten], limit: [$u <= h \/ 200$], load_case: [häufig (21)]),
    (criterion: [Nutzung und Betrieb], limit: [$u <= H \/ 300$], load_case: [häufig (21)]),
    (criterion: [Aussehen], limit: [$u <= h \/ 250$], load_case: [quasi-ständig (22)]),
  ),
  caption: [Zulässige horizontale Auslenkungen],
)
// woodcore:/object horizontal-limits-table
