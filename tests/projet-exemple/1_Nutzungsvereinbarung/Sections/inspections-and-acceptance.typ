#import "/commands.typ": *

// woodcore:object heading title
== Kontrollen und Abnahmen
// woodcore:/object title

// woodcore:object text p1
Die folgenden Kontrollen und Abnahmen werden vereinbart; das detaillierte Kontrollprogramm wird im Kontrollplan festgelegt.
// woodcore:/object p1

// woodcore:object doc-checklist inspections-list
#doc-checklist(
  label: [Kontrollen und Abnahmen],
  options: (
    (id: "shell-acceptance", label: [Abnahme des Holzrohbaus vor Beginn des Innenausbaus], checked: true),
    (id: "acoustic-measurements", label: [Akustikmessungen (Geschossdecken) vor dem Einbau des definitiven Bodenbelags], checked: true),
    (id: "excavation-acceptance", label: [Abnahme der Aushubsohle durch die Tragwerksplanung oder das Geologiebüro], checked: false),
    (id: "timber-moisture", label: [Kontrolle der Holzfeuchte vor dem Schliessen der Bauteile], checked: false),
    (id: "final-acceptance", label: [Schlussabnahme [Kalenderwoche …]], checked: true),
  ),
)
// woodcore:/object inspections-list
