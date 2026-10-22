#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Tragwerks- und Berechnungsmodell
// woodcore:/object title

// woodcore:object table structural-model-table
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Software und Berechnungsmodell], [[Berechnungsprogramm, Modelltyp (Stab-, Finite-Elemente-Modell), Detaillierungsgrad.]],
    [Statisches System und Lagerung], [[…]],
    [Angenommene Steifigkeiten], [[Steifigkeit von Baugrund, Verbindungen (Verschiebungsmoduln), Verbundbauteilen, Rissbildung.]],
    [Effekte 2. Ordnung], [[…]],
    [Interaktion Baugrund-Tragwerk], [[…]],
    [Holzfeuchte und Lasteinwirkungsdauer (Holz)], [[…]],
    [Plausibilitätskontrolle], [[Die Ergebnisse der Tragwerksanalyse werden auf ihre Plausibilität geprüft (SIA 260, Ziffer 3.1.4).]],
    table.hline(stroke: 1pt),
  ),
  caption: [Modellannahmen],
)
// woodcore:/object structural-model-table
