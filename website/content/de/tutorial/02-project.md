# Ein Projekt anlegen

Ohne Projekt gestartet, öffnet sich Woodcore auf seiner Startseite: die zuletzt geöffneten Projekte und drei Schaltflächen — **Öffnen…**, **Neues Projekt…** und **Alten Ordner umwandeln…**.

## Neues Projekt

Auf **Neues Projekt…** klicken. Das Fenster fragt nach:

- dem **Speicherort** und dem **Projektordner**, der leer sein muss;
- **Name** und **Nummer** des Projekts, der **Bauherrschaft** und der **Adresse**;
- dem **Büro**, der **Verfasserin** oder dem **Verfasser** und der **Prüferin** oder dem **Prüfer**.

Diese Angaben stehen auf dem Titelblatt des Berichts und in den Metadaten des PDF. Sie lassen sich jederzeit unter **Datei › Projekteigenschaften…** ändern.

## Was der Ordner enthält

```text
Halle Nord/
├── Halle Nord.woodcore          das Projekt: diese Datei wird geöffnet
├── Statischer Bericht (typst)/  der Bericht
│   ├── Statischer Rapport.typ   das Hauptdokument
│   ├── Sections/                ein Abschnitt pro Datei
│   ├── commands.typ             alle Befehle von Woodcore
│   └── _woodcore/               Export und Engine — erzeugt, nie von Hand geändert
├── Woodcore-Datei/              was in Woodcore erfasst und gezeichnet wird, auch die Positionen (Schritt 3)
└── _Archiv/                     ein Zip und eine Kopie des PDF pro Export
```

Sonst ist nichts in diesen Ordner zu kopieren: Wind, Schnee und ständige Lasten werden in den Registern von Woodcore erfasst und in `Woodcore-Datei/loads/` gespeichert (Schritt 4).

> [!note]
> Ein in einem Fenster geöffnetes Projekt ist durch eine Datei `Halle Nord.woodcore.lock` **gesperrt**. Öffnet es eine Kollegin oder ein Kollege gleichzeitig, sagt Woodcore es und bietet den Schreibschutz an: zwei Fenster, die dasselbe Projekt speichern, verlören die Arbeit des ersten.

## Ein Projekt öffnen

Ein Doppelklick auf die `.woodcore`-Datei, **Öffnen…** auf der Startseite, oder eine `.woodcore`-Datei, die auf das Fenster gezogen wird. Jedes Projekt öffnet sich in einem eigenen Fenster; **Datei › In neuem Fenster öffnen…** öffnet ein zweites daneben.
