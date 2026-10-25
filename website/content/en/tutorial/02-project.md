# Create a project

Started without a project, Woodcore opens on its start page: the projects opened lately, and three buttons — **Open…**, **New project…** and **Convert an old folder…**.

## New project

Click **New project…**. The window asks for:

- the **location** and the **project folder**, which must be empty;
- the project's **name** and **number**, the **client** and the **address**;
- the **office**, the **author** and the **checker**.

These are printed on the report's title page and in the PDF's metadata. They can be changed at any time in **File › Project properties…**.

## What the folder holds

```text
Halle Nord/
├── Halle Nord.woodcore          the project: this is the file you open
├── Statischer Bericht (typst)/  the report
│   ├── Statischer Rapport.typ   the main document
│   ├── Sections/                one section per file
│   ├── commands.typ             every command of Woodcore
│   └── _woodcore/               the export and the engine — generated, never edited by hand
├── Woodcore-Datei/              what is entered and drawn in Woodcore, the positions included (step 3)
└── _Archiv/                     a zip and a copy of the PDF per export
```

Nothing else needs copying into this folder: wind, snow and permanent loads are entered in Woodcore's tabs and saved in `Woodcore-Datei/loads/` (step 4).

> [!note]
> A project open in a window is **locked** by a file `Halle Nord.woodcore.lock`. If a colleague opens it at the same time, Woodcore says so and offers read-only: two windows saving the same project would lose the first one's work.

## Open a project

A double-click on the `.woodcore` file, **Open…** on the start page, or a `.woodcore` file dropped on the window. Every project opens in a window of its own; **File › Open in a new window…** opens a second one beside it.
