"""A project laid out as one report, offered its migration into three documents as it opens (the engineer's request of 30.09.2026; calc/project_migrate.py is the migration itself).

Until the three documents a project was one report, in one folder that was also the Typst root; a project in three documents keeps what the three share at its top and gives each document a folder of its own -- the convention d'utilisation, the base de projet and the report, which is simply the third and keeps every name it had. A project opened in the window that is still laid out as one report is asked once, before the window is built: **«Migrer maintenant»** or **«Plus tard»**.

**What the question says is what the migration will do**, read from project_migrate's own plan and check (`plan`, `check`, `describe`) and never restated: the three folders, in the project's own language, the report's folder renamed and the two new documents made, what moves up to the top of the project, and that nothing is deleted -- a backup and a journal are written first, the report is compared before and after, and a difference undoes everything. Where the project's copy of the engine is not one to replace without asking (`project.ASKED`) the question says it will be replaced first, the migration refusing to run otherwise; where the migration cannot run at all -- a folder already named as one of the three, a Typst missing -- the question says why and offers only «Plus tard». The migration's own English, step by step, is behind «Afficher les détails».

**«Migrer maintenant» runs `woodcore-cli migrate` in a process of its own** (project.cli_command, the command line's route, as «Import données» runs the export), with `--lock-owner` naming this process -- the window's, which holds the project's lock -- and a progress dialog showing the step it is at. A migration that fails is undone by the migration itself, and the project opens as it was. **«Plus tard» is remembered for the project** in the user's settings, so the question is not put again at every opening: the window says it instead, in a banner whose «Migrer…» starts Woodcore again on the project and asks once more (`--migrate`, `forced`).

Never asked of a project opened read-only, and never under `--self-test`, where nobody is there to answer (woodcore_gui.open_project). Qt, and nothing of the migration's own: every write is the command line's.
"""

import os
from pathlib import Path

from PySide6.QtCore import QEventLoop, QProcess, QProcessEnvironment, Qt, QTimer
from PySide6.QtWidgets import QMessageBox, QProgressDialog

import documents
import engine
import proc
import project
import project_migrate
import usersettings

# The projects whose migration the engineer put off, in the user's settings, by project file: asked again only through the banner's «Migrer…» (`forced`).
POSTPONED = "migration_postponed"
# A migration of the engineer's own project took about a minute (its reference, its moves and its proof); one still running after half an hour is stopped, the migration then undoing what it did at its next run's rollback.
TIMEOUT_MS = 30 * 60 * 1000
# What a line of the migration's own log starts with (project_migrate._say): what the progress dialog shows, step by step.
LOG_PREFIX = "migrate: "

