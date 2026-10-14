#import "/commands.typ": *

// woodcore:object heading title
=== Wind
// woodcore:/object title

// woodcore:object text p1
Die Windeinwirkungen werden nach der Norm SIA 261, Kapitel 6, ermittelt. Der Staudruck beträgt:
// woodcore:/object p1

// woodcore:object text p2
$ q_p = c_h dot q_(p 0) $
// woodcore:/object p2

// woodcore:object text p3
wobei der Referenzwert $q_"p0"$ dem Anhang E, die Geländekategorie und der Profilbeiwert $c_h$ der Ziffer 6.2.1 (Tabelle 4) entnommen werden. Die Druck- und Kraftbeiwerte sind jene des Anhangs C.
// woodcore:/object p3

// woodcore:object doc-table wind-parameters
#doc-table(
  columns: (
    (id: "parameter", title: [Parameter], kind: "wide"),
    (id: "symbol", title: [Symbol], kind: "math"),
    (id: "value", title: [Wert], kind: "number"),
    (id: "unit", title: [Einheit]),
  ),
  hidden: (),
  rows: (
    (parameter: [Geländekategorie], symbol: [], value: [[…]], unit: []),
    (parameter: [Bezugshöhe über Boden], symbol: [$z$], value: [[…]], unit: [m]),
    (parameter: [Profilbeiwert], symbol: [$c_h$], value: [[…]], unit: []),
    (parameter: [Referenzwert des Staudrucks], symbol: [$q_(p 0)$], value: [[…]], unit: [kN/m²]),
    (parameter: [Staudruck], symbol: [$q_p$], value: [[…]], unit: [kN/m²]),
  ),
  caption: [Windparameter],
)
// woodcore:/object wind-parameters
