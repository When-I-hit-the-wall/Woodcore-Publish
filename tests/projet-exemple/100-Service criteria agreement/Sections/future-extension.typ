#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Vorinvestition Aufstockung und spätere Erweiterung
// woodcore:/object title

// woodcore:object text p1
[Falls eine Aufstockung oder Erweiterung vorgesehen ist: die Option, die betroffenen Geschosse und das im Tragwerk und in den Installationen bereits Vorinvestierte beschreiben. Die Lasten der Erweiterung (Eigengewicht, Auflasten, Nutzlasten) sind nachfolgend definiert; sie müssen in der weiteren Projektierung von der Tragwerksplanung freigegeben werden.]
// woodcore:/object p1

// woodcore:object table extension-loads
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, right, right),
    table.hline(stroke: 1pt),
    table.header([*Geschoss*], [*Nutzung / Aufbau*], [*Auflast*], [*Nutzlast*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Vorgesehene Lasten der Erweiterung],
)
// woodcore:/object extension-loads
