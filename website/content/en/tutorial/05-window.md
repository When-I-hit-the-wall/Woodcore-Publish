# Import and explore in Woodcore's window

A project opens in **Woodcore's window**. It imports the workbooks, shows what they hold, and is where you draw what a workbook cannot describe.

## Import from Excel

The **Import from Excel** button reads the load workbooks, calculates what is to be calculated, checks every file and writes the export into `Statischer Bericht (typst)/_woodcore/data/`. Nothing is written when something is wrong: the message then names the sheet and the cell to correct, and the previous data stays on screen.

> [!note]
> A banner points out a workbook saved after the last import: importing again is all it takes.

## The tabs

| Tab | What you do there |
|---|---|
| **Loads** | Browse every load, case and value, with its provenance down to the Excel cell. A double-click copies the Typst call that prints it. |
| **Position plan** | Import an architect's document (PDF, image, SVG, DXF, DWG), scroll through its pages, tick the pages that become plans, then set the positions' STE symbols on them, with the axes and the scale. Drawing sheets and the `#show-plan` command are prepared there too. |
| **Positions** | The source of the positions: add, change or delete a position (`Woodcore-Datei/positions.json`); the export follows at once. **Import from Excel…** takes in an old `Positionen.xlsx`. |
| **Static models** | Draw a static system: members, supports, releases, loads and dimensions. |
| **Schemas** | Draw a connection detail at its real size: the pieces, the fasteners, construction aids, dimensions. |
| **Fasteners** | Calculate the resistance of a dowel connection after SIA 265, on a schema. |
| **Polar moments of inertia** | Distribute N, V and M over the fasteners of a schema. |
| **Commands** | The documentation of every command of the report, with its examples — this site's. |

What you draw is saved in `Woodcore-Datei/` and exported at once: the report sees it without another import.

## Copy a call

Nearly every row of the window offers the call that prints it in the report. A double-click copies it, a right-click lists them all. For a position drawn on a plan, for instance:

```typ
#show-plan("Velo-Unterstand", highlight: "T001", detail: true)
```
