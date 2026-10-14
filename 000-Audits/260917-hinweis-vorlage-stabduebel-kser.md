# Hinweis an die verantwortliche Person der Vorlage «dowel connections»

**Vorlage:** `«dowel connections» template` (Excel-Tools)
**Blätter:** «Stabdübel (Holz-Holz)», Zelle C62, und «Stabdübel (Stahl-Holz)», Zelle C66 — Kser,Verb
**Gefunden:** periodisches Audit des Projekts «Statischer Rapport», 16.09.2026 (Befund AUD-2-3)
**Datum dieses Hinweises:** 17.09.2026

## Was nicht stimmt

Der Verschiebungsmodul der Verbindung Kser,Verb wird ohne den Umrechnungsfaktor η_w für die Steifigkeit berechnet:

| Blatt | Zelle | Formel heute |
|---|---|---|
| Stabdübel (Holz-Holz) | C62 | `=MIN(C59:D59)*C29*C39` |
| Stabdübel (Stahl-Holz) | C66 | `=C63*C26*C27` |

Die Feuchteklasse (C13 bzw. C35) geht damit nicht in Kser,Verb ein. Für die Feuchteklassen 2 und 3 ist der Wert zu steif.

## Was die Norm sagt

- **SIA 265:2021, 3.2.1.3:** η_w rechnet «die Tragwiderstände und die Steifigkeitswerte» von der Feuchteklasse 1 auf die Feuchteklassen 2 und 3 um.
- **SIA 265:2021, Tabelle 4 (S. 22):** η_w für die Steifigkeit = 1,0 / 0,90 / 0,75 für die Feuchteklassen 1 / 2 / 3.
- **SIA 265:2021, Tabelle 25 (S. 66):** Kser ist «für Feuchteklasse 1» angegeben.

## Grösse der Abweichung

- Feuchteklasse 2: Kser,Verb der Vorlage um 11 % zu hoch (Faktor 1/0,90).
- Feuchteklasse 3: um 33 % zu hoch (Faktor 1/0,75).
- Beispiel C24/C24, d = 10 mm, zweischnittig, t = 50/100 mm, 4 Stabdübel, Feuchteklasse 2: Vorlage 22 503,25 N/mm, normgerecht 20 252,93 N/mm.

Das Audit hat 59 berechnete Fälle der Vorlage mit einer unabhängigen Berechnung verglichen. Alle 22 Fälle in Feuchteklasse 2 oder 3 zeigen genau diese Abweichung, sonst keine.

## Vorschlag

Die Vorlage enthält den Faktor bereits: Blatt «Daten», Spalte O («ηw,Steifigkeit»), O24 für Stahl-Holz und O29 für Holz-Holz. Er wird nur nicht verwendet.

| Blatt | Zelle | Formel vorgeschlagen |
|---|---|---|
| Stabdübel (Holz-Holz) | C62 | `=MIN(C59:D59)*C29*C39*Daten!O29` |
| Stabdübel (Stahl-Holz) | C66 | `=C63*C26*C27*Daten!O24` |

Im Projekt ist diese Korrektur in `Verbindung.xlsm` (gleiche Formeln wie die Vorlage) am 17.09.2026 mit dem Einverständnis des Ingenieurs so eingetragen worden. Der Blattschutz (ohne Passwort) wurde mit denselben Optionen wiederhergestellt. Eine Eintragung im Änderungsjournal der Vorlage wäre sinnvoll.
