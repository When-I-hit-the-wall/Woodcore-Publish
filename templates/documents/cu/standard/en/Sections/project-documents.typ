#import "/commands.typ": *

// woodcore:object heading title
== Project documents
// woodcore:/object title
// woodcore:shared project-documents

// woodcore:object text p1
The following documents are authoritative for this document, in the status stated.
// woodcore:/object p1

// woodcore:object doc-table project-documents-table
#doc-table(
  columns: (
    (id: "no", title: [No.], kind: "number"),
    (id: "category", title: [Category]),
    (id: "document", title: [Document]),
    (id: "status", title: [Status (index, date)]),
  ),
  hidden: (),
  rows: (
    (no: 1, category: [Architectural drawings], document: [[Architect's drawings and 3D model]], status: [[…]]),
    (no: 2, category: [Geology], document: [[Geotechnical report (author)]], status: [[…]]),
  ),
  caption: [Project documents],
)
// woodcore:/object project-documents-table
// woodcore:/shared project-documents
