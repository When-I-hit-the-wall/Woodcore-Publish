#import "/commands.typ": *

// woodcore:object heading title
== Lastbeiwerte
// woodcore:/object title

// woodcore:object text p1
Art des Bauwerks: [Gebäude]. Für den Nachweis der Tragsicherheit gelten die Lastbeiwerte der Norm SIA 260, Tabelle 1. Bei einem Gebäude sind im Allgemeinen die Werte des Grenzzustands vom Typ 2 (Erreichen des Tragwiderstands des Tragwerks oder eines seiner Bauteile) massgebend.
// woodcore:/object p1

// woodcore:object doc-table load-factors-table
#doc-table(
  columns: (
    (id: "action", title: [Einwirkungen], kind: "wide"),
    (id: "type1", title: [Grenzzustand Typ 1], kind: "number"),
    (id: "type2", title: [Grenzzustand Typ 2], kind: "number"),
    (id: "type3", title: [Grenzzustand Typ 3], kind: "number"),
  ),
  hidden: (),
  rows: (
    (action: [Ständige Einwirkungen, ungünstig wirkend: $γ_(G,"sup")$], type1: 1.1, type2: 1.35, type3: 1.0),
    (action: [Ständige Einwirkungen, günstig wirkend: $γ_(G,"inf")$], type1: 0.9, type2: 0.8, type3: 1.0),
    (action: [Veränderliche Einwirkungen im Allgemeinen: $γ_Q$], type1: 1.5, type2: 1.5, type3: 1.3),
  ),
  caption: [Lastbeiwerte für den Nachweis der Tragsicherheit],
  notes: (
    [G wird je nach ungünstiger oder günstiger Gesamtauswirkung mit $γ_(G,"sup")$ oder $γ_(G,"inf")$ multipliziert (SIA 260, Tabelle 1, Fussnote 1). Die Beiwerte für Einwirkungen aus dem Baugrund und aus Verkehr stehen in der Norm.],
  ),
)
// woodcore:/object load-factors-table
