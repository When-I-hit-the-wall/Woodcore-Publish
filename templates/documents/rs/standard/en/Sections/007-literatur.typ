#import "/commands.typ": *

// woodcore:object heading title
= References
// woodcore:/object title

// woodcore:object text p1
Norms, literature and other documents cited in this report.
// woodcore:/object p1

// Every norm and document this report cites, with its designation, full title, edition and publisher -- in three blocks: the norms, the literature, the other documents. Woodcore knows the norms itself (calc/norms/norms.json); what else this project cites is in references.bib at the top of the project. A document neither names is printed as it was cited (docs/typst/citations.md §10).
//
// `project:` names references.bib from the project's folder, the Typst root. If the file is deleted, the argument has to go too: Typst cannot find a file that is not there.
#show-bibliography(project: "references.bib")
