# Den Bericht schreiben

Der Bericht ist ein Typst-Dokument: `Statischer Rapport.typ` und seine Abschnitte, in `Statischer Bericht (typst)/Sections/`. **Datei › In VS Code öffnen** öffnet den Ordner; mit der Erweiterung Tinymist `Statischer Rapport.typ` als Hauptdatei festlegen (*Typst: Pin the main file*), um die laufende Vorschau des PDF zu sehen.

## Ein Abschnitt

Jeder Abschnitt beginnt mit derselben Zeile, die alle Befehle von Woodcore verfügbar macht:

```typ
#import "../commands.typ": *

= Einwirkungen

Die Schneelast wird nach SIA 261 ermittelt.

#show-calc("snow-load", "SL")
```

Der Text ist Ihrer, in der Sprache des Berichts; die Befehle drucken, was der Export berechnet hat. Die [Referenz](~/docs/) listet sie alle, mit ihren Beispielen.

## Berechnungen einer Position zuordnen

`#calc-block` fasst die Berechnungen zusammen, die eine oder mehrere Positionen betreffen, und druckt als Kopf die Zeile, die `#member` auf Stufe 1 von jeder druckt:

{{example calc-block-1}}

## Drei Detailstufen

Jeder Befehl druckt mehr oder weniger je nach **Stufe**: 1 das Ergebnis, für die Bauherrschaft; 2 die wichtige Berechnung, für die Ingenieurin oder den Ingenieur; 3 jedes Detail, für die Prüfung. Die Stufe des Berichts wird beim Export gewählt (Schritt 8), und ein Aufruf kann seine eigene vorgeben:

```typ
#show-calc("snow-load", "SL", level: 3)
```

> [!tip]
> Im Fenster von Woodcore zeigt das Register **Befehle** jedes Beispiel auf den Stufen 1, 2 und 3: der schnellste Weg zu sehen, was ein Aufruf drucken wird.
