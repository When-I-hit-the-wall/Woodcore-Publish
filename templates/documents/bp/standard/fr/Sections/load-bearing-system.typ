#import "/commands.typ": *

// woodcore:object heading title
== Système porteur
// woodcore:/object title

// woodcore:object doc-table structural-system-table
#doc-table(
  columns: (
    (id: "item", title: [Élément]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Système porteur vertical], text: [[Poteaux, murs, noyaux, fondations …]]),
    (item: [Planchers et toitures], text: [[Type de plancher par niveau, portée principale, mode de fonctionnement (une ou deux directions), rôle du bois dans la section mixte …]]),
    (item: [Murs et poteaux], text: [[Matériau et disposition par niveau, sections principales …]]),
    (item: [Reprises de charges], text: [[Éléments de transfert : poutres, dalles, treillis ; niveaux concernés …]]),
    (item: [Cheminement des charges], text: [[…]]),
    (item: [Variantes étudiées], text: [[Renvoi aux études de variantes le cas échéant.]]),
  ),
  caption: [Système porteur],
  header: false,
)
// woodcore:/object structural-system-table
