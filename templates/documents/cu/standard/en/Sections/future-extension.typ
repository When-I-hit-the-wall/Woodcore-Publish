#import "/commands.typ": *

// woodcore:object heading title
== Provision for a future extension
// woodcore:/object title

// woodcore:object text p1
[If a further storey or an extension is envisaged: describe the option, the storeys concerned and what is already provided for in the structure and the services. The loads of the extension (self-weight, superimposed dead loads, live loads) are defined below; they must be approved by the engineer in the further design.]
// woodcore:/object p1

// woodcore:object doc-table extension-loads
#doc-table(
  columns: (
    (id: "storey", title: [Storey]),
    (id: "buildup", title: [Use / build-up]),
    (id: "dead", title: [Superimposed dead load], unit: "kN/m²", kind: "number"),
    (id: "live", title: [Live load], unit: "kN/m²", kind: "number"),
  ),
  hidden: (),
  rows: (
    (storey: [[…]], buildup: [[…]], dead: [[…]], live: [[…]]),
  ),
  caption: [Loads provided for the extension],
)
// woodcore:/object extension-loads
