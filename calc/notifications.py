"""Woodcore's notices: every error, warning and information, gathered in one place (spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-010, ARCH-001).

The engineer, 07.10.2026: «Les erreurs ne doivent plus être présentées sous forme de fenêtres popup dispersées dans l'application … Toutes les erreurs doivent être centralisées dans le système global de notifications d'erreurs de Woodcore» · «Les modules de Woodcore doivent pouvoir envoyer une erreur au système central sans avoir à gérer eux-mêmes l'affichage».

A module says what went wrong with `report(...)` -- or `report_note`, `report_exception`, `report_typst` for what it already holds -- and does nothing else: the window shows it (calc/tools/notices_ui.py, the red octagon and the orange triangle at the top right), the log keeps it, a test reads it. No Qt here, so the domain, the export and the command line can report the same way; the window's adapter is what carries a notice raised in a thread over to the window's thread.

**A notice** (`Notice`) carries its `code` -- what kind of trouble it is, and the key of its sentence in the window's glossary --, its `severity` (SEVERITIES), its English `text` (what is printed where no window translates it), the `args` of its sentence, the `technical` text as Typst, Python or a process wrote it (never translated), the `source` that reported it, the `file`, `line` and `column` it is about, when it came (`timestamp`, `last`) and how many times (`count`): the same trouble reported again -- the same code, file, line and technical text -- counts once more rather than piling up.

**Its words** are the window's, looked up when it is shown and again when the language changes: the title `notice_<code>_title`, else the severity's own (`notice_severity_<severity>`); the sentence `notice_<code>`, else `warn_<code>` (an `engine.Note`'s), else the English `text`. An argument that is itself an `engine.Note` is written in the window's language too. The window gives its glossary once, `configure(translate=…)`; nothing here ever raises over a missing word.

**The log**: once `configure(log=…)` is called -- by the window's start, never by a test -- every notice is appended to `%LOCALAPPDATA%\\Woodcore\\woodcore.log`, a diagnosis rather than an archive, started afresh past LOG_LIMIT as stalls.log is; the command line keeps writing its own on standard error.

Deleting a notice takes it out of the window and nothing else: the trouble it named is untouched, and comes back with the operation that met it (the engineer: «La suppression doit uniquement supprimer la notification de l'interface»).
"""

import itertools
import threading
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

# The severities, gravest first. The window shows the first two (🛑 and ⚠); `info` goes to its status line; `success` is kept for when something needs it (T26).
CRITICAL, WARNING, INFO, SUCCESS = "critical", "warning", "info", "success"
SEVERITIES = (CRITICAL, WARNING, INFO, SUCCESS)

# What a notice offers beyond copying and deleting it.
OPEN_FILE = "open_file"

LOG_LIMIT = 512 * 1024


@dataclass
class Notice:
    code: str
    severity: str
    text: str
    args: dict = field(default_factory=dict)
    technical: str = ""
    source: str = ""
    file: str = ""
    line: int = None
    column: int = None
    timestamp: float = field(default_factory=time.time)
    last: float = None
    count: int = 1
    actions: tuple = ()
    key: str = ""          # the glossary key of its sentence, where it is not `notice_<code>` -- a message box's own sentence, converted
    title_key: str = ""    # the glossary key of its title, where it has one of its own
    id: int = 0

    def identity(self):
        """What makes two reports the same trouble."""
        return (self.code, self.severity, self.file, self.line, self.column, self.text, self.technical)

    def where(self):
        if not self.file:
            return ""
        return ":".join(str(part) for part in (self.file, self.line, self.column) if part is not None)


_ids = itertools.count(1)


