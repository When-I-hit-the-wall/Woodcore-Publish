# Woodcore installieren

Woodcore ist in einer Minute installiert, ohne Administratorrechte, und enthält alles, was ein Bericht braucht: das Programm mit seinem Fenster, die Befehlszeile `woodcore-cli` und Typst.

## Herunterladen und installieren

Das Installationsprogramm auf der Seite [Herunterladen](~/download/) holen und starten. Da es nicht signiert ist, kann Windows «Der Computer wurde durch Windows geschützt» anzeigen: auf **Weitere Informationen** klicken, dann auf **Trotzdem ausführen**.

Die Option **.woodcore-Dateien mit Woodcore öffnen** angekreuzt lassen. Ein Woodcore-Projekt ist ein Ordner mit einer Datei `<Name>.woodcore`: mit dieser Option öffnet ein Doppelklick auf diese Datei das Projekt, so wie sich ein Word-Dokument in Word öffnet.

> [!tip]
> Woodcore wird für Ihren Benutzer in `%LOCALAPPDATA%\Programs\Woodcore\<Version>\` installiert. Jede Version hat ihren Ordner: eine neue Version ersetzt nie die alte.

## Die Werkzeuge daneben

Woodcore liest Excel-Arbeitsmappen und schreibt einen Bericht in Typst. Zwei Werkzeuge machen die Arbeit bequem:

- **Microsoft Excel**, um die Lasten-Arbeitsmappe auszufüllen;
- **Visual Studio Code** mit der Erweiterung **Tinymist**, um den Bericht zu schreiben: Tinymist zeigt die Dokumentation jedes Befehls beim Überfahren und eine laufende Vorschau des PDF.

Typst selbst wird mit Woodcore geliefert: es ist nichts weiter zu installieren.

## Auf dem neuesten Stand bleiben

Bei jedem Start schaut Woodcore, ob auf dieser Website eine neuere Version veröffentlicht ist. Wenn ja, stellt ein Fenster sie mit ihren Neuerungen vor und bietet an, sie zu installieren: Woodcore lädt das Installationsprogramm herunter, prüft seine Prüfsumme und startet es. Die installierten Versionen bleiben, und das Startmenü öffnet fortan die neueste.

Im nächsten Schritt legen wir ein erstes Projekt an.
