#import "/commands.typ": *

// woodcore:object heading title
== Project documents
// woodcore:/object title
// woodcore:shared project-documents

// woodcore:object text p1
The following documents are authoritative for this document, in the status stated.
// woodcore:/object p1

// woodcore:object table project-documents-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (right, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*No.*], [*Category*], [*Document*], [*Status (index, date)*]),
    table.hline(stroke: 0.5pt),
    [1], [Architectural drawings], [[Architect's drawings and 3D model]], [[…]],
    [2], [Geology], [[Geotechnical report (author)]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Project documents],
)
// woodcore:/object project-documents-table
// woodcore:/shared project-documents
