#import "/commands.typ": *

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

// woodcore:object doc-table vibrations-table
#doc-table(
  columns: (
    (id: "use", title: [Nutzung], kind: "wide"),
    (id: "f", title: [Mindest-Eigenfrequenz $f$], unit: "Hz", kind: "number"),
    (id: "basis", title: [Grundlage]),
  ),
  hidden: (),
  rows: (
    (use: [Turn- und Sporthallen], f: [> 8.0], basis: [SIA 260, Tab. 5]),
    (use: [Tanzlokale und Konzertsäle], f: [> 7.0], basis: [SIA 260, Tab. 5]),
  ),
  caption: [Mindest-Eigenfrequenzen],
)
// woodcore:/object vibrations-table
// woodcore:/shared vibrations
