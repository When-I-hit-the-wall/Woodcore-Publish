#import "/commands.typ": *

// woodcore:object heading title
== Exposition au bruit selon l'OPB
// woodcore:/object title

// woodcore:object doc-table noise-exposure-table
#doc-table(
  columns: (
    (id: "item", title: [Élément]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Zone d'affectation], text: [[…]]),
    (item: [Degré de sensibilité], text: [[DS …]]),
    (item: [Sources de bruit extérieures], text: [[…]]),
    (item: [Valeurs limites d'immission jour / nuit], text: [[… dB / … dB]]),
  ),
  caption: [Exposition au bruit],
  header: false,
)
// woodcore:/object noise-exposure-table
