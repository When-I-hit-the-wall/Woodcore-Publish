#import "/commands.typ": *

// woodcore:object heading title
== Vorinvestition Aufstockung und spätere Erweiterung
// woodcore:/object title

// woodcore:object text p1
[Falls eine Aufstockung oder Erweiterung vorgesehen ist: die Option, die betroffenen Geschosse und das im Tragwerk und in den Installationen bereits Vorinvestierte beschreiben. Die Lasten der Erweiterung (Eigengewicht, Auflasten, Nutzlasten) sind nachfolgend definiert; sie müssen in der weiteren Projektierung von der Tragwerksplanung freigegeben werden.]
// woodcore:/object p1

// woodcore:object doc-table extension-loads
#doc-table(
  columns: (
    (id: "storey", title: [Geschoss]),
    (id: "buildup", title: [Nutzung / Aufbau]),
    (id: "dead", title: [Auflast], unit: "kN/m²", kind: "number"),
    (id: "live", title: [Nutzlast], unit: "kN/m²", kind: "number"),
  ),
  hidden: (),
  rows: (
    (storey: [[…]], buildup: [[…]], dead: [[…]], live: [[…]]),
  ),
  caption: [Vorgesehene Lasten der Erweiterung],
)
// woodcore:/object extension-loads
