# Woodcore herunterladen

{{download}}

## Voraussetzungen

| Komponente | | Bemerkung |
|---|---|---|
| Windows 10 oder 11, 64 Bit | nötig | Woodcore ist ein Windows-Programm. |
| Rund 250 MB pro Version | nötig | Jede Version wird in einen eigenen Ordner installiert. |
| Administratorrechte | nein | Installiert wird für den Benutzer, in `%LOCALAPPDATA%\Programs\Woodcore\`. |
| Microsoft Excel und eine Lasten-Arbeitsmappe | nein | Wind, Schnee und ständige Lasten werden in den Registern von Woodcore erfasst, wie die Positionen. Eine Arbeitsmappe `Belastungsannahmen` wird nie geöffnet. |
| Visual Studio Code mit der Erweiterung Tinymist | empfohlen | Zum Schreiben des Berichts, mit der Dokumentation jedes Befehls beim Überfahren. |
| Typst | inbegriffen | Typst 0.14.2 wird mit Woodcore geliefert: nichts zu installieren. |
| Internetverbindung | freiwillig | Nur, um zu erfahren, ob eine neue Version veröffentlicht ist. |

## Installieren

1. Das Installationsprogramm oben herunterladen und starten.
2. Windows kann «Der Computer wurde durch Windows geschützt» anzeigen: das Installationsprogramm ist nicht signiert. Auf **Weitere Informationen** klicken, dann auf **Trotzdem ausführen**.
3. Die Sprache des Assistenten wählen und die Option **.woodcore-Dateien mit Woodcore öffnen** angekreuzt lassen: ein Doppelklick auf ein Projekt öffnet es dann.
4. Am Ende öffnet sich Woodcore auf seiner Startseite.

Das Startmenü enthält **Woodcore**, das immer die neueste installierte Version öffnet, und einen Eintrag pro Version.

## Aktualisierungen

Bei jedem Start fragt Woodcore diese Website, ob eine neue Version veröffentlicht ist. Wenn ja, stellt ein Fenster sie mit ihren Neuerungen vor:

- **Installieren** lädt das Installationsprogramm herunter, prüft seine SHA-256-Prüfsumme und startet es;
- **Später** fragt am nächsten Tag wieder;
- **Diese Version überspringen** bietet sie nicht mehr an — die nächste schon.

Ohne Verbindung erscheint nichts, und nichts wird langsamer.

## Mehrere Versionen nebeneinander

Eine neue Version wird **neben** den bisherigen installiert, ohne sie zu ersetzen. So öffnet sich ein vor Jahren exportiertes Projekt mit der Version, die es erzeugt hat: unter **Datei › Projekteigenschaften** legt das Feld **Woodcore-Version** ein Projekt auf eine Version fest. Ein Doppelklick auf ein Projekt öffnet die Version, die es verlangt, sonst die neueste.

## Deinstallieren

Jede Version wird einzeln deinstalliert, unter **Einstellungen › Apps** von Windows, mit dem Namen «Woodcore 0.89.0». Ihre Projekte werden nie berührt: sie liegen in eigenen Ordnern.
