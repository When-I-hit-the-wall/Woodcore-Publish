#import "/commands.typ": *

// woodcore:object heading title
== Anforderungen an die Rissbildung
// woodcore:/object title

// woodcore:object text p1
Die Norm SIA 262 unterscheidet bezüglich Rissbildung zwischen normalen, erhöhten und hohen Anforderungen: normale, wenn Risse toleriert und keine besonderen Ansprüche an Dichtigkeit und Aussehen gestellt werden; erhöhte, wenn besondere Ansprüche an Funktionstüchtigkeit und Aussehen bestehen und eine gute Rissverteilung angestrebt wird; hohe, wenn eine Begrenzung der Rissbreiten erwünscht ist. Diese Anforderungen gelten sowohl für Beanspruchungen aus Zwang (z. B. Schwinden) als auch aus Biegung; erhöhte oder hohe Anforderungen reduzieren die zulässigen Stahlspannungen und führen zu einem erhöhten Bewehrungsgehalt.
// woodcore:/object p1

// woodcore:object table cracking-requirements-table
#figure(
  table(
    columns: (auto, auto),
    align: (left, left),
    table.hline(stroke: 1pt),
    table.header([*Bereich*], [*Anforderung*]),  // woodcore:hidden 3=[Mittlere Rissweite $w_m$] 4=[Maximale Rissweite $w_"max"$]
    table.hline(stroke: 0.5pt),
    [[Allgemein]], [Normale],  // woodcore:hidden 3=[0.7] 4=[1.2]
    [[Sichtbetonbauteile]], [Erhöhte],  // woodcore:hidden 3=[0.5] 4=[0.9]
    table.hline(stroke: 1pt),
  ),
  caption: [Anforderungen nach Bereich],
)
// woodcore:/object cracking-requirements-table

// woodcore:object text cracking-requirements-table-notes
Zu erwartende Rissweiten bei den drei Anforderungsstufen: $w_m$ = 0.7 / 0.5 / 0.25 mm und $w_"max"$ = 1.2 / 0.9 / 0.4 mm ($w_"max"$ = 1.7 · $w_m$, 95 %-Fraktile), nach dem Zuggurtmodell (Dokumentation SIA D 0182).
// woodcore:/object cracking-requirements-table-notes
