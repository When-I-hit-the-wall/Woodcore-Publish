#import "/commands.typ": *

// woodcore:object heading title
== Anforderungen nach Bauteil
// woodcore:/object title

// woodcore:object doc-table maintenance-table
#doc-table(
  columns: (
    (id: "item", title: [Element]),
    (id: "text", title: [Beschreibung], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Dach], text: [[Abdichtung, zugängliche Entwässerung, für Unterhalt und Schneeräumung begehbares Dach. Im Dimensionierungsfall berücksichtigte Schneehöhe; darüber hinaus Schneeräumung zulasten der Bauherrschaft.]]),
    (item: [Obergeschosse], text: [[…]]),
    (item: [Erdgeschoss], text: [[…]]),
    (item: [Untergeschosse], text: [[…]]),
    (item: [Fassade], text: [[Unabhängig von den tragenden Elementen austauschbar; gewünschtes Material (z. B. Holzverkleidung).]]),
  ),
  caption: [Betriebs- und Unterhaltsanforderungen],
  header: false,
)
// woodcore:/object maintenance-table
