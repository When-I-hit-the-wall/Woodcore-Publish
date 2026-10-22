# Im Bericht rechnen

Nicht alles kommt aus dem Export: ein Wert aus einem Herstellerblatt, ein von Hand geschriebener Nachweis. Woodcore rechnet solche Zeilen im Bericht selbst, mit ihren Einheiten, und druckt sie wie den Rest.

## Variablen und Formeln

`#var` hält eine Variable fest und druckt sie; `#eq` wertet eine Formel aus, die die Variablen **nennt**, druckt sie in Buchstaben und dann in Zahlen und rechnet die Einheiten um:

{{example eq-2}}

Eine Variable behält ihren Namen für den Rest des Dokuments: die nächste Zeile kann sie wiederum nennen. Mehrere `#var` in einem Satz werden in diesem Satz gedruckt, und `level: 0` hält einen Wert fest, ohne ihn zu drucken.

## Ein Nachweis

`#verify` vergleicht die beiden Seiten einer Beziehung, druckt das Zeichen, das gilt, und markiert die Antwort mit ✔ oder ✘:

{{example verify-1}}

## Ein Holzbauteil nachweisen

Die Nachweise der SIA 265, Kapitel 4.2, entstehen in den Registern des Fensters — Zug, Druck, Biegung, Schub, Knicken, Kippen: Woodcore schreibt jeden vollständig in eine eigene Datei, jeden Wert gegen den Export geprüft, und der Abschnitt bindet sie ein:

```typ
#include domain-file("check", "ZT-01")
```

Was Sie in dieser Datei mit VS Code ändern, übernimmt Woodcore Zeile für Zeile; ein Wert, den der Export nicht mehr sagt, erscheint rot.

> [!note]
> Was im Bericht gerechnet wird, ist im Export nicht nachverfolgt: der Text daneben muss sagen, woher die von Hand eingegebenen Werte kommen.
