#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Lastbeiwerte
// woodcore:/object title

// woodcore:object text p1
Art des Bauwerks: [Gebäude]. Für den Nachweis der Tragsicherheit gelten die Lastbeiwerte der Norm SIA 260, Tabelle 1. Bei einem Gebäude sind im Allgemeinen die Werte des Grenzzustands vom Typ 2 (Erreichen des Tragwiderstands des Tragwerks oder eines seiner Bauteile) massgebend.
// woodcore:/object p1

// woodcore:object table load-factors-table
#figure(
  table(
    columns: (1fr, auto, auto, auto),
    align: (left, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Einwirkungen*], [*Grenzzustand Typ 1*], [*Grenzzustand Typ 2*], [*Grenzzustand Typ 3*]),
    table.hline(stroke: 0.5pt),
    [Ständige Einwirkungen, ungünstig wirkend: $γ_(G,"sup")$], [1.1], [1.35], [1.0],
    [Ständige Einwirkungen, günstig wirkend: $γ_(G,"inf")$], [0.9], [0.8], [1.0],
    [Veränderliche Einwirkungen im Allgemeinen: $γ_Q$], [1.5], [1.5], [1.3],
    table.hline(stroke: 1pt),
  ),
  caption: [Lastbeiwerte für den Nachweis der Tragsicherheit],
)
// woodcore:/object load-factors-table

// woodcore:object text load-factors-table-notes
G wird je nach ungünstiger oder günstiger Gesamtauswirkung mit $γ_(G,"sup")$ oder $γ_(G,"inf")$ multipliziert (SIA 260, Tabelle 1, Fussnote 1). Die Beiwerte für Einwirkungen aus dem Baugrund und aus Verkehr stehen in der Norm.
// woodcore:/object load-factors-table-notes
