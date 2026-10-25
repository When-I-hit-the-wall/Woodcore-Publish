# The loads

Loads are not entered in the Positions tab: every load case is entered in the **tab of its load**, under **Actions** in the left pane, and saved as a file of `Woodcore-Datei/loads/` (`wind/`, `snow/`, `dead/`).

| Tab | Load | Who calculates |
|---|---|---|
| **Snow** | snow, SIA 261 chapter 5 | Woodcore, from the building, the site and the roof entered |
| **Self-weight and superimposed load** | permanent loads, layer by layer | Woodcore, from the layers entered |
| **Wind** | wind, SIA 261 chapter 6 | Woodcore, from the basic data and the Annex C building entered |

**A new case is a new file**: “New” or “Duplicate” in the tab's list adds a second roof, with nothing written anywhere else. The case's name is its file's and the one you give the report.

> [!warning]
> Woodcore opens no load workbook. A file whose name contains `Belastungsannahmen`, left in the project folder, is never read: every export points it out in a warning that names it and recalls that the cases are entered in the tabs.

## Print a load case

A case is printed whole by the file Woodcore writes for it, `#include domain-file("snow-load", "SL")`: the snow load of case `SL`, the formula in letters and then in numbers, every value with its standard.


The section `004-einwirkungen.typ` of a new project already prints every case of every load with a loop; name them one by one to choose each one's level.

## Live loads

Live loads come from Table 8 of SIA 261, with nothing to enter: you name the surface's category.

```typ
#include domain-file("live-load", "A1")
```
