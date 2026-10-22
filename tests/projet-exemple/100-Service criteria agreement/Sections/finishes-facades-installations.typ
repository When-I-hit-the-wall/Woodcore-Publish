#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Ausbauten, Fassaden und Installationen
// woodcore:/object title

// woodcore:object text p1
Nichttragende Wände, die mit dem Rohbau erstellt werden (z. B. nicht tragendes Mauerwerk), müssen gegenüber der Decke mit weichen Zwischenlagen getrennt werden, sodass die oben definierten Deckenverformungen (zusätzlich zur Bautoleranz) ohne Folgen für sie sind. Nichttragende Wände, die nach dem Rohbau und dem Entfernen der Spriessung erstellt werden, müssen eine weiche Zwischenlage von mindestens [20] mm gegenüber der Decke aufweisen. Für nicht tragende Mauerwerkswände, die sich nicht selbst stabilisieren, ist für den Erdbebenfall eine Kippsicherung vorzusehen. [Gewicht und zulässige Verformungen der Fassade: …]
// woodcore:/object p1

// woodcore:object table deformation-margins
#figure(
  table(
    columns: (auto, auto),
    align: (left, right),
    table.hline(stroke: 1pt),
    table.header([*Bauteil*], [*Zu erwartende Deckenverformung*]),
    table.hline(stroke: 0.5pt),
    [Nicht tragende Innenwände], [[…]],
    [Fassade], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Nach dem Einbau einzuplanender Verformungsspielraum],
)
// woodcore:/object deformation-margins

// woodcore:object text deformation-margins-notes
Verformungsspielraum zusätzlich zur Bautoleranz; die Deckenränder sind vor Produktion und Einbau der Fassade aufzunehmen.
// woodcore:/object deformation-margins-notes
