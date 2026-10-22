# Write the report

The report is a Typst document: `Statischer Rapport.typ` and its sections, in `Statischer Bericht (typst)/Sections/`. **File › Open in VS Code** opens the folder; with the Tinymist extension, pin `Statischer Rapport.typ` as the main file (*Typst: Pin the main file*) to see the PDF's live preview.

## A section

Every section starts with the same line, which makes every command of Woodcore available:

```typ
#import "../commands.typ": *

= Einwirkungen

Die Schneelast wird nach SIA 261 ermittelt.

#include domain-file("snow-load", "SL")
```

The text is yours, in the report's language; the commands print what the export calculated: a calculation of Woodcore's is written out whole in a file of its own, which the section includes. The [reference](~/docs/) lists them all, with their examples.

## Tie calculations to a position

`#position` names a position on a line, its id in its type's colour, and the calculation that concerns it follows in a `#domain` of its own -- or in the file Woodcore wrote for a check, `#include domain-file("check", "ZT-01")`:

{{example domain-1}}

## Three levels of detail

Every command prints more or less depending on the **level**: 1 the result, for the client; 2 the important calculation, for the engineer; 3 every detail, for the checking engineer. The report's level is chosen at the export (step 8), and a call may set its own:

```typ
#var("s_k", domain: ("snow-load", "SL"), level: 3)
```

> [!tip]
> In Woodcore's window, the **Commands** tab shows every example at levels 1, 2 and 3: the quickest way to see what a call will print.
