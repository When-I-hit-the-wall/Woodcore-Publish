#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Wasserdichtigkeit
// woodcore:/object title

// woodcore:object text p1
[Abdichtungskonzept der erdberührten Bauteile (z. B. Weisse Wanne oder Gelbe Wanne): Die Anforderungen werden in Anlehnung an die Norm SIA 272 festgelegt; das detaillierte Konzept wird in der Ausführungsplanung mit der Unternehmung und gegebenenfalls dem Systemanbieter erarbeitet. Die Verantwortung für die Einhaltung der Kriterien liegt bei der Bauunternehmung bzw. dem Abdichtungs-Unternehmen. Die Erkennung der Gefahr von Kondenswasserbildung ist Sache der Bauphysik.]
// woodcore:/object p1

// woodcore:object table sealing-classes-table
#figure(
  table(
    columns: (auto, 1fr, auto),
    align: (right, left, left),
    table.hline(stroke: 1pt),
    table.header([*Klasse*], [*Definition*], [*Bauteile*]),
    table.hline(stroke: 0.5pt),
    [1], [Vollständig trocken; keine Feuchtstellen an den trockenseitigen Bauwerksoberflächen zugelassen.], [[…]],
    [2], [Trocken bis leicht feucht; einzelne Feuchtstellen zugelassen; kein tropfendes Wasser an den trockenseitigen Bauwerksoberflächen.], [[…]],
    [3], [Feucht; örtlich begrenzte Feuchtstellen und einzelne Tropfstellen zugelassen; nachträgliches Injizieren von Rissen akzeptiert.], [[…]],
    [4], [Feucht bis nass; Feucht- und Tropfstellen zugelassen.], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Dichtigkeitsklassen und Zuordnung zu Bauteilen],
)
// woodcore:/object sealing-classes-table