STRINGS = {
    "fr": {
        "mg_title": "Migrer en trois documents",
        "mg_intro": "« {name} » est organisé en un seul rapport. Woodcore peut l'organiser en trois documents, chacun dans son dossier :",
        "mg_folder_new": "{folder} — {document}, créé",
        "mg_folder_renamed": "{folder} — {document} : le dossier « {old} », renommé",
        "mg_shared": "Le moteur et l'export et les images passent en tête du projet, partagés par les trois ; config.typ et commands.typ aussi.",
        "mg_safe": "Rien n'est supprimé : les dossiers sont renommés, et une sauvegarde et un journal sont écrits d'abord dans {archives}. Le rapport est comparé avant et après ; au moindre écart, tout est défait. Cela prend une minute environ.",
        "mg_engine_older": "Le moteur de ce projet (Woodcore {detail}) est d'abord remplacé par celui de Woodcore {ours} : le rapport peut s'imprimer différemment ensuite.",
        "mg_engine_unknown": "Le moteur de ce projet, qu'aucun fichier VERSION ne nomme ({detail}), est d'abord remplacé par celui de Woodcore {ours} : le rapport peut s'imprimer différemment ensuite.",
        "mg_engine_edited": "Le moteur copié dans ce projet a été modifié à la main ({detail}) : il est d'abord remplacé par celui de Woodcore {ours}, et ces modifications sont perdues.",
        "mg_now": "Migrer maintenant",
        "mg_later": "Plus tard",
        "mg_refused": "Ce projet ne peut pas être migré pour l'instant :",
        "mg_why_no_report": "son rapport, {report}, est introuvable",
        "mg_why_report_at_top": "son rapport est en tête du projet : il n'a pas de dossier à renommer",
        "mg_why_sources_inside": "les sources de Woodcore ({folder}) sont dans le dossier du rapport, que la migration renomme",
        "mg_why_archives_inside": "les archives ({folder}) sont dans le dossier du rapport, que la migration renomme",
        "mg_why_generated_is_report": "l'export n'a pas de dossier à lui ({folder})",
        "mg_why_collision": "« {path} » existe déjà : renommez-le ou déplacez-le d'abord",
        "mg_why_unrewritable": "{file} : un chemin ne peut pas suivre sa cible ({literal})",
        "mg_why_locked": "le projet est ouvert par {user} sur le poste {host}",
        "mg_why_engine_own": "son export est le dossier du programme lui-même : un projet organisé avant la v0.82 ne peut pas être migré",
        "mg_why_no_typst": "Typst est introuvable : la migration compare le rapport avant et après",
        "mg_why_no_pypdf": "pypdf n'est pas installé : la migration lit les pages du rapport pour les comparer",
        "mg_why_no_template": "le modèle d'un des deux nouveaux documents est introuvable",
        "mg_why_bad_names": "les noms des dossiers ne conviennent pas",
        "mg_why_woodcore_unrewritable": "le fichier du projet ne peut pas être réécrit",
        "mg_running": "Migration de « {name} » en trois documents…",
        "mg_done": "« {name} » est organisé en trois documents.\n\nDans VS Code, ouvrez le dossier du projet (« Ouvrir dans VS Code » le fait) et épinglez comme fichier principal l'entrée du document que vous écrivez (« Typst: Pin the main file ») :\n{entries}",
        "mg_failed": "La migration n'a pas abouti et a été défaite : le projet reste organisé en un seul rapport.\n\n{output}",
        "mg_banner": "Ce projet est organisé en un seul rapport. Migré en trois documents, il écrit aussi la convention d'utilisation et la base de projet.",
        "mg_banner_button": "Migrer…",
        "mg_banner_tip": "Ferme cette fenêtre, rouvre le projet et propose sa migration en trois documents.",
    },
    "de": {
        "mg_title": "In drei Dokumente überführen",
        "mg_intro": "«{name}» ist als ein einziger Bericht angelegt. Woodcore kann ihn in drei Dokumente überführen, jedes in seinem eigenen Ordner:",
        "mg_folder_new": "{folder} — {document}, neu angelegt",
        "mg_folder_renamed": "{folder} — {document}: der Ordner «{old}», umbenannt",
        "mg_shared": "Die Engine und der Export und die Bilder kommen an die Spitze des Projekts, von den dreien geteilt; config.typ und commands.typ ebenso.",
        "mg_safe": "Nichts wird gelöscht: die Ordner werden umbenannt, und zuerst werden eine Sicherung und ein Protokoll in {archives} geschrieben. Der Bericht wird vorher und nachher verglichen; beim kleinsten Unterschied wird alles rückgängig gemacht. Das dauert etwa eine Minute.",
        "mg_engine_older": "Die Engine dieses Projekts (Woodcore {detail}) wird zuerst durch die von Woodcore {ours} ersetzt: der Bericht kann danach anders gedruckt werden.",
        "mg_engine_unknown": "Die Engine dieses Projekts, die keine VERSION-Datei nennt ({detail}), wird zuerst durch die von Woodcore {ours} ersetzt: der Bericht kann danach anders gedruckt werden.",
        "mg_engine_edited": "Die in dieses Projekt kopierte Engine wurde von Hand geändert ({detail}): sie wird zuerst durch die von Woodcore {ours} ersetzt, und diese Änderungen gehen verloren.",
        "mg_now": "Jetzt überführen",
        "mg_later": "Später",
        "mg_refused": "Dieses Projekt kann vorerst nicht überführt werden:",
        "mg_why_no_report": "sein Bericht, {report}, ist nicht zu finden",
        "mg_why_report_at_top": "sein Bericht liegt an der Spitze des Projekts: er hat keinen Ordner, der umbenannt werden könnte",
        "mg_why_sources_inside": "die Quellen von Woodcore ({folder}) liegen im Ordner des Berichts, den die Überführung umbenennt",
        "mg_why_archives_inside": "die Archive ({folder}) liegen im Ordner des Berichts, den die Überführung umbenennt",
        "mg_why_generated_is_report": "der Export hat keinen eigenen Ordner ({folder})",
        "mg_why_collision": "«{path}» gibt es schon: benennen Sie es zuerst um oder verschieben Sie es",
        "mg_why_unrewritable": "{file}: ein Pfad kann seinem Ziel nicht folgen ({literal})",
        "mg_why_locked": "das Projekt ist von {user} auf dem Rechner {host} geöffnet",
        "mg_why_engine_own": "sein Export ist der Ordner des Programms selbst: ein vor v0.82 angelegtes Projekt kann nicht überführt werden",
        "mg_why_no_typst": "Typst ist nicht zu finden: die Überführung vergleicht den Bericht vorher und nachher",
        "mg_why_no_pypdf": "pypdf ist nicht installiert: die Überführung liest die Seiten des Berichts, um sie zu vergleichen",
        "mg_why_no_template": "die Vorlage eines der zwei neuen Dokumente ist nicht zu finden",
        "mg_why_bad_names": "die Namen der Ordner passen nicht",
        "mg_why_woodcore_unrewritable": "die Projektdatei kann nicht neu geschrieben werden",
        "mg_running": "«{name}» wird in drei Dokumente überführt…",
        "mg_done": "«{name}» ist in drei Dokumente überführt.\n\nÖffnen Sie in VS Code den Ordner des Projekts («In VS Code öffnen» tut es) und heften Sie den Einstieg des Dokuments, das Sie schreiben, als Hauptdatei an («Typst: Pin the main file»):\n{entries}",
        "mg_failed": "Die Überführung ist nicht gelungen und wurde rückgängig gemacht: das Projekt bleibt ein einziger Bericht.\n\n{output}",
        "mg_banner": "Dieses Projekt ist als ein einziger Bericht angelegt. In drei Dokumente überführt, schreibt es auch die Nutzungsvereinbarung und die Projektbasis.",
        "mg_banner_button": "Überführen…",
        "mg_banner_tip": "Schliesst dieses Fenster, öffnet das Projekt wieder und bietet seine Überführung in drei Dokumente an.",
    },
    "en": {
        "mg_title": "Migrate into three documents",
        "mg_intro": "“{name}” is laid out as one report. Woodcore can lay it out as three documents, each in a folder of its own:",
        "mg_folder_new": "{folder} — {document}, made",
        "mg_folder_renamed": "{folder} — {document}: the folder “{old}”, renamed",
        "mg_shared": "The engine and the export, and the pictures, move up to the top of the project, shared by the three; config.typ and commands.typ too.",
        "mg_safe": "Nothing is deleted: the folders are renamed, and a backup and a log are written first into {archives}. The report is compared before and after; the least difference undoes everything. It takes about a minute.",
        "mg_engine_older": "This project's engine (Woodcore {detail}) is first replaced by that of Woodcore {ours}: the report may print differently afterwards.",
        "mg_engine_unknown": "This project's engine, which no VERSION file names ({detail}), is first replaced by that of Woodcore {ours}: the report may print differently afterwards.",
        "mg_engine_edited": "The engine copied into this project was edited by hand ({detail}): it is first replaced by that of Woodcore {ours}, and those edits are lost.",
        "mg_now": "Migrate now",
        "mg_later": "Later",
        "mg_refused": "This project cannot be migrated for now:",
        "mg_why_no_report": "its report, {report}, cannot be found",
        "mg_why_report_at_top": "its report lies at the top of the project: it has no folder to rename",
        "mg_why_sources_inside": "Woodcore's sources ({folder}) lie inside the report's folder, which the migration renames",
        "mg_why_archives_inside": "the archives ({folder}) lie inside the report's folder, which the migration renames",
        "mg_why_generated_is_report": "the export has no folder of its own ({folder})",
        "mg_why_collision": "“{path}” is there already: rename or move it first",
        "mg_why_unrewritable": "{file}: a path cannot follow its target ({literal})",
        "mg_why_locked": "the project is open by {user} on the machine {host}",
        "mg_why_engine_own": "its export is the program's own folder: a project laid out before v0.82 cannot be migrated",
        "mg_why_no_typst": "Typst cannot be found: the migration compares the report before and after",
        "mg_why_no_pypdf": "pypdf is not installed: the migration reads the report's pages to compare them",
        "mg_why_no_template": "the template of one of the two new documents cannot be found",
        "mg_why_bad_names": "the folders' names do not do",
        "mg_why_woodcore_unrewritable": "the project file cannot be rewritten",
        "mg_running": "Migrating “{name}” into three documents…",
        "mg_done": "“{name}” is laid out as three documents.\n\nIn VS Code, open the project's folder (“Open in VS Code” does) and pin as the main file the entry of the document you are writing (“Typst: Pin the main file”):\n{entries}",
        "mg_failed": "The migration did not go through and was undone: the project stays laid out as one report.\n\n{output}",
        "mg_banner": "This project is laid out as one report. Migrated into three documents, it writes the service criteria agreement and the basis of design too.",
        "mg_banner_button": "Migrate…",
        "mg_banner_tip": "Closes this window, opens the project again and offers its migration into three documents.",
    },
}


