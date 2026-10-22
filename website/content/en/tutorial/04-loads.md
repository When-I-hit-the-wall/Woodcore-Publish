# The loads

Loads are not entered in the Positions tab: they come from the **load workbook**, any `.xlsm` or `.xlsx` file of the project folder whose name contains `Belastungsannahmen`. Every load case is a **sheet** of that workbook, recognised by its prefix.

| Prefix | Load | Who calculates |
|---|---|---|
| `SL-` | snow, SIA 261 chapter 5 | Excel; Woodcore reads the values and the formulas |
| `EL+AL-` | permanent loads, layer by layer | Woodcore, from the layers entered |
| `WL-` | wind, SIA 261 chapter 6 | Excel; Woodcore reads the forces and envelopes the local ones |

**Copying a sheet adds a load case**: `SL-Dach2` is a second roof, with nothing written anywhere else. The sheet's name becomes the case's name in the report.

> [!warning]
> Woodcore reads the values Excel **calculated and saved**. Always save the workbook in Excel before importing.

## Print a load case

A case is printed whole by the file Woodcore writes for it, `#include domain-file("snow-load", "SL")`: the snow load of sheet `SL`, the formula in letters and then in numbers, every value with its standard.


The section `004-einwirkungen.typ` of a new project already prints every case of every load with a loop; name them one by one to choose each one's level.

## Live loads

Live loads come from Table 8 of SIA 261, with no workbook: you name the surface's category.

```typ
#include domain-file("live-load", "A1")
```
