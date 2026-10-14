# What's new

What each version of Woodcore brings, what it changes in a report already written, and what to do when moving to it. Read the pages of every version between yours and the new one: the changes add up.

## Updating Woodcore

1. **Install the new version.** Woodcore offers it at its start (**Install**), or download it from the [Download](~/download/) page. It installs **beside** the previous versions, never replacing them.
2. **Open your project.** Woodcore compares the engine copied into the project (`Statischer Bericht (typst)/_woodcore/`) with its own and asks: «This project uses the engine of Woodcore 0.88.0. Update it to 0.89.0?».
   - **Show differences…** shows what changes in the engine's files;
   - **Update** copies the new engine: the new commands become available in the report;
   - **Later** changes nothing; the question comes back at the next opening and at the next export.
3. **Export the PDF and read it through.** A new engine may print a report differently — the layout, a text, a level of detail. The numbers change only where the version's page says so.
4. **Do the «To do» points** of the versions you skipped.

> [!tip]
> A finished project can stay on its version: in **File › Project properties…**, the **Woodcore version** field pins it. A double-click on the project then opens that version, which stays installed.

## Going back

Nothing is lost by updating: every export leaves in `_Archiv/` a zip of the state that produced it, engine included, and the previous versions of Woodcore stay installed. A version is uninstalled on its own, in Windows' **Settings › Apps**.
