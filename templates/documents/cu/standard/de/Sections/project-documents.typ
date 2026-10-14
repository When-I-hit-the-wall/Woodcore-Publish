#import "/commands.typ": *

// woodcore:object heading title
== Projektspezifische Unterlagen
// woodcore:/object title
// woodcore:shared project-documents

// woodcore:object text p1
Die folgenden Unterlagen sind für das vorliegende Dokument in dem angegebenen Stand massgebend.
// woodcore:/object p1

// woodcore:object doc-table project-documents-table
#doc-table(
  columns: (
    (id: "no", title: [Nr.], kind: "number"),
    (id: "category", title: [Kategorie]),
    (id: "document", title: [Dokument]),
    (id: "status", title: [Stand (Index, Datum)]),
  ),
  hidden: (),
  rows: (
    (no: 1, category: [Architekturpläne], document: [[Pläne und 3D-Modell der Architektur]], status: [[…]]),
    (no: 2, category: [Geologie], document: [[Geotechnischer Bericht (Verfasser)]], status: [[…]]),
  ),
  caption: [Projektspezifische Unterlagen],
)
// woodcore:/object project-documents-table
// woodcore:/shared project-documents
