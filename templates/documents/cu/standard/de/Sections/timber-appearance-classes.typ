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

// woodcore:object table appearance-classes-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Bauteil*], [*Produkt*], [*Erscheinungsklasse*]),  // woodcore:hidden 4=[Bemerkung]
    table.hline(stroke: 0.5pt),
    [[Sichtbare Stützen und Träger]], [Voll- und Brettschichtholz], [N: Normalqualität (Bauholz)],  // woodcore:hidden 4=[]
    [[Nicht sichtbare Bauteile]], [Voll- und Brettschichtholz], [I: Industriequalität, ohne Anforderungen an das Aussehen],  // woodcore:hidden 4=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Erscheinungsklassen nach Bauteil],
)
// woodcore:/object appearance-classes-table