def _t(lang):
    return STRINGS[lang if lang in STRINGS else "en"]


def _key(file):
    return os.path.normcase(str(Path(file).resolve()))


def postponed(here, settings=None):
    """Whether the engineer put off the migration of project `here`."""
    settings = usersettings.read() if settings is None else settings
    kept = settings.get(POSTPONED)
    return isinstance(kept, list) and _key(here.file) in kept


def set_postponed(here, on):
    """Project `here`'s migration put off, or no longer, in the user's settings -- written as they stand on disk, another window or the start page having perhaps written since."""
    settings = usersettings.read()
    kept = [k for k in (settings.get(POSTPONED) or []) if isinstance(k, str) and k != _key(here.file)]
    if on:
        kept.append(_key(here.file))
    if kept:
        settings[POSTPONED] = kept
    else:
        settings.pop(POSTPONED, None)
    usersettings.write(settings)


def prepare(here, lock_owner=None):
    """What migrating `here` would do and what stands in its way, as the migration itself says it -- read, nothing written: (plan, refusals, update_engine, (engine state, detail), skip_data).

    `update_engine` is True where the project's copy of the engine is not one to replace without asking (`project.ASKED`): the migration refuses to run without `--update-engine`, so migrating is agreeing to it, which the question says. `skip_data` where the project has no positions -- neither Woodcore's positions.json (calc/positions_store.py, v0.114) nor a Positionen.xlsx to import -- and so no export worth comparing: the migration then only brings the engine up to date before its reference (`--skip-data`). `lock_owner` is the process holding the project's lock -- this one, which is the window's.
    """
    state, detail = project.engine_state(here)
    update_engine = state in project.ASKED
    try:
        plan = project_migrate.plan(here)
        refusals = project_migrate.check(plan, update_engine=update_engine, lock_owner=os.getpid() if lock_owner is None else lock_owner)
    except (project.ProjectError, OSError) as exc:
        plan = project_migrate.Plan(here=here)
        refusals = [engine.Note("unreadable", str(exc))]
    import positions_store
    return plan, refusals, update_engine, (state, detail), not (here.positions_book.is_file() or positions_store.path(here).is_file())


