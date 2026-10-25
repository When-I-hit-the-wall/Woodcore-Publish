# Im Fenster von Woodcore importieren und erkunden

Ein Projekt öffnet sich im **Fenster von Woodcore**. Dort werden die Lastfälle erfasst und wird gezeichnet, was der Bericht zeigt; es exportiert, was das Projekt enthält, und zeigt, was der Export übernommen hat.

## Daten importieren

Die Schaltfläche **Daten importieren** liest die Dateien des Projekts — die in den Registern erfassten Lastfälle, die Positionen, die Zeichnungen —, rechnet, was zu rechnen ist, prüft jede Datei und schreibt den Export nach `Statischer Bericht (typst)/_woodcore/data/`. Geht etwas schief, wird nichts geschrieben: die Meldung nennt dann die Datei und das Feld, die zu korrigieren sind, und die bisherigen Daten bleiben angezeigt.

> [!note]
> Ein Projekt, das von einer früheren Version von Woodcore exportiert wurde, kompiliert nicht mehr, bis einmal **Daten importieren** geklickt wird. Eine im Ordner liegen gebliebene Datei `Belastungsannahmen` wird nie gelesen: der Export meldet sie mit einer Warnung.

## Die Register

| Register | Was man dort tut |
|---|---|
| **Wind**, **Schnee**, **Eigen- und Auflasten** | Die Lastfälle erfassen, unter **Einwirkungen**: jeder Fall ist eine Datei in `Woodcore-Datei/loads/` (Schritt 4). |
| **Variablen** | Jede Last, jeden Fall und jeden Wert durchgehen, mit seiner Herkunft bis zum Register, in dem er erfasst ist. |
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
