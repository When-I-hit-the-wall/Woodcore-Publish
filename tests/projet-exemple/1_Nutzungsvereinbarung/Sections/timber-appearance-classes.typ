#import "/commands.typ": *

// woodcore:object heading title
== Oberflächenqualität der Holzbauteile
// woodcore:/object title

// woodcore:object text p1
Holz ist ein natürlich wachsender Rohstoff: An der Oberfläche kommen Äste, Harzgallen (abhängig von der Holzart), Farbdifferenzen und unter Umständen auch Verfärbungen zum Vorschein. Die Anzahl und Grösse der zulässigen Äste sowie die Zulässigkeit von Verfärbungen lassen sich über Erscheinungsklassen definieren, die während der Projektierung gemeinsam mit der Ingenieurin bzw. dem Ingenieur festzulegen sind. Eine ausführliche Definition findet sich in der Lignum-Publikation «Qualitätskriterien für Holz und Holzwerkstoffe im Bau und Ausbau, Handelsgebräuche für die Schweiz» [Ausgabe].
// woodcore:/object p1

// woodcore:object text p2
Mit zunehmender Dauer verändert sich die Holzoberfläche: Der Witterung direkt ausgesetzte Bauteile vergrauen, was kein Mangel, sondern eine optische Veränderung darstellt; Holzoberflächen in witterungsgeschützten Bereichen dunkeln durch UV-Einstrahlung nach. In Folge wechselnder Luftfeuchtigkeit quillt und schwindet Holz, was zu vereinzelten Rissen in linearen Bauteilen (Stützen, Träger) führen kann.
// woodcore:/object p2

// woodcore:object doc-table appearance-classes-table
#doc-table(
  columns: (
    (id: "member", title: [Bauteil]),
    (id: "product", title: [Produkt]),
    (id: "class", title: [Erscheinungsklasse]),
    (id: "remark", title: [Bemerkung]),
  ),
  hidden: ("remark",),
  rows: (
    (member: [[Sichtbare Stützen und Träger]], product: [Voll- und Brettschichtholz], class: [N: Normalqualität (Bauholz)], remark: []),
    (member: [[Nicht sichtbare Bauteile]], product: [Voll- und Brettschichtholz], class: [I: Industriequalität, ohne Anforderungen an das Aussehen], remark: []),
  ),
  caption: [Erscheinungsklassen nach Bauteil],
)
// woodcore:/object appearance-classes-table
