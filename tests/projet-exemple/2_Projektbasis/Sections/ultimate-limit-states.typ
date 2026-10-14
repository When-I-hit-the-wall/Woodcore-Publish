#import "/commands.typ": *

// woodcore:object heading title
== Grenzzustände der Tragsicherheit
// woodcore:/object title

// woodcore:object text p1
Die Tragsicherheit gilt für Grenzzustände der Typen 2 und 3 als nachgewiesen, wenn der Bemessungswert der Auswirkung $E_d$ des massgebenden Lastfalls in der Bemessungssituation kleiner oder gleich dem Bemessungswert des Tragwiderstands $R_d$ ist (SIA 260, Ziffer 4.4.3.3):
// woodcore:/object p1

// woodcore:object text p2
$ E_d <= R_d $
// woodcore:/object p2

// woodcore:object text p3
Für den Grenzzustand vom Typ 1 (Gesamtstabilität) wird $E_(d,"dst")$ ≤ $E_(d,"stb")$ nachgewiesen (Ziffer 4.4.3.2); für den Typ 4 (Ermüdung) $E_d$ ≤ $R_d$ (Ziffer 4.4.3.8). Im Hochbau ist im Allgemeinen der Grenzzustand vom Typ 2 (Tragwiderstand des Tragwerks) massgebend. [Der Verzicht auf den Nachweis eines Grenzzustands wird im Abschnitt «Verzicht auf Nachweise» begründet.]
// woodcore:/object p3

// woodcore:object doc-checklist limit-state-types
#doc-checklist(
  label: [Nachgewiesene Grenzzustände der Tragsicherheit],
  options: (
    (id: "type-1", label: [Typ 1: Gesamtstabilität (Kippen, Abheben, Aufschwimmen)], checked: true),
    (id: "type-2", label: [Typ 2: Tragwiderstand des Tragwerks oder eines seiner Bauteile], checked: true),
    (id: "type-3", label: [Typ 3: Tragwiderstand des Baugrunds], checked: false),
    (id: "type-4", label: [Typ 4: Ermüdungsfestigkeit], checked: false),
  ),
)
// woodcore:/object limit-state-types
