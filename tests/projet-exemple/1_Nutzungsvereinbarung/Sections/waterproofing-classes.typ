#import "/commands.typ": *

// woodcore:object heading title
== Wasserdichtigkeit
// woodcore:/object title

// woodcore:object text p1
[Abdichtungskonzept der erdberührten Bauteile (z. B. Weisse Wanne oder Gelbe Wanne): Die Anforderungen werden in Anlehnung an die Norm SIA 272 festgelegt; das detaillierte Konzept wird in der Ausführungsplanung mit der Unternehmung und gegebenenfalls dem Systemanbieter erarbeitet. Die Verantwortung für die Einhaltung der Kriterien liegt bei der Bauunternehmung bzw. dem Abdichtungs-Unternehmen. Die Erkennung der Gefahr von Kondenswasserbildung ist Sache der Bauphysik.]
// woodcore:/object p1

// woodcore:object doc-table sealing-classes-table
#doc-table(
  columns: (
    (id: "class", title: [Klasse], kind: "number"),
    (id: "definition", title: [Definition], kind: "wide"),
    (id: "parts", title: [Bauteile]),
  ),
  hidden: (),
  rows: (
    (class: 1, definition: [Vollständig trocken; keine Feuchtstellen an den trockenseitigen Bauwerksoberflächen zugelassen.], parts: [[…]]),
    (class: 2, definition: [Trocken bis leicht feucht; einzelne Feuchtstellen zugelassen; kein tropfendes Wasser an den trockenseitigen Bauwerksoberflächen.], parts: [[…]]),
    (class: 3, definition: [Feucht; örtlich begrenzte Feuchtstellen und einzelne Tropfstellen zugelassen; nachträgliches Injizieren von Rissen akzeptiert.], parts: [[…]]),
    (class: 4, definition: [Feucht bis nass; Feucht- und Tropfstellen zugelassen.], parts: [[…]]),
  ),
  caption: [Dichtigkeitsklassen und Zuordnung zu Bauteilen],
)
// woodcore:/object sealing-classes-table
