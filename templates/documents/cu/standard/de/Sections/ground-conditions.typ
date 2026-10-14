#import "/commands.typ": *

// woodcore:object heading title
== Baugrund
// woodcore:/object title
// woodcore:shared ground-conditions

// woodcore:object text p1
[Art des Baugrunds, Schichtaufbau, hydrogeologische Verhältnisse (Grundwasser, Hang- und Schichtwasser) und Quelle dieser Angaben: geotechnischer Bericht (Verfasser, Datum). Sind die Untersuchungen nicht abgeschlossen, die vor der Projektierung noch nötigen Abklärungen angeben.]
// woodcore:/object p1

// woodcore:object doc-table ground-layers
#doc-table(
  columns: (
    (id: "layer", title: [Schicht]),
    (id: "description", title: [Beschreibung]),
    (id: "depth", title: [Tiefe / Mächtigkeit], unit: "m", kind: "number"),
  ),
  hidden: (),
  rows: (
    (layer: [[…]], description: [[…]], depth: [[…]]),
  ),
  caption: [Baugrundschichten],
)
// woodcore:/object ground-layers

// woodcore:object doc-table design-water-levels
#doc-table(
  columns: (
    (id: "level", title: [Wasserstand]),
    (id: "elevation", title: [Kote (m ü. M.)], unit: "m", kind: "number"),
    (id: "remark", title: [Bemerkung]),
  ),
  hidden: ("remark",),
  rows: (
    (level: [Hochwasser (HW)], elevation: [[…]], remark: []),
    (level: [Mittelwasser (MW)], elevation: [[…]], remark: []),
  ),
  caption: [Massgebende Wasserstände],
)
// woodcore:/object design-water-levels

// woodcore:object doc-image ground-profile
#doc-image(
  file: none,
  caption: [Geologisches Profil / Auszug aus dem geotechnischen Bericht],
  placeholder: [[Abbildung mit Legende und Quelle]],
)
// woodcore:/object ground-profile
// woodcore:/shared ground-conditions
