# Export the PDF

**Export PDF** imports the workbooks, then compiles the report: `Statischer Rapport.pdf` is written beside `Statischer Rapport.typ` and opened. If the import fails, nothing is compiled and the previous PDF stays as it was.

## Choose the level and the language

The small arrow beside the button opens a menu of settings; they hold for the exports that follow:

| Setting | Effect |
|---|---|
| **As written (document)** | the level and the language the document itself declares |
| **Base level of detail 1, 2 or 3** | the report's level; a call that sets its own keeps it |
| **Uniform level of detail 1, 2 or 3** | the whole report at that level, even the calls that set one |
| **Document language, de, fr, en** | the language of the words Woodcore prints |

One project thus gives the client's report (uniform 1), the engineer's (base level 2) and the checking engineer's (uniform 3).

## Every export is archived

Every successful export leaves in `_Archiv/` a copy of the PDF and a zip of the state that produced it — the report, the export, the engine, the drawings —, named by date and time. A report handed over long ago is found again as it was.

## From the command line

`woodcore-cli.exe`, in the installation folder, does the same without a window:

```bash
woodcore-cli export --project "Halle Nord.woodcore" --uniform 3 --lang en
```

That is the end of the tutorial. The [command reference](~/docs/) and the [examples](~/examples/) go further.
