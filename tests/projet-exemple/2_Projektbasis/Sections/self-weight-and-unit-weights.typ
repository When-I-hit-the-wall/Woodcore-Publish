#import "/commands.typ": *

// woodcore:object heading title
=== Eigengewicht und Raumlasten
// woodcore:/object title

// woodcore:object text p1
Die ständigen Einwirkungen wirken dauernd. Sie umfassen das Eigengewicht des Tragwerks und die ständigen Lasten der Bauteile. Das Eigengewicht wird aus den plangemässen Abmessungen und den mittleren Raumlasten der Norm SIA 261, Anhang A ermittelt; es wird gesamthaft mit oberen oder unteren Bemessungswerten berücksichtigt, je nachdem, ob die Gesamtauswirkung ungünstig oder günstig ist (SIA 261, Ziffer 2.1.2).
// woodcore:/object p1

// woodcore:object doc-table permanent-actions-table
#doc-table(
  columns: (
    (id: "action", title: [Einwirkung / Gefährdung]),
    (id: "measures", title: [Massnahmen]),
    (id: "followup", title: [Weiterbearbeitung]),
    (id: "assumptions", title: [Bemessungsannahmen]),
  ),
  hidden: (),
  rows: (
    (action: [Eigengewicht], measures: [Bemessung; Ausführungskontrolle], followup: [Statische Berechnung; Kontrollplan], assumptions: [Raumlasten nach SIA 261, Anhang A (Tabelle unten)]),
    (action: [Auflasten], measures: [Bemessung; Ausführungskontrollen; Überwachung während der Nutzung betreffend Änderungen], followup: [Statische Berechnung; Kontrollplan; Überwachungsplan], assumptions: [Gemäss den Bauteilaufbauten (Abschnitt «Auflasten»)]),
  ),
  caption: [Ständige Einwirkungen: Massnahmen und Annahmen],
)
// woodcore:/object permanent-actions-table

// woodcore:object doc-table unit-weights-table
#doc-table(
  columns: (
    (id: "material", title: [Material]),
    (id: "gamma", title: [Raumlast $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: (),
  rows: (
    (material: [Baustahl], gamma: 78.5),
    (material: [Beton, bewehrt], gamma: 25),
    (material: [Holz, Nadelhölzer allgemein], gamma: 5),
  ),
  caption: [Raumlasten der Baustoffe],
  notes: (
    [Mittelwerte der Norm SIA 261, Anhang A, Tabelle 28; die vollständige Tabelle steht in der Norm.],
  ),
)
// woodcore:/object unit-weights-table
