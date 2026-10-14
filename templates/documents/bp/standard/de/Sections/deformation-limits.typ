#import "/commands.typ": *

// woodcore:object heading title
== Verformungsgrenzen (Durchbiegungen)
// woodcore:/object title
// woodcore:shared deformation-limits

// woodcore:object text p1
Die Durchbiegungen werden auf die Richtwerte der Norm SIA 260, Anhang A, Tabelle 3 begrenzt; sie sind nach den Normen SIA 262 bis 266 zu bestimmen. Abweichende Grenzwerte können in Abstimmung auf die Nutzungsanforderungen vereinbart werden, insbesondere für sekundäre Bauteile; sie werden in der Projektbasis festgelegt. [Die Bauherrschaft stellt keine erhöhten Anforderungen gegenüber der Norm: ja / nein.]
// woodcore:/object p1

// woodcore:object doc-table deformation-table
#doc-table(
  columns: (
    (id: "element", title: [Bauteil]),
    (id: "criterion", title: [Kriterium]),
    (id: "limit", title: [Grenzwert], kind: "math"),
    (id: "load_case", title: [Lastfall (SIA 260, Tab. 3)]),
  ),
  hidden: (),
  rows: (
    (element: [Decken und Balken], criterion: [Einbauten mit sprödem Verhalten], limit: [$w <= l \/ 500$], load_case: [selten (20)]),
    (element: [Decken und Balken], criterion: [Einbauten mit duktilem Verhalten], limit: [$w <= l \/ 350$], load_case: [häufig (21)]),
    (element: [Decken und Balken], criterion: [Nutzung, Betrieb und Komfort (Durchbiegung infolge veränderlicher Einwirkungen)], limit: [$w <= l \/ 350$], load_case: [häufig (21)]),
    (element: [Decken und Balken], criterion: [Aussehen (nach Abzug einer allfälligen Überhöhung)], limit: [$w <= l \/ 300$], load_case: [quasi-ständig (22)]),
  ),
  caption: [Zulässige Durchbiegungen],
)
// woodcore:/object deformation-table

// woodcore:object text p2
Durchbiegung infolge der Einwirkungen und Langzeitwirkungen nach dem Einbau aller sekundären Bauteile und der technischen Ausrüstung. Reagieren Einbauten besonders empfindlich auf Verformungen des Tragwerks, sind neben oder anstelle von bemessungstechnischen vor allem auch konstruktive Massnahmen gegen Beschädigungen vorzusehen.
// woodcore:/object p2
// woodcore:/shared deformation-limits
