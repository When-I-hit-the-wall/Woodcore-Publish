#import "/commands.typ": *

// woodcore:object heading title
== Projektspezifische Unterlagen
// woodcore:/object title
// woodcore:shared project-documents

// woodcore:object text p1
Die folgenden Unterlagen sind für das vorliegende Dokument in dem angegebenen Stand massgebend.
// woodcore:/object p1

// woodcore:object table project-documents-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (right, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Nr.*], [*Kategorie*], [*Dokument*], [*Stand (Index, Datum)*]),
    table.hline(stroke: 0.5pt),
    [1], [Architekturpläne], [[Pläne und 3D-Modell der Architektur]], [[…]],
    [2], [Geologie], [[Geotechnischer Bericht (Verfasser)]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Projektspezifische Unterlagen],
)
// woodcore:/object project-documents-table
// woodcore:/shared project-documents
