#import "/commands.typ": *

// woodcore:object heading title
== Maçonnerie
// woodcore:/object title

// woodcore:object doc-table masonry-table
#doc-table(
  columns: (
    (id: "designation", title: [Désignation]),
    (id: "fxd", title: [Résistance à la compression de calcul $f_"xd"$], unit: "N/mm²", kind: "number"),
    (id: "Exd", title: [Module d'élasticité de calcul $E_"xd"$], unit: "N/mm²", kind: "number"),
    (id: "remark", title: [Autres valeurs caractéristiques]),
  ),
  hidden: ("remark",),
  rows: (
    (designation: [[…]], fxd: [[…]], Exd: [[…]], remark: []),
  ),
  caption: [Maçonnerie (SIA 266)],
)
// woodcore:/object masonry-table
