#import "/commands.typ": *

// woodcore:object heading title
== Verformungsgrenzen (Durchbiegungen)
// woodcore:/object title
// woodcore:shared deformation-limits

// woodcore:object text p1
Die Durchbiegungen werden auf die Richtwerte der Norm SIA 260, Anhang A, Tabelle 3 begrenzt; sie sind nach den Normen SIA 262 bis 266 zu bestimmen. Abweichende Grenzwerte können in Abstimmung auf die Nutzungsanforderungen vereinbart werden, insbesondere für sekundäre Bauteile; sie werden in der Projektbasis festgelegt. [Die Bauherrschaft stellt keine erhöhten Anforderungen gegenüber der Norm: ja / nein.]
// woodcore:/object p1

// woodcore:object table deformation-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, center, left),
    table.hline(stroke: 1pt),
    table.header([*Bauteil*], [*Kriterium*], [*Grenzwert*], [*Lastfall (SIA 260, Tab. 3)*]),
    table.hline(stroke: 0.5pt),
    [Decken und Balken], [Einbauten mit sprödem Verhalten], [$w <= l \/ 500$], [selten (20)],
    [Decken und Balken], [Einbauten mit duktilem Verhalten], [$w <= l \/ 350$], [häufig (21)],
    [Decken und Balken], [Nutzung, Betrieb und Komfort (Durchbiegung infolge veränderlicher Einwirkungen)], [$w <= l \/ 350$], [häufig (21)],
    [Decken und Balken], [Aussehen (nach Abzug einer allfälligen Überhöhung)], [$w <= l \/ 300$], [quasi-ständig (22)],
    table.hline(stroke: 1pt),
  ),
  caption: [Zulässige Durchbiegungen],
)
// woodcore:/object deformation-table

// woodcore:object text p2
Durchbiegung infolge der Einwirkungen und Langzeitwirkungen nach dem Einbau aller sekundären Bauteile und der technischen Ausrüstung. Reagieren Einbauten besonders empfindlich auf Verformungen des Tragwerks, sind neben oder anstelle von bemessungstechnischen vor allem auch konstruktive Massnahmen gegen Beschädigungen vorzusehen.
// woodcore:/object p2
// woodcore:/shared deformation-limits
