#import "/commands.typ": *

// woodcore:object heading title
== Baustelle und Zufahrt
// woodcore:/object title

// woodcore:object doc-table construction-site-table
#doc-table(
  columns: (
    (id: "item", title: [Element]),
    (id: "text", title: [Beschreibung], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Baustelle und Zufahrt], text: [[Zufahrt zur Baustelle (Strassen, Fahrzeugprofile, Seilbahn, Helikopter …), Installations- und Lagerflächen, Umschlagplätze.]]),
    (item: [Kranstandort], text: [[Erforderlicher Kran, zu bedienender Bereich, Standort festgelegt oder nicht.]]),
    (item: [Lärmemissionen], text: [[Zeitliche oder saisonale Einschränkungen, empfindliche Bereiche (Wildschutzgebiet, Nachbarschaft …).]]),
  ),
  caption: [Baustelle],
  header: false,
)
// woodcore:/object construction-site-table
