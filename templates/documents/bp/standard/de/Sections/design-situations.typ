#import "/commands.typ": *

// woodcore:object heading title
== Bemessungssituationen
// woodcore:/object title

// woodcore:object text p1
Die betrachteten Bemessungssituationen schliessen alle vorhersehbaren Bedingungen ein, die während der Ausführung und Nutzung auftreten können (SIA 260, Ziffer 4.2.1). Sie werden in andauernde, vorübergehende und aussergewöhnliche Situationen eingeteilt; Bauzustände können als andauernde oder vorübergehende Bemessungssituationen betrachtet werden (Ziffern 4.2.2 und 4.2.3).
// woodcore:/object p1

// woodcore:object doc-table design-situations-table
#doc-table(
  columns: (
    (id: "situation", title: [Situation]),
    (id: "description", title: [Beschreibung]),
    (id: "governing", title: [Massgebende Lastfälle]),
  ),
  hidden: (),
  rows: (
    (situation: [Andauernd], description: [[Normale Nutzung]], governing: [[…]]),
    (situation: [Vorübergehend], description: [[Bauzustände]], governing: [[…]]),
    (situation: [Aussergewöhnlich], description: [[Erdbeben, Brand, Anprall]], governing: [[…]]),
  ),
  caption: [Bemessungssituationen],
)
// woodcore:/object design-situations-table
