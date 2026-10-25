# Die Lasten

Die Lasten werden nicht im Register Positionen erfasst: jeder Lastfall wird im **Register seiner Last** erfasst, unter **Einwirkungen** im linken Bereich, und als Datei in `Woodcore-Datei/loads/` gespeichert (`wind/`, `snow/`, `dead/`).

| Register | Last | Wer rechnet |
|---|---|---|
| **Schnee** | der Schnee, SIA 261 Kapitel 5 | Woodcore, aus dem erfassten Gebäude, Standort und Dach |
| **Eigen- und Auflasten** | die ständigen Lasten, Schicht für Schicht | Woodcore, aus den erfassten Schichten |
| **Wind** | der Wind, SIA 261 Kapitel 6 | Woodcore, aus den erfassten Grunddaten und dem Gebäude von Anhang C |

**Ein neuer Fall ist eine neue Datei**: «Neu» oder «Duplizieren» in der Liste des Registers fügt ein zweites Dach hinzu, ohne anderswo etwas zu schreiben. Der Name des Falls ist der seiner Datei und der, den man dem Bericht nennt.

> [!warning]
> Woodcore öffnet keine Lasten-Arbeitsmappe. Eine Datei, deren Name `Belastungsannahmen` enthält und die im Projektordner liegen geblieben ist, wird nie gelesen: jeder Export meldet sie mit einer Warnung, die sie nennt und daran erinnert, dass die Fälle in den Registern erfasst werden.

## Einen Lastfall drucken

Ein Fall wird vollständig durch die Datei gedruckt, die Woodcore für ihn schreibt, `#include domain-file("snow-load", "SL")`: die Schneelast des Falls `SL`, die Formel in Buchstaben und dann in Zahlen, jeder Wert mit seiner Norm.


Der Abschnitt `004-einwirkungen.typ` eines neuen Projekts druckt bereits alle Fälle jeder Last mit einer Schleife; nennen Sie sie einzeln, um die Stufe jedes Falls zu wählen.

## Die Nutzlasten

Die Nutzlasten kommen aus Tabelle 8 der SIA 261, ohne etwas zu erfassen: man nennt die Kategorie der Fläche.

```typ
#include domain-file("live-load", "A1")
```
