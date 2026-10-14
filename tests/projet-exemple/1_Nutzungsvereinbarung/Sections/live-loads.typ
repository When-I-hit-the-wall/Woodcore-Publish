#import "/commands.typ": *

// woodcore:object heading title
== Nutzlasten
// woodcore:/object title
// woodcore:shared live-loads

// woodcore:object text p1
Die zulässigen Belastungen orientieren sich an der vorgesehenen Nutzung auf dem Boden des jeweiligen Geschosses und sind in der Norm SIA 261, Kapitel 8, Tabelle 8 geregelt. 1 kN/m² entspricht rund 100 kg/m², 10 kN rund einer Tonne.
// woodcore:/object p1

// woodcore:object text p2
Die folgenden Werte sind Höchstwerte: Sie dienen der Bemessung und dürfen während der Nutzungsdauer nicht überschritten werden. [Für vertikale Bauteile mehrgeschossiger Gebäude darf die Nutzlast nach SIA 261, Ziffer 8.3 abgemindert werden: präzisieren.]
// woodcore:/object p2

// woodcore:object live-load-table live-loads-table
#live-load-table(
  columns: (
    (id: "zone"),
    (id: "storey"),
    (id: "use"),
    (id: "category"),
    (id: "q_k"),
    (id: "Q_k"),
  ),
  hidden: (),
  rows: (
    (zone: [[…]], storey: [[…]], use: [[Wohnräume]], category: "A1", q_k: auto, Q_k: auto),
    (zone: [[…]], storey: [[Dach]], use: [[Nur für Unterhaltszwecke begehbar]], category: "H", q_k: auto, Q_k: auto),
  ),
  caption: [Nutzlasten nach Teilbereich und Geschoss],
  notes: (
    [$Q_k$: Aufstandsfläche 50 × 50 mm; $Q_k$ muss im Allgemeinen nicht mit $q_k$ kombiniert werden. Für Flächen mit Lagergestellen oder mit Hebeeinrichtungen befahrene Flächen ist $Q_k$ projektspezifisch festzulegen (SIA 261, Tabelle 8, Fussnote 1).],
    [Kategorien F und G: $Q_k$ und $q_k$ wirken gleichzeitig; zwei Einzellasten $Q_k$/2 im Abstand von 1.8 m auf Aufstandsflächen von 200 × 200 mm (SIA 261, Tabelle 8, Fussnoten 3 und 4).],
    [Kategorie E: die Werte sind projektspezifisch festzulegen (SIA 261, Ziffer 8.2.2) und in der Nutzungsvereinbarung sowie in der Projektbasis festzuhalten.],
    [Begehbare und befahrbare Dächer sind entsprechend ihrer Nutzung als Flächen der Kategorien A bis G zu behandeln; die Kategorie H gilt nur für Dächer mit Zugang nur für Unterhaltsarbeiten (SIA 261, Tabelle 8, Fussnote 5).],
  ),
)
// woodcore:/object live-loads-table

// woodcore:object text p3
Besondere Massnahmen (SIA 261, Ziffer 8.4): Nutzflächen der Kategorie E werden in den betreffenden Räumen mit dem hier vereinbarten Höchstwert der Nutzlast beschriftet; die Zugänge zu Nutzflächen der Kategorie F werden durch bauliche Massnahmen eingeschränkt; Nutzflächen der Kategorien F und G werden entsprechend beschriftet und signalisiert. [Befahrbare Flächen: Geschwindigkeitsbegrenzung und Signalisation bei der Einfahrt.]
// woodcore:/object p3
// woodcore:/shared live-loads
