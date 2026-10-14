#import "/commands.typ": *

// woodcore:object heading title
== Logistik und Transport
// woodcore:/object title
// woodcore:shared transport-dimensions

// woodcore:object text p1
[Vorgesehene Transportmittel (Lastwagen, Kran, Seilbahn, Helikopter …), Anforderungen der Bauherrschaft, Abmessungs- und Gewichtsbeschränkungen der vorgefertigten Elemente, Lager- und Umschlagsflächen. Haupttransportmittel und zulässige Ausnahmen.]
// woodcore:/object p1

// woodcore:object doc-table transport-table
#doc-table(
  columns: (
    (id: "transport", title: [Transportmittel]),
    (id: "length", title: [Max. Länge], unit: "mm", kind: "number"),
    (id: "width", title: [Max. Breite], unit: "mm", kind: "number"),
    (id: "height", title: [Max. Höhe], unit: "mm", kind: "number"),
    (id: "hung", title: [Max. Hängelast], unit: "kg", kind: "number"),
    (id: "distributed", title: [Max. verteilte Last], unit: "kg", kind: "number"),
  ),
  hidden: (),
  rows: (
    (transport: [[…]], length: [[…]], width: [[…]], height: [[…]], hung: [[…]], distributed: [[…]]),
  ),
  caption: [Maximale Abmessungen der transportierten Elemente],
)
// woodcore:/object transport-table
// woodcore:/shared transport-dimensions
