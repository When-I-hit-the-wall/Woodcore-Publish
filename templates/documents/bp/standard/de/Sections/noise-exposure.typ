#import "/commands.typ": *

// woodcore:object heading title
== Lärmbelastung nach LSV
// woodcore:/object title

// woodcore:object doc-table noise-exposure-table
#doc-table(
  columns: (
    (id: "item", title: [Element]),
    (id: "text", title: [Beschreibung], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Nutzungszone], text: [[…]]),
    (item: [Empfindlichkeitsstufe], text: [[DS …]]),
    (item: [Äussere Lärmquellen], text: [[…]]),
    (item: [Immissionsgrenzwerte Tag / Nacht], text: [[… dB / … dB]]),
  ),
  caption: [Lärmbelastung],
  header: false,
)
// woodcore:/object noise-exposure-table
