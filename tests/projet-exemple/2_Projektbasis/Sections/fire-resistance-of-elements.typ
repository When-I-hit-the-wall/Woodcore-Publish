#import "/commands.typ": *

// woodcore:object heading title
== Feuerwiderstand der Bauteile
// woodcore:/object title

// woodcore:object doc-table fire-resistance-table
#doc-table(
  columns: (
    (id: "category", title: [Kategorie]),
    (id: "zone", title: [Bereich / Bauteil]),
    (id: "basis", title: [Grundlage]),
    (id: "requirement", title: [Anforderung]),
    (id: "execution", title: [Ausführung / Werte]),
  ),
  hidden: (),
  rows: (
    (category: [Tragwerk], zone: [[Untergeschoss – Erdgeschoss]], basis: [VKF 15-15], requirement: [R 60], execution: [[…]]),
    (category: [Brandabschnitte], zone: [[Decke über Erdgeschoss]], basis: [VKF 15-15], requirement: [REI 60], execution: [[…]]),
  ),
  caption: [Feuerwiderstand der Bauteile],
)
// woodcore:/object fire-resistance-table
