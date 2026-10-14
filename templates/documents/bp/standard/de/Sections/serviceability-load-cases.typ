#import "/commands.typ": *

// woodcore:object heading title
== Lastfälle: Gebrauchstauglichkeit
// woodcore:/object title

// woodcore:object text p1
Für die Gebrauchstauglichkeit wird $E_d$ im Allgemeinen mit $γ_F$ = $γ_m$ = 1.0 ermittelt (SIA 260, Ziffer 4.4.4.3). Es werden drei Typen von Lastfällen unterschieden (Ziffer 4.4.4.4):
// woodcore:/object p1

// woodcore:object text p2
- seltene Lastfälle: veränderliche Leiteinwirkung mit ihrem charakteristischen Wert, Begleiteinwirkungen mit ψ₀;
- häufige Lastfälle: veränderliche Leiteinwirkung mit ψ₁, Begleiteinwirkungen mit ψ₂;
- quasi-ständige Lastfälle: alle veränderlichen Einwirkungen mit ψ₂.
// woodcore:/object p2

// woodcore:object doc-table sls-load-cases-table
#doc-table(
  columns: (
    (id: "element", title: [Bauteil]),
    (id: "case", title: [Lastfall]),
    (id: "permanent", title: [Eigengewicht und ständige Lasten], kind: "number"),
    (id: "live", title: [Nutzlast [Kategorie]], kind: "number"),
    (id: "snow", title: [Schnee], kind: "number"),
    (id: "wind", title: [Wind], kind: "math"),
  ),
  hidden: (),
  rows: (
    (element: [[Dach]], case: [CC 1], permanent: 1.0, live: [–], snow: 1.0, wind: [$ψ_0$]),
    (element: [[Regelgeschoss]], case: [CC 2], permanent: 1.0, live: 1.0, snow: [–], wind: [$ψ_0$]),
  ),
  caption: [Lastfälle: Gebrauchstauglichkeit],
)
// woodcore:/object sls-load-cases-table