class Store:
    """The notices of this process, safe to report into from any thread. `listen(callback)` is called with no argument after every change, in the thread that made it."""

    def __init__(self):
        self._lock = threading.RLock()
        self._notices = []
        self._listeners = []

    def listen(self, callback):
        with self._lock:
            self._listeners.append(callback)
        return callback

    def unlisten(self, callback):
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def _changed(self):
        with self._lock:
            listeners = list(self._listeners)
        for callback in listeners:
            try:
                callback()
            except Exception:  # broad: a listener that fails must not lose the notice, nor stop the others
                traceback.print_exc()

    def add(self, notice):
        """`notice` kept -- or, the same trouble already kept, that one counted once more and brought up to date. Returns the notice kept."""
        if notice.severity not in SEVERITIES:
            raise ValueError(f"unknown severity {notice.severity!r}")
        with self._lock:
            identity = notice.identity()
            same = next((n for n in self._notices if n.identity() == identity), None)
            if same is not None:
                same.count += 1
                same.last = notice.timestamp
                same.args = notice.args or same.args
                kept = same
            else:
                notice.id = next(_ids)
                notice.last = notice.timestamp
                self._notices.append(notice)
                kept = notice
        _log(kept)
        self._changed()
        return kept

    def remove(self, notice_id):
        with self._lock:
            before = len(self._notices)
            self._notices = [n for n in self._notices if n.id != notice_id]
            changed = len(self._notices) != before
        if changed:
            self._changed()
        return changed

    def clear(self, severity=None):
        """Every notice taken out of the window -- those of `severity` alone where it is given."""
        with self._lock:
            before = len(self._notices)
            self._notices = [n for n in self._notices if severity is not None and n.severity != severity]
            changed = len(self._notices) != before
        if changed:
            self._changed()
        return changed

    def items(self, severity=None):
        """The notices kept, the latest first; those of `severity` alone where it is given."""
        with self._lock:
            found = [n for n in self._notices if severity is None or n.severity == severity]
        return sorted(found, key=lambda n: (n.last or n.timestamp, n.id), reverse=True)

    def counts(self):
        with self._lock:
            return {severity: sum(n.severity == severity for n in self._notices) for severity in SEVERITIES}

    def get(self, notice_id):
        with self._lock:
            return next((n for n in self._notices if n.id == notice_id), None)


STORE = Store()

_config = {"translate": None, "log": None}
_log_lock = threading.Lock()


