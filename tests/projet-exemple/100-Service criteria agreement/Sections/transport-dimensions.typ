#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Logistik und Transport
// woodcore:/object title
// woodcore:shared transport-dimensions

// woodcore:object text p1
[Vorgesehene Transportmittel (Lastwagen, Kran, Seilbahn, Helikopter …), Anforderungen der Bauherrschaft, Abmessungs- und Gewichtsbeschränkungen der vorgefertigten Elemente, Lager- und Umschlagsflächen. Haupttransportmittel und zulässige Ausnahmen.]
// woodcore:/object p1

// woodcore:object table transport-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, right, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Transportmittel*], [*Max. Länge*], [*Max. Breite*], [*Max. Höhe*], [*Max. Hängelast*], [*Max. verteilte Last*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]], [[…]], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Maximale Abmessungen der transportierten Elemente],
)
// woodcore:/object transport-table
// woodcore:/shared transport-dimensions
