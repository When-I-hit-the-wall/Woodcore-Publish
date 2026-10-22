#import "/commands.typ": *

// woodcore:object heading title
= Unterschriften
// woodcore:/object title

// woodcore:object table agreement-signatures-block
#figure(
  table(
    columns: (auto, auto, auto, 1fr),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Funktion*], [*Name*], [*Ort, Datum*], [*Unterschrift*]),
    table.hline(stroke: 0.5pt),
    [*Bauherrschaft*], [], [], [],
    [Bauherrschaft], [], [], [#v(1cm)#line(length: 100%, stroke: 0.5pt)],
    [Vertretung], [], [], [#v(1cm)#line(length: 100%, stroke: 0.5pt)],
    [*Projektverfassende*], [], [], [],
    [Architekt:in], [], [], [#v(1cm)#line(length: 100%, stroke: 0.5pt)],
    [Ingenieur:in], [], [], [#v(1cm)#line(length: 100%, stroke: 0.5pt)],
    table.hline(stroke: 1pt),
  ),
)
// woodcore:/object agreement-signatures-block
