# Neuerungen

Was jede Version von Woodcore bringt, was sie an einem bereits geschriebenen Bericht ändert, und was beim Wechsel zu ihr zu tun ist. Lesen Sie die Seiten aller Versionen zwischen Ihrer und der neuen: die Änderungen summieren sich.

## Woodcore aktualisieren

1. **Installieren Sie die neue Version.** Woodcore bietet sie beim Start an (**Installieren**), oder laden Sie sie auf der Seite [Herunterladen](~/download/) herunter. Sie wird **neben** den bisherigen Versionen installiert, ohne sie zu ersetzen.
2. **Öffnen Sie Ihr Projekt.** Woodcore vergleicht die ins Projekt kopierte Engine (`Statischer Bericht (typst)/_woodcore/`) mit der eigenen und fragt: «Dieses Projekt verwendet die Engine von Woodcore 0.88.0. Auf 0.89.0 aktualisieren?».
   - **Unterschiede anzeigen…** zeigt, was sich in den Dateien der Engine ändert;
   - **Aktualisieren** kopiert die neue Engine: die neuen Befehle stehen im Bericht zur Verfügung;
   - **Später** ändert nichts; die Frage kommt beim nächsten Öffnen und beim nächsten Export wieder.
3. **Exportieren Sie das PDF und lesen Sie es durch.** Eine neue Engine kann einen Bericht anders drucken — Layout, ein Text, eine Detailstufe. Die Zahlen ändern sich nur, wo die Seite der Version es sagt.
4. **Erledigen Sie die Punkte «Zu tun»** der übersprungenen Versionen.

> [!tip]
> Ein abgeschlossenes Projekt kann bei seiner Version bleiben: unter **Datei › Projekteigenschaften…** legt das Feld **Woodcore-Version** es fest. Ein Doppelklick auf das Projekt öffnet dann diese Version, die installiert bleibt.

## Zurück

Bei einer Aktualisierung geht nichts verloren: jeder Export legt in `_Archiv/` ein Zip des Stands ab, der ihn erzeugt hat, Engine inbegriffen, und die bisherigen Woodcore-Versionen bleiben installiert. Eine Version wird einzeln deinstalliert, unter **Einstellungen › Apps** von Windows.
