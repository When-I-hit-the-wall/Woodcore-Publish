#import "/commands.typ": *

// woodcore:object heading title
== Radonbelastung
// woodcore:/object title

// woodcore:object doc-choice radon-risk
#doc-choice(
  label: [Radonrisiko (Radonkarte der Schweiz, BAG)],
  options: (
    (id: "low", label: [Geringes Risiko: keine rohbaulichen Massnahmen]),
    (id: "medium", label: [Mittleres Risiko: Massnahmen gemäss Empfehlung BAG (z. B. dichte Rohrdurchführungen)]),
    (id: "high", label: [Hohes Risiko: Massnahmen gemäss Empfehlungen BAG (z. B. dichte Rohrdurchführungen, Bodenplatte mit Dichtigkeitsklasse 1)]),
  ),
  selected: none,
)
// woodcore:/object radon-risk

// woodcore:object text p1
Eine allfällige Abdichtung gegen Radon liegt im Aufgaben- und Verantwortungsbereich der Bauherrschaft und der Architekturplanung, nicht des Ingenieurbüros.
// woodcore:/object p1
