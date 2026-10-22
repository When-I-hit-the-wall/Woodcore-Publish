#import "/commands.typ": *

// woodcore:object heading title
== Provision for a future extension
// woodcore:/object title

// woodcore:object text p1
[If a further storey or an extension is envisaged: describe the option, the storeys concerned and what is already provided for in the structure and the services. The loads of the extension (self-weight, superimposed dead loads, live loads) are defined below; they must be approved by the engineer in the further design.]
// woodcore:/object p1

// woodcore:object table extension-loads
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, right, right),
    table.hline(stroke: 1pt),
    table.header([*Storey*], [*Use / build-up*], [*Superimposed dead load*], [*Live load*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Loads provided for the extension],
)
// woodcore:/object extension-loads
