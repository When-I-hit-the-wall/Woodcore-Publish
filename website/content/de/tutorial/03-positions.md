# Die Positionen beschreiben

Eine **Position** ist ein Bauteil des Tragwerks — ein Träger, eine Stütze, eine Platte — so, wie der Positionsplan es nummeriert. Die Positionen werden im Register **Positionen** von Woodcore erfasst, eine Zeile pro Bauteil; sie werden in `Woodcore-Datei/positions.json` gespeichert.

> [!note]
> Ein älteres Projekt mit einer `Positionen.xlsx`: Beim ersten Öffnen importiert Woodcore die Arbeitsmappe einmal und verschiebt sie dann nach `_Archiv/` — sie wird nie gelöscht und danach nicht mehr gelesen. Die Schaltfläche **Aus Excel importieren…** im Register Positionen bleibt verfügbar, um später eine Arbeitsmappe zu übernehmen.

## Die Felder

Nur Nummer und Art sind erforderlich; alles andere ist freiwillig.

| Feld | Inhalt | Beispiel |
|---|---|---|
| Nummer (`position`) | die Nummer, erforderlich | `T001` |
| Art (`type`) | die Art des Bauteils, erforderlich | `Träger` |
| Werkstoff (`material`) | der Werkstoff | `Fichte` |
| Festigkeitsklasse (`resistance class`) | die Festigkeitsklasse | `C24` |
| Querschnittsart (`section type`) | die Art des Querschnitts: `rec`, `cir`, `pla`, `clt` oder ein Stahlprofil der SZS C5 (`IPE`, `HEA`, `ROR` …) | `rec` |
| Abmessung (`dimension`) | die Grösse des Querschnitts, nach seiner Art gelesen | `100/200` |
| Einheit (`units`) | die Einheit des Querschnitts: mm, cm oder m | `mm` |
| Feuchteklasse (`moisture class`) | die Feuchteklasse: 1, 2 oder 3 | `2` |
| Beschreibung (`description`) | ein freier Text | `Sparren, Achse 3` |

Die Nummer beginnt mit dem Buchstaben der Art — `T` für einen Träger, `S` für eine Stütze, `D` für eine Decke —, gefolgt vom Nummerierungszeichen des Geschosses und einer Nummer: `T001` ist der Träger 01 des Erdgeschosses. Das Register schlägt die nächste freie Nummer vor.

> [!tip]
> Die Abmessung wird nach der Art des Querschnitts gelesen: `rec` Breite und Höhe, `100/200`; `cir` der Durchmesser, `200`; `pla` die Dicke einer Platte, `22`; `clt` ihre Lagen, `20/30/20/30/20`; ein Stahlprofil die Grösse seiner Bezeichnung, `200` für IPE 200 oder `101.6x10` für ROR 101.6×10, in mm. Eine leere Art lässt die Abmessung beschreibenden Text, etwa `180` für eine Platte. **Ein Querschnitt, den Woodcore nicht lesen kann, hält den Export nicht an**: Er wird zur Warnung.

## Im Bericht

Jede Position erscheint in der Baustoffliste des Berichts, ohne dass etwas zu schreiben ist: der Abschnitt `003-baustoffe.typ` durchläuft alle Positionen mit `#position`, das die Zeile einer Position druckt — ihre ID in der Farbe ihres Typs, dann die verlangten Felder (`category-show:`), Querschnitt, Festigkeitsklasse, Beschreibung.

{{example position-2}}

Eine im Register hinzugefügte oder geänderte Position erreicht den Bericht sofort: Der Export folgt dem Speichern.
