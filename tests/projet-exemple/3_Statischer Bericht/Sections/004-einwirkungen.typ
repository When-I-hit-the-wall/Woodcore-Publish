#import "/commands.typ": *

= Einwirkungen

Berücksichtigte Lasten und Lastfälle (Eigengewicht, Schnee, Wind, Nutzlasten, ...).

// Every load on this page is project-wide: it belongs to no position in particular, so nothing here sits inside a calc-block (docs/domain/positions.md §7-8 -- a load is never linked to a position, not even by a block header).
//
// The cases are chosen here by hand, each at the level this report wants it -- the engineer's decision (periodic audit 260916, AUD-7-205). Each load is a *domain* whose instances are the sheets carrying its prefix, in every workbook of the project folder whose name contains "Belastungsannahmen" (docs/domain/calculation-domains.md §3.3): copying a sheet in Excel exports that case at once, and it reaches this page when it is named below. A sheet not named here is exported and not printed -- `EL+AL-Wand` is one today. `#for s in instance-ids("dead-load") { show-calc("dead-load", s) }` prints them all instead.

== Eigengewicht

=== Velo Unterstand

#show-calc("dead-load", "EL+AL-Dach mit Wasser", level:3)
#v(1em)
#show-calc("dead-load", "EL+AL-Dach ohne Wasser", level:1)
#v(1em)
#show-calc("dead-load", "EL+AL-DachRand", level:2)

== Nutzlast

Die Dächer des Velo-Unterstands und des Pavillons sind nur für Unterhaltsarbeiten zugänglich und damit nicht begehbare Dächer im Sinne der Norm.

#show-live-load("H", level: 2)

== Schneelast

#show-calc("snow-load", "SL", level: 1, title: none)

== Windlast

=== Velo Unterstand

#show-calc("wind-load", "WL-Velo", title: "WL Velo Unterstand", level:2)

=== Fluchttreppe und Gerätehaus

#show-calc("wind-load", "WL-Fluchttreppe+Geräte", title: "WL Fluchttreppe + Geräte", level:1)

=== Pavillon

#show-calc("wind-load", "WL-Pavillon", title: "WL Pavillon", level:1)
