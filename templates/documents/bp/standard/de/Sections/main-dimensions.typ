#import "/commands.typ": *

// woodcore:object heading title
== Wichtigste Abmessungen
// woodcore:/object title

// woodcore:object text p1
Die wichtigsten Abmessungen der tragenden Bauteile sind in den Tragkonzeptplänen festgehalten und basieren auf der statischen Dimensionierung des Gebäudes.
// woodcore:/object p1

// woodcore:object table main-dimensions-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Position*], [*Bauteil*], [*Material / Festigkeitsklasse*], [*Abmessungen*]),  // woodcore:hidden 5=[Bemerkung]
    table.hline(stroke: 0.5pt),
    [[…]], [[Hauptträger]], [[…]], [[…]],  // woodcore:hidden 5=[]
    [[…]], [[Stütze]], [[…]], [[…]],  // woodcore:hidden 5=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Wichtigste tragende Bauteile],
)
// woodcore:/object main-dimensions-table
