# Write the report

The report is a Typst document: `Statischer Rapport.typ` and its sections, in `Statischer Bericht (typst)/Sections/`. **File › Open in VS Code** opens the folder; with the Tinymist extension, pin `Statischer Rapport.typ` as the main file (*Typst: Pin the main file*) to see the PDF's live preview.

## A section

Every section starts with the same line, which makes every command of Woodcore available:

```typ
#import "../commands.typ": *

= Einwirkungen

Die Schneelast wird nach SIA 261 ermittelt.

#show-calc("snow-load", "SL")
```

The text is yours, in the report's language; the commands print what the export calculated. The [reference](~/docs/) lists them all, with their examples.

## Tie calculations to a position

`#calc-block` groups the calculations that concern one or several positions, and prints at its head the line `#member` prints of each at level 1:

{{example calc-block-1}}

## Three levels of detail

Every command prints more or less depending on the **level**: 1 the result, for the client; 2 the important calculation, for the engineer; 3 every detail, for the checking engineer. The report's level is chosen at the export (step 8), and a call may set its own:

```typ
#show-calc("snow-load", "SL", level: 3)
```

> [!tip]
> In Woodcore's window, the **Commands** tab shows every example at levels 1, 2 and 3: the quickest way to see what a call will print.
