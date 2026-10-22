#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Lärmbelastung nach LSV
// woodcore:/object title

// woodcore:object table noise-exposure-table
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Nutzungszone], [[…]],
    [Empfindlichkeitsstufe], [[DS …]],
    [Äussere Lärmquellen], [[…]],
    [Immissionsgrenzwerte Tag / Nacht], [[… dB / … dB]],
    table.hline(stroke: 1pt),
  ),
  caption: [Lärmbelastung],
)
// woodcore:/object noise-exposure-table
