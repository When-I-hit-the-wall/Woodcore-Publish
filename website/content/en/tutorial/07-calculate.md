# Calculate in the report

Not everything comes from the export: a value from a manufacturer's sheet, a check written by hand. Woodcore calculates those lines in the report itself, with their units, and prints them like the rest.

## Variables and formulas

`#var` writes a variable down and prints it; `#eq` evaluates a formula that **names** the variables, prints it in letters and then in numbers, and converts the units:

{{example eq-2}}

A variable keeps its name for the rest of the document: the next line can name it in turn. Several `#var` written in a sentence are printed in that sentence, and `level: 0` declares a value without printing it.

## A check

`#verify` compares both sides of a relation, prints the sign that holds, and marks the answer ✔ or ✘:

{{example verify-1}}

## Check a timber member

The checks of SIA 265, chapter 4.2, are made in the window's tabs — Tension, Compression, Bending, Shear, Buckling, Lateral torsional buckling: Woodcore writes each out whole in a file of its own, every value checked against the export, and the section includes it:

```typ
#include domain-file("check", "ZT-01")
```

What you change in that file with VS Code is taken back by Woodcore line by line; a value the export no longer gives turns red.

> [!note]
> What is calculated in the report is not traced in the export: the text around it must say where values typed by hand come from.
