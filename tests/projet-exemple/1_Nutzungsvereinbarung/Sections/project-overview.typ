#import "/commands.typ": *

// woodcore:object heading title
== Projekt und Umfeld
// woodcore:/object title

// woodcore:object doc-table project-overview-table
#doc-table(
  columns: (
    (id: "item", title: [Element]),
    (id: "text", title: [Beschreibung], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Umfeld], text: [[Lage, Höhe über Meer, Topographie, Art des Baugrunds, Nachbarbauten, Schutzzonen …]]),
    (item: [Architektonisches Konzept], text: [[Organisation nach Geschossen (Untergeschosse, Erdgeschoss, Obergeschosse), Bauweise (Holz, Beton, Verbund), Bestand oder Neubau, Einpassung in die Umgebung, grosse Öffnungen, Innenausbau, Dach (flach, Photovoltaik …), Zielgruppe, Baustoffe mit geringen CO₂-Emissionen …]]),
    (item: [Projektpläne], text: [[Massgebende Pläne und 3D-Modell der Architektur mit Stand (Index, Datum).]]),
    (item: [Besonderheiten], text: [[Zufahrts- und Transportbeschränkungen, während der Bauarbeiten aufrechtzuerhaltender Betrieb, Umweltauflagen …]]),
  ),
  caption: [Allgemeine Beschreibung],
  header: false,
)
// woodcore:/object project-overview-table
