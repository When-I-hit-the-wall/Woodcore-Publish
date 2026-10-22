#import "/commands.typ": *

// woodcore:object heading title
== Baugrund
// woodcore:/object title
// woodcore:shared ground-conditions

// woodcore:object text p1
[Art des Baugrunds, Schichtaufbau, hydrogeologische Verhältnisse (Grundwasser, Hang- und Schichtwasser) und Quelle dieser Angaben: geotechnischer Bericht (Verfasser, Datum). Sind die Untersuchungen nicht abgeschlossen, die vor der Projektierung noch nötigen Abklärungen angeben.]
// woodcore:/object p1

// woodcore:object table ground-layers
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, right),
    table.hline(stroke: 1pt),
    table.header([*Schicht*], [*Beschreibung*], [*Tiefe / Mächtigkeit*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Baugrundschichten],
)
// woodcore:/object ground-layers

// woodcore:object table design-water-levels
#figure(
  table(
    columns: (auto, auto),
    align: (left, right),
    table.hline(stroke: 1pt),
    table.header([*Wasserstand*], [*Kote (m ü. M.)*]),  // woodcore:hidden 3=[Bemerkung]
    table.hline(stroke: 0.5pt),
    [Hochwasser (HW)], [[…]],  // woodcore:hidden 3=[]
    [Mittelwasser (MW)], [[…]],  // woodcore:hidden 3=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Massgebende Wasserstände],
)
// woodcore:/object design-water-levels

// woodcore:object text ground-profile
#figure(rect(width: 100%, height: 5cm, stroke: 0.5pt + luma(60%))[[Abbildung mit Legende und Quelle]], caption: [Geologisches Profil / Auszug aus dem geotechnischen Bericht])
// woodcore:/object ground-profile
// woodcore:/shared ground-conditions
