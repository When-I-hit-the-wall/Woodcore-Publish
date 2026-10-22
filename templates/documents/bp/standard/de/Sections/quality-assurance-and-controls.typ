#import "/commands.typ": *

// woodcore:object heading title
== Qualitätssicherung und Kontrollen
// woodcore:/object title

// woodcore:object text p1
Die Gewährleistung einer angemessenen Zuverlässigkeit erfordert Massnahmen zur Qualitätssicherung während der Projektierung, Ausführung, Nutzung und Erhaltung (SIA 260, Ziffer 2.3.6), mit Verantwortlichkeiten, Abläufen, Kontrollen und Korrekturmechanismen (Ziffer 2.5.2). Das Tragsystem wird so gewählt, dass eine ausreichende Redundanz (Unempfindlichkeit gegenüber lokalem Versagen, Ziffer 2.4.6) besteht. Wesentliche Instrumente sind [der Kontrollplan der Tragwerksplanung und der Prüfplan der Bauunternehmung gemäss dem SIA-Merkblatt 2007 «Qualität im Bauwesen»].
// woodcore:/object p1

// woodcore:object table controls-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Phase*], [*Massnahme*], [*Verantwortlich*], [*Kontrolle / Nachweis*]),
    table.hline(stroke: 0.5pt),
    [Projektierung], [[Nachweis $E_d$ ≤ $R_d$ nach den SIA-Normen; Plausibilitätskontrolle der Ergebnisse]], [[Ingenieur:in]], [[Kontrolle durch Dritte]],
    [Ausführung], [[Qualitätssicherungsprogramm der Unternehmung; Prüfung und Überwachung der verwendeten Baustoffe]], [[Unternehmung / Bauleitung]], [[Kontrollplan]],
    table.hline(stroke: 1pt),
  ),
  caption: [Massnahmen und Kontrollen],
)
// woodcore:/object controls-table
