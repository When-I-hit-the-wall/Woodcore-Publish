#import "/commands.typ": *

// woodcore:object heading title
== Gefährdungsbilder
// woodcore:/object title

// woodcore:object text p1
Mögliche Gefährdungsbilder wurden durchgedacht, und geeignete Massnahmen sind festgelegt, um die Gefährdungen unter Kontrolle zu halten oder auf ein akzeptierbar kleines Mass zu beschränken (SIA 260, Ziffer 2.4.4). Die betrachteten Gefährdungsbilder mit Massnahmen, Weiterbearbeitung und Bemessungsannahmen sind:
// woodcore:/object p1

// woodcore:object doc-checklist hazard-influences
#doc-checklist(
  label: [Einflüsse, die eine Gefährdung darstellen können (SIA 260, Ziffer 2.4.5)],
  options: (
    (id: "deviations-actions", label: [Abweichungen von den angenommenen Werten der Einwirkungen], checked: true),
    (id: "ground-actions", label: [Einwirkungen aus dem Baugrund], checked: false),
    (id: "natural-hazards", label: [Einwirkung durch gravitative und meteorologische Naturgefahren], checked: false),
    (id: "physical", label: [Physikalische Einwirkungen, z. B. Feuchtigkeit oder Temperatur], checked: true),
    (id: "chemical", label: [Chemische Einwirkungen, z. B. infolge Streusalz oder Grundwasser], checked: false),
    (id: "biological", label: [Biologische Einwirkungen, z. B. durch Insekten oder Pilze], checked: true),
    (id: "resonance", label: [Resonanzeffekte], checked: false),
    (id: "resistance-deviations", label: [Abweichungen von geplanten Werten des Trag- oder Baugrundwiderstands], checked: false),
    (id: "deterioration", label: [Beeinträchtigung des Tragwiderstands durch Korrosion, Versprödung oder Ermüdung], checked: false),
    (id: "accidental", label: [Beeinträchtigung des Tragwiderstands durch Brand, Explosion, Anprall, Leitungsbruch oder Erdbeben], checked: true),
  ),
)
// woodcore:/object hazard-influences

// woodcore:object doc-table hazard-scenarios-table
#doc-table(
  columns: (
    (id: "scenario", title: [Gefährdungsbild]),
    (id: "measures", title: [Massnahmen]),
    (id: "followup", title: [Weiterbearbeitung]),
    (id: "assumptions", title: [Bemessungsannahmen]),
  ),
  hidden: (),
  rows: (
    (scenario: [[Brand]], measures: [[Brandabschnitte, Feuerwiderstand, ausreichende Bauteilabmessungen, Brandschutzverkleidung]], followup: [[Brandschutzkonzept; Brandfallplanung]], assumptions: [[R 60]]),
    (scenario: [[Erdbeben]], measures: [[Bemessung; konstruktive Massnahmen nach SIA 261]], followup: [[Statische Berechnung]], assumptions: [[Zone, Baugrundklasse, Bauwerksklasse, q]]),
  ),
  caption: [Gefährdungsbilder und Massnahmen],
)
// woodcore:/object hazard-scenarios-table
