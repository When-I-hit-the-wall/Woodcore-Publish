#import "/commands.typ": *

// woodcore:object heading title
=== Auflasten
// woodcore:/object title
// woodcore:shared superimposed-dead-loads

// woodcore:object text p1
Die Auflasten umfassen Bodenaufbauten, nicht tragende Wände sowie abgehängte Decken [sowie Installationen und Fassade]. Die folgenden Werte sind charakteristische Werte und massgebend für die Bemessung.
// woodcore:/object p1

// woodcore:object dead-load-table superimposed-table
#dead-load-table(
  columns: (
    (id: "zone"),
    (id: "storey"),
    (id: "buildup"),
    (id: "load"),
  ),
  hidden: (),
  rows: (
    (zone: [[…]], storey: [[…]], buildup: [[Bodenaufbau, nichttragende Wände, abgehängte Decken]], load: [[…]]),
    (zone: [[…]], storey: [[Dach]], buildup: [[Dachaufbau, Begrünung, Photovoltaikanlage]], load: [[…]]),
  ),
  caption: [Auflasten nach Teilbereich und Geschoss],
)
// woodcore:/object superimposed-table

// woodcore:object text p2
Werden die vorgesehenen Schütthöhen oder Belagsstärken überschritten, muss ein Teil des Materials durch leichtes Material (Dämmstoff, Blähton, Porenbeton) ersetzt werden, und zwar nur in Absprache mit der Ingenieurin bzw. dem Ingenieur; das fertig erstellte Terrain bzw. der fertige Boden ist nach der Ausführung zu vermessen, die Ergebnisse sind zur Prüfung abzugeben (SIA 261, Ziffer 2.3.4). Die Auswirkungen eines möglichen Entfernens der Auflast werden geprüft (Ziffer 2.3.5). [Besondere Massnahmen: …]
// woodcore:/object p2
// woodcore:/shared superimposed-dead-loads
