# Das PDF exportieren

**PDF exportieren** importiert die Arbeitsmappen und kompiliert dann den Bericht: `Statischer Rapport.pdf` wird neben `Statischer Rapport.typ` geschrieben und geöffnet. Schlägt der Import fehl, wird nichts kompiliert, und das bisherige PDF bleibt, wie es war.

## Stufe und Sprache wählen

Der kleine Pfeil neben der Schaltfläche öffnet ein Menü mit Einstellungen; sie gelten für die folgenden Exporte:

| Einstellung | Wirkung |
|---|---|
| **Wie im Dokument** | die Stufe und die Sprache, die das Dokument selbst festlegt |
| **Basis-Detailstufe 1, 2 oder 3** | die Stufe des Berichts; ein Aufruf, der seine eigene vorgibt, behält sie |
| **Einheitliche Detailstufe 1, 2 oder 3** | der ganze Bericht auf dieser Stufe, auch die Aufrufe, die eine vorgeben |
| **Sprache des Dokuments, de, fr, en** | die Sprache der Wörter, die Woodcore druckt |

So ergibt ein Projekt den Bericht für die Bauherrschaft (einheitlich 1), den für die Ingenieurin oder den Ingenieur (Basis-Detailstufe 2) und den für die Prüfung (einheitlich 3).

## Jeder Export wird archiviert

Jeder gelungene Export legt in `_Archiv/` eine Kopie des PDF und ein Zip des Stands ab, der es erzeugt hat — Bericht, Export, Engine, Zeichnungen —, benannt nach Datum und Uhrzeit. Ein vor langer Zeit abgegebener Bericht findet sich so wieder, wie er war.

## In der Befehlszeile

`woodcore-cli.exe` im Installationsordner tut dasselbe ohne Fenster:

```bash
woodcore-cli export --project "Halle Nord.woodcore" --uniform 3 --lang de
```

Das ist das Ende des Tutorials. Die [Befehlsreferenz](~/docs/) und die [Beispiele](~/examples/) führen weiter.
