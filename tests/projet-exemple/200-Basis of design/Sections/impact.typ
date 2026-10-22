#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
=== Anprall
// woodcore:/object title
// woodcore:shared impact

// woodcore:object text p1
Anprall ist eine aussergewöhnliche Einwirkung (SIA 261, Ziffer 14.1.1). Er wird berücksichtigt, wenn das Tragwerk innerorts näher als 3 m oder ausserorts näher als 10 m vom Fahrbahnrand liegt (Ziffer 14.2.1). Für den Anprall von Schiffen, Helikoptern, Flugzeugen oder abstürzenden Teilen werden die Ersatzkräfte projektspezifisch festgelegt und in der Projektbasis festgehalten (Ziffer 14.1.8). [Schutzmassnahmen (Sitzbänke, Poller): …]
// woodcore:/object p1

// woodcore:object table impact-table
#figure(
  table(
    columns: (auto, auto, 1fr, auto, auto, auto),
    align: (left, left, left, center, right, right),
    table.hline(stroke: 1pt),
    table.header([*Geschoss*], [*Teilbereich*], [*Nutzung*], [*Kategorie (SIA 261)*], [*Anprallkraft $Q_"gd"$*], [*Anprallhöhe*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[Parkierung für Fahrzeuge bis 3.5 t]], [F], [60], [0.6],
    [[…]], [[…]], [[Anlieferung, Fahrzeuge von 3.5 t bis 16 t]], [G], [180], [1.2],
    table.hline(stroke: 1pt),
  ),
  caption: [Anprallkräfte von Strassenfahrzeugen in Gebäuden],
)
// woodcore:/object impact-table
// woodcore:/shared impact
