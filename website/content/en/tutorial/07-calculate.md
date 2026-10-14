# Calculate in the report

Not everything comes from the export: a value from a manufacturer's sheet, a check written by hand. Woodcore calculates those lines in the report itself, with their units, and prints them like the rest.

## Variables and formulas

`#var` writes a variable down and prints it; `#eq` evaluates a formula that **names** the variables, prints it in letters and then in numbers, and converts the units:

{{example eq-2}}

A variable keeps its name for the rest of the document: the next line can name it in turn. Several declarations fit on one line with `#var-line`, and `level: 0` declares a value without printing it.

## A check

`#verify` compares both sides of a relation, prints the sign that holds, and marks the answer ✔ or ✘:

{{example verify-1}}

## Check a timber member

The checks of SIA 265, chapter 4.2, take two steps: `#member` describes the member once — section, strength class and moisture class, read from its position —, then a `verify-…` command checks it for each action.

{{example verify-compression-1}}

`verify-tension`, `verify-compression`, `verify-bending`, `verify-bending-normal`, `verify-shear` and the others take the same form; the normal force is signed, tension positive.

> [!note]
> What is calculated in the report is not traced in the export: the text around it must say where values typed by hand come from.