def refusal_text(note, lang):
    """One reason the migration cannot run, in the window's language by its code (`mg_why_<code>`), else the migration's own English."""
    t = _t(lang)
    key = "mg_why_" + getattr(note, "code", "")
    if key in t:
        try:
            return t[key].format(**getattr(note, "args", {}))
        except (KeyError, IndexError):
            pass
    return str(note)


def message(lang, here, plan, refusals, engine_state):
    """(the question's text, its details) -- what the migration will do, from its own plan, in the window's language; the migration's own description of every move and every rewrite, in English, for «Afficher les détails»."""
    t = _t(lang)
    lines = [t["mg_intro"].format(name=here.name), ""]
    if plan.folders:
        old = here.rel(plan.old_report_dir) if plan.old_report_dir is not None else ""
        language = plan.language or documents.DEFAULT_LANGUAGE
        for mode in project.MODES:
            name = documents.mode_name(mode, language)
            folder = plan.folders.get(mode, "")
            if mode == "rs":
                lines.append("• " + t["mg_folder_renamed"].format(folder=folder, document=name, old=old))
            else:
                lines.append("• " + t["mg_folder_new"].format(folder=folder, document=name))
        lines += ["", t["mg_shared"]]
    state, detail = engine_state
    if state in project.ASKED and not refusals:
        lines += ["", t["mg_engine_" + state].format(detail=detail, ours=project.VERSION)]
    if refusals:
        lines += ["", t["mg_refused"], *("• " + refusal_text(note, lang) for note in refusals)]
    else:
        lines += ["", t["mg_safe"].format(archives=here.layout.get("archives", ""))]
    return "\n".join(lines), "\n".join(project_migrate.describe(plan, refusals))


