#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Schwingungen
// woodcore:/object title
// woodcore:shared vibrations

// woodcore:object text p1
Schwingungen dürfen weder die Funktionstüchtigkeit des Bauwerks einschränken noch den Komfort der Nutzenden beeinträchtigen. Die folgenden Mindest-Eigenfrequenzen sind Richtwerte; abweichende Werte sind zugelassen, wenn eine genauere dynamische Berechnung unter Berücksichtigung der Dämpfung durchgeführt wird. [Besondere Kriterien für leichte Decken (Holz): …]
// woodcore:/object p1

// woodcore:object text p2
Schwingungserzeugende Geräte sind schwimmend gemäss den Angaben der Bauphysik zu lagern. [Erschütterungen infolge Bahn- oder Strassenverkehr: durch die Bauherrschaft abzuklären.]
// woodcore:/object p2

// woodcore:object table vibrations-table
#figure(
  table(
    columns: (1fr, auto, auto),
    align: (left, right, left),
    table.hline(stroke: 1pt),
    table.header([*Nutzung*], [*Mindest-Eigenfrequenz $f$*], [*Grundlage*]),
    table.hline(stroke: 0.5pt),
    [Turn- und Sporthallen], [> 8.0], [SIA 260, Tab. 5],
    [Tanzlokale und Konzertsäle], [> 7.0], [SIA 260, Tab. 5],
    table.hline(stroke: 1pt),
  ),
  caption: [Mindest-Eigenfrequenzen],
)
// woodcore:/object vibrations-table
// woodcore:/shared vibrations
