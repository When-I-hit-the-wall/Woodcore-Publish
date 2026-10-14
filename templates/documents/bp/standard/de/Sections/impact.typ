#import "/commands.typ": *

// woodcore:object heading title
=== Anprall
// woodcore:/object title
// woodcore:shared impact

// woodcore:object text p1
Anprall ist eine aussergewöhnliche Einwirkung (SIA 261, Ziffer 14.1.1). Er wird berücksichtigt, wenn das Tragwerk innerorts näher als 3 m oder ausserorts näher als 10 m vom Fahrbahnrand liegt (Ziffer 14.2.1). Für den Anprall von Schiffen, Helikoptern, Flugzeugen oder abstürzenden Teilen werden die Ersatzkräfte projektspezifisch festgelegt und in der Projektbasis festgehalten (Ziffer 14.1.8). [Schutzmassnahmen (Sitzbänke, Poller): …]
// woodcore:/object p1

// woodcore:object doc-table impact-table
#doc-table(
  columns: (
    (id: "storey", title: [Geschoss]),
    (id: "area", title: [Teilbereich]),
    (id: "use", title: [Nutzung], kind: "wide"),
    (id: "category", title: [Kategorie (SIA 261)], kind: "math"),
    (id: "force", title: [Anprallkraft $Q_"gd"$], unit: "kN", kind: "number"),
    (id: "height", title: [Anprallhöhe], unit: "m", kind: "number"),
  ),
  hidden: (),
  rows: (
    (storey: [[…]], area: [[…]], use: [[Parkierung für Fahrzeuge bis 3.5 t]], category: "F", force: 60, height: 0.6),
    (storey: [[…]], area: [[…]], use: [[Anlieferung, Fahrzeuge von 3.5 t bis 16 t]], category: "G", force: 180, height: 1.2),
  ),
  caption: [Anprallkräfte von Strassenfahrzeugen in Gebäuden],
)
// woodcore:/object impact-table
// woodcore:/shared impact
