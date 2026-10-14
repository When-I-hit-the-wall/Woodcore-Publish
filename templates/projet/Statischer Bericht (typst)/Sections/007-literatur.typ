#import "../commands.typ": *

= Literatur

Normen, Literatur und weitere in diesem Bericht referenzierte Dokumente.

// Jede Norm und jedes Dokument, das dieser Bericht zitiert, mit Bezeichnung, vollem Titel,
// Ausgabe und Herausgeber -- in drei Blöcken: Normen, Literatur, weitere Dokumente.
// Woodcore kennt die Normen selbst (calc/norms/norms.json); was dieses Projekt sonst zitiert,
// steht in references.bib daneben. Ein Dokument, das keiner der beiden nennt, wird so
// ausgegeben, wie es zitiert wurde (docs/typst/api-conventions.md §10bis).
//
// ⚠️ `project:` nennt references.bib im Ordner dieses Berichts. Wird die Datei gelöscht,
// muss das Argument hier weg: Typst findet eine Datei, die es nicht gibt, nicht.
#show-bibliography(project: "references.bib")
