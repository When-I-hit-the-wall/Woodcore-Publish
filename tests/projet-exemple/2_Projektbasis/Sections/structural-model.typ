#import "/commands.typ": *

// woodcore:object heading title
== Tragwerks- und Berechnungsmodell
// woodcore:/object title

// woodcore:object doc-table structural-model-table
#doc-table(
  columns: (
    (id: "item", title: [Element]),
    (id: "text", title: [Beschreibung], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Software und Berechnungsmodell], text: [[Berechnungsprogramm, Modelltyp (Stab-, Finite-Elemente-Modell), Detaillierungsgrad.]]),
    (item: [Statisches System und Lagerung], text: [[…]]),
    (item: [Angenommene Steifigkeiten], text: [[Steifigkeit von Baugrund, Verbindungen (Verschiebungsmoduln), Verbundbauteilen, Rissbildung.]]),
    (item: [Effekte 2. Ordnung], text: [[…]]),
    (item: [Interaktion Baugrund-Tragwerk], text: [[…]]),
    (item: [Holzfeuchte und Lasteinwirkungsdauer (Holz)], text: [[…]]),
    (item: [Plausibilitätskontrolle], text: [[Die Ergebnisse der Tragwerksanalyse werden auf ihre Plausibilität geprüft (SIA 260, Ziffer 3.1.4).]]),
  ),
  caption: [Modellannahmen],
  header: false,
)
// woodcore:/object structural-model-table