def configure(translate=None, log=None):
    """The window's glossary -- `translate(key, lang)` returning the sentence or None -- and the log file, from the window's start (never at import: a test writes no log). A log that cannot be opened is no log."""
    if translate is not None:
        _config["translate"] = translate
    if log is not None:
        try:
            log = Path(log)
            log.parent.mkdir(parents=True, exist_ok=True)
            if log.exists() and log.stat().st_size > LOG_LIMIT:
                log.unlink()
            with open(log, "a", encoding="utf-8", newline="\n") as handle:
                handle.write(f"\n--- Woodcore started {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            _config["log"] = log
        except OSError:
            _config["log"] = None


def _log(notice):
    log = _config["log"]
    if log is None:
        return
    first = (notice.technical or "").strip().splitlines()[:1]
    line = f"{time.strftime('%H:%M:%S', time.localtime(notice.last or notice.timestamp))} {notice.severity} {notice.source or '-'} {notice.code}"
    if notice.where():
        line += f" {notice.where()}"
    line += f": {notice.text}"
    if first:
        line += f" | {first[0]}"
    if notice.count > 1:
        line += f" (x{notice.count})"
    try:
        with _log_lock, open(log, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")
    except OSError:
        pass


def _word(key, lang):
    translate = _config["translate"]
    if translate is None:
        return None
    try:
        return translate(key, lang)
    except Exception:  # broad: a glossary that fails gives the English text, never an error about an error
        return None


def _arg(value, lang):
    code = getattr(value, "code", None)
    if code and hasattr(value, "args"):
        sentence = _word("warn_" + code, lang)
        if sentence:
            try:
                return sentence.format(**{k: _arg(v, lang) for k, v in value.args.items()})
            except (KeyError, IndexError, ValueError):
                pass
    return str(value)


def title(notice, lang):
    """The notice's title in `lang`: its own key's, else its code's, else its severity's, else the code."""
    return ((notice.title_key and _word(notice.title_key, lang)) or _word(f"notice_{notice.code}_title", lang)
            or _word(f"notice_severity_{notice.severity}", lang) or notice.code)


def message(notice, lang):
    """The notice's sentence in `lang`, its arguments filled in -- the English text where the glossary has none, or where its holes do not fit."""
    args = {key: _arg(value, lang) for key, value in (notice.args or {}).items()}
    for key in ([notice.key] if notice.key else []) + [f"notice_{notice.code}", f"warn_{notice.code}"]:
        sentence = _word(key, lang)
        if sentence:
            try:
                return sentence.format(**args)
            except (KeyError, IndexError, ValueError):
                break
    return notice.text


def copy_text(notice, lang, context=None):
    """What «Copier» puts on the clipboard: everything one needs to diagnose the notice -- the user's sentence, the technical text as it was, where, what reported it, when, how often, and `context` (Woodcore's version, the project) -- as plain text one can send to a developer or an AI."""
    lines = [f"[{notice.severity}] {title(notice, lang)} ({notice.code})", message(notice, lang)]
    if notice.where():
        lines.append(f"File: {notice.where()}")
    if notice.source:
        lines.append(f"Source: {notice.source}")
    stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(notice.timestamp))
    lines.append(f"Time: {stamp}" + (f" (x{notice.count})" if notice.count > 1 else ""))
    for name, value in (context or {}).items():
        if value:
            lines.append(f"{name}: {value}")
    if notice.technical:
        lines += ["", notice.technical.rstrip()]
    return "\n".join(lines)


def copy_all(notices, lang, context=None):
    """What «Tout copier» puts on the clipboard (issue #11): every notice of `notices` as `copy_text` writes it, a blank line between two, `context` said once at the end rather than under each."""
    texts = [copy_text(notice, lang) for notice in notices]
    tail = [f"{name}: {value}" for name, value in (context or {}).items() if value]
    return "\n\n".join(texts + (["\n".join(tail)] if tail else []))


# --- notices from another process -----------------------------------------------------------------
# A process Woodcore starts -- the export -- writes its notices on standard error as lines of their own: STRUCTURED_PREFIX and a JSON object (`schema_version`, `severity`, `source`, `code`, `text`, `args`, an argument that is a Note itself in the same form). Only where the window asked for them (STRUCTURED_ENV in the process's environment): run by hand, the process writes its sentences.
STRUCTURED_ENV = "WOODCORE_NOTICES_JSON"
STRUCTURED_PREFIX = "woodcore-notice "
STRUCTURED_SCHEMA = "1.0"


class _Note(str):
    """An `engine.Note` read back from a line: a string with its `code` and `args`, as the window's words expect."""

    def __new__(cls, code, text, args):
        note = super().__new__(cls, text)
        note.code, note.args = code, args
        return note


def _to_json(note):
    code = getattr(note, "code", None)
    if not code:
        return {"text": str(note)}
    return {"code": code, "text": str(note), "args": {key: _to_json(value) if getattr(value, "code", None) else str(value) for key, value in getattr(note, "args", {}).items()}}


def _from_json(value):
    if isinstance(value, dict) and "text" in value:
        if value.get("code"):
            return _Note(value["code"], value["text"], {key: _from_json(arg) for key, arg in (value.get("args") or {}).items()})
        return value["text"]
    return value


def emit(note, severity=WARNING, source="", stream=None):
    """`note` -- an `engine.Note` or a sentence -- written as one structured line on `stream` (standard error)."""
    import json
    import sys
    payload = {"schema_version": STRUCTURED_SCHEMA, "severity": severity, "source": source, **_to_json(note)}
    print(STRUCTURED_PREFIX + json.dumps(payload, ensure_ascii=False), file=stream or sys.stderr, flush=True)


def read_output(output, source="", code="process_output", store=None):
    """What a process wrote on standard error, reported: each structured line a notice of its own, its code and arguments kept; whatever else it wrote -- a traceback, a line of a library -- one warning, the text as it was. Returns the notices kept."""
    import json
    kept, other = [], []
    for line in (output or "").splitlines():
        if line.startswith(STRUCTURED_PREFIX):
            try:
                payload = json.loads(line[len(STRUCTURED_PREFIX):])
            except ValueError:
                other.append(line)
                continue
            if str(payload.get("schema_version", "")).split(".")[0] != STRUCTURED_SCHEMA.split(".")[0]:
                other.append(line)
                continue
            note = _from_json(payload)
            severity = payload.get("severity") if payload.get("severity") in SEVERITIES else WARNING
            kept.append(report_note(note, severity, source=payload.get("source") or source, store=store))
        elif line.strip():
            other.append(line)
    if other:
        text = "\n".join(other)
        kept.append(report(code, text.splitlines()[0], WARNING, args={"first": text.splitlines()[0]}, technical=text, source=source, store=store))
    return kept


# --- reporting -----------------------------------------------------------------------------------

def report(code, text, severity=WARNING, *, args=None, technical="", source="", file="", line=None, column=None, actions=(), key="", title_key="", store=None):
    """One notice reported: `code` its kind (and its sentence's key, `notice_<code>`, unless `key` names another), `text` its sentence as the caller has it -- English, or already in the window's language where the caller wrote it so --, `args` what fills the sentence's holes (written as text now: a notice outlives what it was about). Returns the notice kept. A file named offers to be opened."""
    if file and OPEN_FILE not in actions:
        actions = tuple(actions) + (OPEN_FILE,)
    args = {k: v if getattr(v, "code", None) else ("" if v is None else str(v)) for k, v in (args or {}).items()}
    notice = Notice(code=code, severity=severity, text=str(text), args=args, technical=technical or "", source=source,
                    file=str(file or ""), line=line, column=column, actions=tuple(actions), key=key, title_key=title_key)
    return (store or STORE).add(notice)


def report_note(note, severity=WARNING, source="", store=None, **fields):
    """A domain module's warning (`engine.Note`, or a plain string) reported as it is: its code and arguments kept, so the window writes it in its own language."""
    code = getattr(note, "code", None) or "note"
    return report(code, str(note), severity, args=getattr(note, "args", None), source=source, store=store, **fields)


def report_exception(exc, source="", code="exception", severity=CRITICAL, store=None, tb=None):
    """An exception reported with its whole traceback as the technical text, and the innermost frame of Woodcore's own code as its place."""
    tb = tb if tb is not None else exc.__traceback__
    technical = "".join(traceback.format_exception(type(exc), exc, tb))
    frames = traceback.extract_tb(tb) if tb is not None else []
    own = [f for f in frames if "site-packages" not in f.filename and "\\Lib\\" not in f.filename and "/lib/python" not in f.filename]
    frame = (own or frames or [None])[-1]
    return report(code, f"{type(exc).__name__}: {exc}", severity, args={"error": f"{type(exc).__name__}: {exc}"}, technical=technical, source=source,
                  file=frame.filename if frame else "", line=frame.lineno if frame else None, store=store)


def report_typst(output, source="", code="typst_error", root=None, error_severity=CRITICAL, args=None, store=None):
    """Every diagnostic of Typst's `output` reported: an error at `error_severity` (critical where it stopped what was asked), a warning as a warning; a path relative to `root` made absolute, so it can be opened. Output with no diagnostic in it -- a crash, a timeout -- is one notice of its own. Returns the notices kept."""
    import typst_diagnostics
    found = typst_diagnostics.parse(output)
    kept = []
    for diagnostic in found:
        path = diagnostic.file
        if path and root is not None and not Path(path).is_absolute():
            path = str(Path(root) / path)
        severity = error_severity if diagnostic.severity == "error" else WARNING
        kind = code if diagnostic.severity == "error" else "typst_warning"
        values = {"message": diagnostic.message, **(args or {})}
        kept.append(report(kind, f"Typst {diagnostic.severity}: {diagnostic.message}", severity, args=values, technical=diagnostic.raw,
                           source=source, file=path, line=diagnostic.line, column=diagnostic.column, store=store))
    if not found and (output or "").strip():
        kept.append(report(code, "Typst failed", error_severity, args={"message": (output or "").strip().splitlines()[0], **(args or {})},
                           technical=output.strip(), source=source, store=store))
    return kept
