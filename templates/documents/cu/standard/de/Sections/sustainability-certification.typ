#import "/commands.typ": *

// woodcore:object heading title
== Zertifizierung und Nachhaltigkeits-Standard
// woodcore:/object title
// woodcore:shared sustainability-certification

// woodcore:object doc-checklist certification-choice
#doc-checklist(
  label: [Angestrebte Zertifizierung oder angestrebter Standard],
  options: (
    (id: "snbs", label: [SNBS Hochbau (Standard Nachhaltiges Bauen Schweiz)], checked: false),
    (id: "minergie", label: [Minergie], checked: false),
    (id: "minergie-p", label: [Minergie-P], checked: false),
    (id: "minergie-a", label: [Minergie-A], checked: false),
    (id: "minergie-eco", label: [Minergie-ECO (Zusatz)], checked: false),
    (id: "sia-2040", label: [SIA-Effizienzpfad Energie (SIA 2040) und Graue Energie (SIA 2032)], checked: false),
    (id: "none", label: [Keine Zertifizierung angestrebt], checked: true),
  ),
)
// woodcore:/object certification-choice

// woodcore:object text p1
[Angeben, was das angestrebte Ziel für das Tragwerk bedeutet, z. B. Grenzwerte für Treibhausgasemissionen, Graue Energie und gespeicherten Kohlenstoff sowie den möglichst weitgehenden Einsatz von Holzbauteilen mit geringen CO₂-Emissionen und hoher Kohlenstoffspeicherung.]
// woodcore:/object p1

// woodcore:object text p2
[Festhalten, wer die Einhaltung der Grenzwerte prüft: diese Prüfung gehört in der Regel nicht zu den Aufgaben der Tragwerksplanung.]
// woodcore:/object p2
// woodcore:/shared sustainability-certification
