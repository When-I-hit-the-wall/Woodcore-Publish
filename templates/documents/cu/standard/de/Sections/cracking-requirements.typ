#import "/commands.typ": *

// woodcore:object heading title
== Anforderungen an die Rissbildung
// woodcore:/object title

// woodcore:object text p1
Die Norm SIA 262 unterscheidet bezüglich Rissbildung zwischen normalen, erhöhten und hohen Anforderungen: normale, wenn Risse toleriert und keine besonderen Ansprüche an Dichtigkeit und Aussehen gestellt werden; erhöhte, wenn besondere Ansprüche an Funktionstüchtigkeit und Aussehen bestehen und eine gute Rissverteilung angestrebt wird; hohe, wenn eine Begrenzung der Rissbreiten erwünscht ist. Diese Anforderungen gelten sowohl für Beanspruchungen aus Zwang (z. B. Schwinden) als auch aus Biegung; erhöhte oder hohe Anforderungen reduzieren die zulässigen Stahlspannungen und führen zu einem erhöhten Bewehrungsgehalt.
// woodcore:/object p1

// woodcore:object doc-table cracking-requirements-table
#doc-table(
  columns: (
    (id: "area", title: [Bereich]),
    (id: "level", title: [Anforderung]),
    (id: "wm", title: [Mittlere Rissweite $w_m$], unit: "mm", kind: "number"),
    (id: "wmax", title: [Maximale Rissweite $w_"max"$], unit: "mm", kind: "number"),
  ),
  hidden: ("wm", "wmax"),
  rows: (
    (area: [[Allgemein]], level: [Normale], wm: 0.7, wmax: 1.2),
    (area: [[Sichtbetonbauteile]], level: [Erhöhte], wm: 0.5, wmax: 0.9),
  ),
  caption: [Anforderungen nach Bereich],
  notes: (
    [Zu erwartende Rissweiten bei den drei Anforderungsstufen: $w_m$ = 0.7 / 0.5 / 0.25 mm und $w_"max"$ = 1.2 / 0.9 / 0.4 mm ($w_"max"$ = 1.7 · $w_m$, 95 %-Fraktile), nach dem Zuggurtmodell (Dokumentation SIA D 0182).],
  ),
)
// woodcore:/object cracking-requirements-table
