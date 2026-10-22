#import "/commands.typ": *

// woodcore:object heading title
= Signatures
// woodcore:/object title

// woodcore:object table agreement-signatures-block
#figure(
  table(
    columns: (auto, auto, auto, 1fr),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Fonction*], [*Nom*], [*Lieu, date*], [*Signature*]),
    table.hline(stroke: 0.5pt),
    [*Maître de l'ouvrage*], [], [], [],
    [Maître de l'ouvrage], [], [], [#v(1cm)#line(length: 100%, stroke: 0.5pt)],
    [Représentant·e], [], [], [#v(1cm)#line(length: 100%, stroke: 0.5pt)],
    [*Auteur du projet*], [], [], [],
    [Architecte], [], [], [#v(1cm)#line(length: 100%, stroke: 0.5pt)],
    [Ingénieur·e], [], [], [#v(1cm)#line(length: 100%, stroke: 0.5pt)],
    table.hline(stroke: 1pt),
  ),
)
// woodcore:/object agreement-signatures-block
