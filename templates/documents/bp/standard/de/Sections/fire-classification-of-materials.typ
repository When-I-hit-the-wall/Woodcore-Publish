#import "/commands.typ": *

// woodcore:object heading title
== Verwendung von Baustoffen
// woodcore:/object title

// woodcore:object doc-table fire-materials-table
#doc-table(
  columns: (
    (id: "category", title: [Kategorie]),
    (id: "element", title: [Bauteil]),
    (id: "basis", title: [Grundlage]),
    (id: "requirement", title: [Anforderung]),
    (id: "execution", title: [Ausführung / Werte]),
  ),
  hidden: (),
  rows: (
    (category: [Gebäudehülle], element: [[Aussenwandbekleidung]], basis: [[VKF 14-15]], requirement: [[RF3 (cr)]], execution: [[…]]),
    (category: [Innenausbau: vertikale Fluchtwege], element: [[Wand- und Deckenbekleidungen]], basis: [[VKF 14-15]], requirement: [[RF1]], execution: [[…]]),
  ),
  caption: [Verwendung von Baustoffen],
)
// woodcore:/object fire-materials-table
