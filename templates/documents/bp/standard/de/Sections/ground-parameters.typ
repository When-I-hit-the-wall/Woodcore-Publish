#import "/commands.typ": *

// woodcore:object heading title
== Baugrundkennwerte
// woodcore:/object title

// woodcore:object text p1
Die Baugrundkennwerte sind im geotechnischen Bericht [Verfasser, Datum] ersichtlich. Für die Bemessung werden folgende charakteristische Werte angenommen (vorsichtige Erwartungswerte nach SIA 260, Ziffer 3.3.3.5 und SIA 267):
// woodcore:/object p1

// woodcore:object doc-table ground-parameters-table
#doc-table(
  columns: (
    (id: "layer", title: [Schicht]),
    (id: "gamma", title: [Raumlast $gamma$], unit: "kN/m³", kind: "number"),
    (id: "phi", title: [Reibungswinkel $phi'$], unit: "°", kind: "number"),
    (id: "c", title: [Kohäsion $c'$], unit: "kPa", kind: "number"),
    (id: "Es", title: [Steifemodul $E_s$], unit: "MN/m²", kind: "number"),
    (id: "remark", title: [Bemerkung]),
  ),
  hidden: ("remark",),
  rows: (
    (layer: [[…]], gamma: [[…]], phi: [[…]], c: [[…]], Es: [[…]], remark: []),
  ),
  caption: [Charakteristische Baugrundkennwerte],
)
// woodcore:/object ground-parameters-table
