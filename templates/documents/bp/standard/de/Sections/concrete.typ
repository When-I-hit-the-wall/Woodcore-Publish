#import "/commands.typ": *

// woodcore:object heading title
== Beton
// woodcore:/object title

// woodcore:object doc-table concrete-table
#doc-table(
  columns: (
    (id: "member", title: [Bauteil]),
    (id: "class", title: [Festigkeitsklasse]),
    (id: "fck", title: [Charakteristische Festigkeit $f_"ck"$], unit: "N/mm²", kind: "number"),
    (id: "fcd", title: [Bemessungswert der Festigkeit $f_"cd"$], unit: "N/mm²", kind: "number"),
    (id: "taucd", title: [Bemessungswert der Schubspannung $tau_"cd"$], unit: "N/mm²", kind: "number"),
    (id: "Ecm", title: [Mittlerer Elastizitätsmodul $E_"cm"$], unit: "N/mm²", kind: "number"),
    (id: "gamma", title: [Raumlast $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: ("Ecm",),
  rows: (
    (member: [[Bauteil]], class: [C25/30], fck: 25, fcd: [[…]], taucd: [[…]], Ecm: [[…]], gamma: 25),
    (member: [[Bauteil]], class: [C30/37], fck: 30, fcd: [[…]], taucd: [[…]], Ecm: [[…]], gamma: 25),
  ),
  caption: [Stahlbeton (SIA 262)],
  notes: (
    [Bemessungswerte nach der Norm SIA 262:2025.],
    [Die Anforderungen an die Dauerhaftigkeit (Expositionsklassen) sind im Abschnitt «Dauerhaftigkeit» festgehalten.],
  ),
)
// woodcore:/object concrete-table
