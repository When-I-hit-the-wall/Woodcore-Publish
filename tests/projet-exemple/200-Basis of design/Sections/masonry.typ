#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Mauerwerk
// woodcore:/object title

// woodcore:object table masonry-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, right, right),
    table.hline(stroke: 1pt),
    table.header([*Bezeichnung*], [*Bemessungswert der Druckfestigkeit $f_"xd"$*], [*Bemessungswert des Elastizitätsmoduls $E_"xd"$*]),  // woodcore:hidden 4=[Weitere Kennwerte]
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]],  // woodcore:hidden 4=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Mauerwerk (SIA 266)],
)
// woodcore:/object masonry-table
