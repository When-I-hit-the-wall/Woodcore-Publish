#import "/000-Typst-Config/commands.typ": *

= Einwirkungen

Berücksichtigte Lasten und Lastfälle (Eigengewicht, Schnee, Wind, Nutzlasten, ...).

// Every load on this page is project-wide: it belongs to no position in particular, so nothing here sits inside a calc-block (docs/domain/positions.md §7-8 -- a load is never linked to a position, not even by a block header).
//
// The cases are chosen here by hand, each at the level this report wants it -- the engineer's decision (periodic audit 260916, AUD-7-205). Each load is a *domain* whose instances are the cases entered in Woodcore's tabs Vent, Neige and Poids propre (Woodcore-Datei/loads/, docs/domain/calculation-domains.md §3.3): a case saved there is exported at once, and it reaches this page when it is named below. A case not named here is exported and not printed -- `EL+AL-Wand` is one today. Each case is written out by the export into its own file (Permanent-loads/, Variable-loads/), which the engineer edits and which is printed by `#include domain-file(kind, id)`; `#for s in ids("dead-load") { include domain-file("dead-load", s) }` prints them all instead.

== Eigengewicht

=== Velo Unterstand

#include domain-file("dead-load", "EL+AL-Dach_mit_Wasser")
#v(1em)
#include domain-file("dead-load", "EL+AL-Dach_ohne_Wasser")
#v(1em)
#include domain-file("dead-load", "EL+AL-DachRand")

== Nutzlast

Die Dächer des Velo-Unterstands und des Pavillons sind nur für Unterhaltsarbeiten zugänglich und damit nicht begehbare Dächer im Sinne der Norm.

#include domain-file("live-load", "H")

== Schneelast

#include domain-file("snow-load", "SL")

== Windlast

=== Velo Unterstand

#include domain-file("wind-load", "WL-Velo")

=== Fluchttreppe und Gerätehaus

#include domain-file("wind-load", "WL-Fluchttreppe+Geraete")

=== Pavillon

#include domain-file("wind-load", "WL-Pavillon")
