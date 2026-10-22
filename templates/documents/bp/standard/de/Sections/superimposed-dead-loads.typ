#import "/commands.typ": *

// woodcore:object heading title
=== Auflasten
// woodcore:/object title
// woodcore:shared superimposed-dead-loads

// woodcore:object text p1
Die Auflasten umfassen Bodenaufbauten, nicht tragende Wände sowie abgehängte Decken [sowie Installationen und Fassade]. Die folgenden Werte sind charakteristische Werte und massgebend für die Bemessung.
// woodcore:/object p1

// woodcore:object table superimposed-table
#figure(
  table(
    columns: (auto, auto, 1fr, auto),
    align: (left, left, left, right),
    table.hline(stroke: 1pt),
    table.header([*Teilbereich*], [*Geschoss*], [*Nutzung / Aufbau*], [*Auflast*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[Bodenaufbau, nichttragende Wände, abgehängte Decken]], [[…]],
    [[…]], [[Dach]], [[Dachaufbau, Begrünung, Photovoltaikanlage]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Auflasten nach Teilbereich und Geschoss],
)
// woodcore:/object superimposed-table

// woodcore:object text p2
Werden die vorgesehenen Schütthöhen oder Belagsstärken überschritten, muss ein Teil des Materials durch leichtes Material (Dämmstoff, Blähton, Porenbeton) ersetzt werden, und zwar nur in Absprache mit der Ingenieurin bzw. dem Ingenieur; das fertig erstellte Terrain bzw. der fertige Boden ist nach der Ausführung zu vermessen, die Ergebnisse sind zur Prüfung abzugeben (SIA 261, Ziffer 2.3.4). Die Auswirkungen eines möglichen Entfernens der Auflast werden geprüft (Ziffer 2.3.5). [Besondere Massnahmen: …]
// woodcore:/object p2
// woodcore:/shared superimposed-dead-loads
