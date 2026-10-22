# Im Fenster von Woodcore importieren und erkunden

Ein Projekt öffnet sich im **Fenster von Woodcore**. Es importiert die Arbeitsmappen, zeigt, was sie enthalten, und dort wird gezeichnet, was eine Arbeitsmappe nicht beschreiben kann.

## Aus Excel importieren

Die Schaltfläche **Aus Excel importieren** liest die Lasten-Arbeitsmappen, rechnet, was zu rechnen ist, prüft jede Datei und schreibt den Export nach `Statischer Bericht (typst)/_woodcore/data/`. Geht etwas schief, wird nichts geschrieben: die Meldung nennt dann das Blatt und die Zelle, die zu korrigieren sind, und die bisherigen Daten bleiben angezeigt.

> [!note]
> Ein Band meldet eine Arbeitsmappe, die nach dem letzten Import gespeichert wurde: es genügt, erneut zu importieren.

## Die Register

| Register | Was man dort tut |
|---|---|
| **Lasten** | Jede Last, jeden Fall und jeden Wert durchgehen, mit seiner Herkunft bis zur Excel-Zelle. Ein Doppelklick kopiert den Typst-Aufruf, der ihn druckt. |
| **Positionsplan** | Ein Dokument der Architektin oder des Architekten importieren (PDF, Bild, SVG, DXF, DWG), seitenweise durchgehen, die Seiten ankreuzen, die zu Plänen werden, und darauf die STE-Symbole der Positionen setzen, mit Achsen und Massstab. Auch die Planblätter und der Befehl `#show-plan` werden dort vorbereitet. |
| **Positionen** | Die Quelle der Positionen: eine Position hinzufügen, ändern oder löschen (`Woodcore-Datei/positions.json`); der Export folgt sofort. **Aus Excel importieren…** übernimmt eine alte `Positionen.xlsx`. |
| **Statische Systeme** | Ein statisches System zeichnen: Stäbe, Auflager, Gelenke, Lasten und Bemassungen. |
| **Schemas** | Ein Anschlussdetail in wahrer Grösse zeichnen: die Bauteile, die Verbindungsmittel, die Konstruktionshilfen, die Bemassungen. |
| **Verbindungsmittel** | Den Tragwiderstand einer Stabdübelverbindung nach SIA 265 berechnen, auf einem Schema. |
| **Polare Trägheitsmomente** | N, V und M auf die Verbindungsmittel eines Schemas verteilen. |
| **Befehle** | Die Dokumentation aller Befehle des Berichts, mit ihren Beispielen — die dieser Website. |

Was gezeichnet wird, wird in `Woodcore-Datei/` gespeichert und sofort exportiert: der Bericht sieht es ohne neuen Import.

## Einen Aufruf kopieren

Fast jede Zeile des Fensters bietet den Aufruf an, der sie im Bericht druckt. Ein Doppelklick kopiert ihn, ein Rechtsklick listet alle. Zum Beispiel für eine auf einem Plan gezeichnete Position:

```typ
#figure(image-positions-plan("Velo-Unterstand", highlight: "T001", frame: "highlight"), kind: image, caption: [Velo-Unterstand]) <fig-velo>
```
