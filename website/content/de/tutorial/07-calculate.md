# Im Bericht rechnen

Nicht alles kommt aus dem Export: ein Wert aus einem Herstellerblatt, ein von Hand geschriebener Nachweis. Woodcore rechnet solche Zeilen im Bericht selbst, mit ihren Einheiten, und druckt sie wie den Rest.

## Variablen und Formeln

`#var` hält eine Variable fest und druckt sie; `#eq` wertet eine Formel aus, die die Variablen **nennt**, druckt sie in Buchstaben und dann in Zahlen und rechnet die Einheiten um:

{{example eq-2}}

Eine Variable behält ihren Namen für den Rest des Dokuments: die nächste Zeile kann sie wiederum nennen. Mehrere Festlegungen passen mit `#var-line` auf eine Zeile, und `level: 0` hält einen Wert fest, ohne ihn zu drucken.

## Ein Nachweis

`#verify` vergleicht die beiden Seiten einer Beziehung, druckt das Zeichen, das gilt, und markiert die Antwort mit ✔ oder ✘:

{{example verify-1}}

## Ein Holzbauteil nachweisen

Die Nachweise der SIA 265, Kapitel 4.2, gehen in zwei Schritten: `#member` beschreibt das Bauteil einmal — Querschnitt, Festigkeitsklasse und Feuchteklasse, aus seiner Position gelesen —, dann weist ein Befehl `verify-…` es für jede Beanspruchung nach.

{{example verify-compression-1}}

`verify-tension`, `verify-compression`, `verify-bending`, `verify-bending-normal`, `verify-shear` und die übrigen folgen derselben Form; die Normalkraft ist vorzeichenbehaftet, Zug positiv.

> [!note]
> Was im Bericht gerechnet wird, ist im Export nicht nachverfolgt: der Text daneben muss sagen, woher die von Hand eingegebenen Werte kommen.
