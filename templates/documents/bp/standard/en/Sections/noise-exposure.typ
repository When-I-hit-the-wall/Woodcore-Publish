#import "/commands.typ": *

// woodcore:object heading title
== Noise exposure in accordance with the LSV / OPB
// woodcore:/object title

// woodcore:object doc-table noise-exposure-table
#doc-table(
  columns: (
    (id: "item", title: [Item]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Land-use zone], text: [[…]]),
    (item: [Sensitivity level], text: [[DS …]]),
    (item: [External noise sources], text: [[…]]),
    (item: [Immission limit values day / night], text: [[… dB / … dB]]),
  ),
  caption: [Noise exposure],
  header: false,
)
// woodcore:/object noise-exposure-table
