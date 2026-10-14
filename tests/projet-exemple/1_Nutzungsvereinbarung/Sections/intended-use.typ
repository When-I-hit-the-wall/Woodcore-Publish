#import "/commands.typ": *

// woodcore:object heading title
== Geplante Nutzung
// woodcore:/object title

// woodcore:object doc-table intended-use-table
#doc-table(
  columns: (
    (id: "item", title: [Element]),
    (id: "text", title: [Beschreibung], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Nutzung], text: [[Vorgesehene Nutzungen (Wohnen, Büro, Schule, Verkauf, Restaurant, Mehrzweckraum …).]]),
    (item: [Nutzlasten], text: [Die Nutzlasten werden nach Nutzungskategorie gemäss der Norm SIA 261 festgelegt (siehe Abschnitt «Nutzlasten»).]),
    (item: [Lichtraumprofile], text: [[Gemäss den Vorprojektplänen und dem 3D-Modell der Architektur.]]),
  ),
  caption: [Geplante Nutzung],
  header: false,
)
// woodcore:/object intended-use-table
