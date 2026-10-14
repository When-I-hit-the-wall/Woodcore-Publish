#import "/commands.typ": *

// woodcore:object heading title
== Wichtigste Abmessungen
// woodcore:/object title

// woodcore:object text p1
Die wichtigsten Abmessungen der tragenden Bauteile sind in den Tragkonzeptplänen festgehalten und basieren auf der statischen Dimensionierung des Gebäudes.
// woodcore:/object p1

// woodcore:object doc-table main-dimensions-table
#doc-table(
  columns: (
    (id: "position", title: [Position]),
    (id: "member", title: [Bauteil]),
    (id: "material", title: [Material / Festigkeitsklasse]),
    (id: "section", title: [Abmessungen]),
    (id: "remark", title: [Bemerkung]),
  ),
  hidden: ("remark",),
  rows: (
    (position: [[…]], member: [[Hauptträger]], material: [[…]], section: [[…]], remark: []),
    (position: [[…]], member: [[Stütze]], material: [[…]], section: [[…]], remark: []),
  ),
  caption: [Wichtigste tragende Bauteile],
)
// woodcore:/object main-dimensions-table
