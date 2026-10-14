# Die Lasten

Die Lasten werden nicht im Register Positionen erfasst: sie kommen aus der **Lasten-Arbeitsmappe**, jeder `.xlsm`- oder `.xlsx`-Datei im Projektordner, deren Name `Belastungsannahmen` enthält. Jeder Lastfall ist ein **Tabellenblatt** dieser Arbeitsmappe, an seinem Präfix erkannt.

| Präfix | Last | Wer rechnet |
|---|---|---|
| `SL-` | der Schnee, SIA 261 Kapitel 5 | Excel; Woodcore liest die Werte und die Formeln |
| `EL+AL-` | die ständigen Lasten, Schicht für Schicht | Woodcore, aus den erfassten Schichten |
| `WL-` | der Wind, SIA 261 Kapitel 6 | Excel; Woodcore liest die Kräfte und hüllt die lokalen Kräfte ein |

**Ein kopiertes Blatt ist ein weiterer Lastfall**: `SL-Dach2` ist ein zweites Dach, ohne anderswo etwas zu schreiben. Der Name des Blatts wird der Name des Falls im Bericht.

> [!warning]
> Woodcore liest die Werte, die Excel **berechnet und gespeichert** hat. Die Arbeitsmappe vor dem Import immer in Excel speichern.

## Einen Lastfall drucken

Ein Fall wird mit `#show-calc` vollständig gedruckt: die Schneelast des Blatts `SL`, die Formel in Buchstaben und dann in Zahlen, jeder Wert mit seiner Norm.

{{example show-calc-1}}

Der Abschnitt `004-einwirkungen.typ` eines neuen Projekts druckt bereits alle Fälle jeder Last mit einer Schleife; nennen Sie sie einzeln, um die Stufe jedes Falls zu wählen.

## Die Nutzlasten

Die Nutzlasten kommen aus Tabelle 8 der SIA 261, ohne Arbeitsmappe: man nennt die Kategorie der Fläche.

```typ
#show-live-load("A1")
```
