#import "/commands.typ": *

// woodcore:object heading title
== Brandwiderstand des Tragwerks
// woodcore:/object title

// woodcore:object text p1
Die Brandschutzanforderungen werden nach den schweizerischen Brandschutzvorschriften (VKF), der Lignum-Dokumentation Brandschutz und dem [baulichen / technischen] Brandschutzkonzept festgelegt. Brand wird nach der Norm SIA 261, Kapitel 15, als aussergewöhnliche Einwirkung behandelt. Die Anforderungen an das Tragwerk sind:
// woodcore:/object p1

// woodcore:object doc-choice structure-fire-resistance
#doc-choice(
  label: [Feuerwiderstand des Tragwerks (allgemein)],
  options: (
    (id: "r30", label: [R 30]),
    (id: "r60", label: [R 60]),
    (id: "r90", label: [R 90]),
    (id: "none", label: [Keine Anforderungen]),
  ),
  selected: "r60",
)
// woodcore:/object structure-fire-resistance

// woodcore:object text p2
[Ausnahmen je Geschoss (z. B. Untergeschoss, oberstes Geschoss).] Der geforderte Feuerwiderstand wird grundsätzlich durch die Betonüberdeckung der Bewehrung und die minimalen Bauteilabmessungen (Beton), durch brandschutztechnische Beplankungen oder Abbrandberechnungen gemäss den Lignum-Dokumentationen (Holz) gewährleistet; vorfabrizierte Bauteile aus Beton oder Stahl müssen über eine VKF-Zulassung verfügen.
// woodcore:/object p2