def ask(parent, lang, text, details, can_migrate):
    """The question itself -- «now» or «later» -- and the one modal of this module a test replaces. Where the migration cannot run there is nothing to agree to, and «Plus tard» is the one button."""
    t = _t(lang)
    box = QMessageBox(QMessageBox.Icon.Question if can_migrate else QMessageBox.Icon.Information, t["mg_title"], text, parent=parent)  # dialog-ok: the migration offered, which waits for its answer
    box.setDetailedText(details)
    now = box.addButton(t["mg_now"], QMessageBox.ButtonRole.AcceptRole) if can_migrate else None
    later = box.addButton(t["mg_later"], QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(now or later)
    box.setEscapeButton(later)
    box.exec()
    return "now" if now is not None and box.clickedButton() is now else "later"


def tell(parent, lang, text, warning=False):
    """What became of the migration, said once: a failure a critical notice, its end an information for the status line of the window that opens next (v0.117: no box)."""
    import notifications
    notifications.report("migration_failed" if warning else "migration_done", text, notifications.CRITICAL if warning else notifications.INFO,
                         source="migration")


def command(here, update_engine=False, skip_data=False, lock_owner=None):
    """The command line the migration is run with, as a program and its arguments: `woodcore-cli migrate --project <file> --lock-owner <pid> [--update-engine] [--skip-data]` (project.cli_command -- woodcore-cli.exe once installed, calc/cli.py from the sources)."""
    args = ["migrate", "--project", str(here.file), "--lock-owner", str(os.getpid() if lock_owner is None else lock_owner)]
    if update_engine:
        args.append("--update-engine")
    if skip_data:
        args.append("--skip-data")
    return project.cli_command(args)


def run(parent, lang, here, update_engine=False, skip_data=False):
    """Runs the migration in a process of its own and waits for it behind a progress dialog showing the step it is at (the lines of its log, `migrate: …`); nothing can be cancelled half-way, a migration stopped half-way being one its own rollback has to undo. Returns (whether it went through, the last lines it wrote to say why not)."""
    t = _t(lang)
    program, arguments = command(here, update_engine=update_engine, skip_data=skip_data)
    process = proc.qprocess()
    environment = QProcessEnvironment.systemEnvironment()
    environment.insert("PYTHONUTF8", "1")
    environment.insert("PYTHONIOENCODING", "utf-8")
    process.setProcessEnvironment(environment)
    process.setWorkingDirectory(str(project.APP_ROOT))
    dialog = QProgressDialog(t["mg_running"].format(name=here.name), None, 0, 0, parent)
    dialog.setWindowTitle(t["mg_title"])
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setAutoReset(False)
    out, err, failed = [], [], []

    def read_out():
        text = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
        out.append(text)
        for line in text.splitlines():
            if line.startswith(LOG_PREFIX):
                dialog.setLabelText(line[len(LOG_PREFIX):])

    def read_err():
        err.append(bytes(process.readAllStandardError()).decode("utf-8", "replace"))

    loop = QEventLoop()
    process.readyReadStandardOutput.connect(read_out)
    process.readyReadStandardError.connect(read_err)
    process.finished.connect(loop.quit)

    def error(kind):
        if kind == QProcess.ProcessError.FailedToStart:   # the one error no `finished` follows
            failed.append(process.errorString())
            loop.quit()

    process.errorOccurred.connect(error)
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(process.kill)
    timer.start(TIMEOUT_MS)
    dialog.show()
    process.start(program, arguments)
    if not failed and process.state() != QProcess.ProcessState.NotRunning:
        loop.exec()
    timer.stop()
    read_out()
    read_err()
    dialog.close()
    ok = not failed and process.exitStatus() == QProcess.ExitStatus.NormalExit and process.exitCode() == 0
    said = "".join(err).strip() or "".join(out).strip() or "; ".join(failed)
    return ok, "\n".join(said.splitlines()[-30:])


def entries_text(here):
    """The three documents' entry files, from the project's folder, one a line: what the engineer pins in Tinymist."""
    return "\n".join(f"• {here.rel(here.document_typ(mode))}" for mode in here.modes)


def offer(parent, lang, here, forced=False):
    """Offers project `here`, laid out as one report, its migration into three documents -- where the engineer has not put it off, or where he asks again (`forced`, the banner's «Migrer…»). Returns what became of it: «migrated» (the project is laid out in three documents now, and is to be read again), «later» (put off, and remembered), «refused» (it cannot run, and says why), «failed» (it ran and was undone) or «postponed» (not asked, having been put off before)."""
    if here.has_modes:
        return "migrated"
    if not forced and postponed(here):
        return "postponed"
    plan, refusals, update_engine, engine_state, skip_data = prepare(here)
    text, details = message(lang, here, plan, refusals, engine_state)
    if ask(parent, lang, text, details, can_migrate=not refusals) != "now":
        set_postponed(here, True)
        return "refused" if refusals else "later"
    ok, output = run(parent, lang, here, update_engine=update_engine, skip_data=skip_data)
    if not ok:
        set_postponed(here, True)
        tell(parent, lang, _t(lang)["mg_failed"].format(output=output), warning=True)
        return "failed"
    set_postponed(here, False)
    try:
        migrated = project.Project.load(here.file)
        entries = entries_text(migrated)
    except project.ProjectError:
        entries = ""
    tell(parent, lang, _t(lang)["mg_done"].format(name=here.name, entries=entries))
    return "migrated"
