#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
=== Eigengewicht und Raumlasten
// woodcore:/object title

// woodcore:object text p1
Die ständigen Einwirkungen wirken dauernd. Sie umfassen das Eigengewicht des Tragwerks und die ständigen Lasten der Bauteile. Das Eigengewicht wird aus den plangemässen Abmessungen und den mittleren Raumlasten der Norm SIA 261, Anhang A ermittelt; es wird gesamthaft mit oberen oder unteren Bemessungswerten berücksichtigt, je nachdem, ob die Gesamtauswirkung ungünstig oder günstig ist (SIA 261, Ziffer 2.1.2).
// woodcore:/object p1

// woodcore:object table permanent-actions-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Einwirkung / Gefährdung*], [*Massnahmen*], [*Weiterbearbeitung*], [*Bemessungsannahmen*]),
    table.hline(stroke: 0.5pt),
    [Eigengewicht], [Bemessung; Ausführungskontrolle], [Statische Berechnung; Kontrollplan], [Raumlasten nach SIA 261, Anhang A (Tabelle unten)],
    [Auflasten], [Bemessung; Ausführungskontrollen; Überwachung während der Nutzung betreffend Änderungen], [Statische Berechnung; Kontrollplan; Überwachungsplan], [Gemäss den Bauteilaufbauten (Abschnitt «Auflasten»)],
    table.hline(stroke: 1pt),
  ),
  caption: [Ständige Einwirkungen: Massnahmen und Annahmen],
)
// woodcore:/object permanent-actions-table

// woodcore:object table unit-weights-table
#figure(
  table(
    columns: (auto, auto),
    align: (left, right),
    table.hline(stroke: 1pt),
    table.header([*Material*], [*Raumlast $gamma$*]),
    table.hline(stroke: 0.5pt),
    [Baustahl], [78.5],
    [Beton, bewehrt], [25],
    [Holz, Nadelhölzer allgemein], [5],
    table.hline(stroke: 1pt),
  ),
  caption: [Raumlasten der Baustoffe],
)
// woodcore:/object unit-weights-table

// woodcore:object text unit-weights-table-notes
Mittelwerte der Norm SIA 261, Anhang A, Tabelle 28; die vollständige Tabelle steht in der Norm.
// woodcore:/object unit-weights-table-notes
