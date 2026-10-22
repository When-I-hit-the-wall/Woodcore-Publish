# Describe the positions

A **position** is a member of the structure — a beam, a column, a panel — as the position plan numbers it. The positions are entered in Woodcore's **Positions** tab, one row per member; they are saved in `Woodcore-Datei/positions.json`.

> [!note]
> An older project that holds a `Positionen.xlsx`: at its first opening Woodcore imports the workbook once, then moves it to `_Archiv/` — it is never deleted and is not read again. The **Import from Excel…** button of the Positions tab stays available to take in a workbook later.

## The fields

Only the number and the type are required; everything else is optional.

| Field | Holds | Example |
|---|---|---|
| number (`position`) | the number, required | `T001` |
| type (`type`) | the kind of member, required | `Träger` |
| material (`material`) | the material | `Fichte` |
| strength class (`resistance class`) | the strength class | `C24` |
| section type (`section type`) | the kind of section: `rec`, `cir`, `pla`, `clt`, or a steel profile of SZS C5 (`IPE`, `HEA`, `ROR` …) | `rec` |
| dimension (`dimension`) | the section's size, read by its type | `100/200` |
| units (`units`) | the section's unit: mm, cm or m | `mm` |
| moisture class (`moisture class`) | the moisture class: 1, 2 or 3 | `2` |
| description (`description`) | free text | `Rafter, axis 3` |

The number starts with the letter of the kind — `T` for a beam (Träger), `S` for a column (Stütze), `D` for a slab (Decke) — followed by the storey's numbering character and a number: `T001` is beam 01 of the ground floor. The tab proposes the next free number.

> [!tip]
> The dimension is read by its section type: `rec` its width and height, `100/200`; `cir` its diameter, `200`; `pla` a plate's thickness, `22`; `clt` its layers, `20/30/20/30/20`; a steel profile its designation's size, `200` for IPE 200 or `101.6x10` for ROR 101.6×10, in mm. An empty type leaves the dimension descriptive text, such as `180` for a panel. **A section Woodcore cannot read does not stop the export**: it becomes a warning.

## In the report

Every position appears in the report's list of materials without writing anything: the section `003-baustoffe.typ` loops over all of them with `#position`, which prints a position's line — its id in its type's colour, then the fields asked for (`category-show:`), the section, the strength class, the description.

{{example position-2}}

A position added or changed in the tab reaches the report at once: the export follows the save.
