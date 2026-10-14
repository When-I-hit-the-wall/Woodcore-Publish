"""Renders one worked example of one Typst command, so Woodcore can show what a command actually prints (docs/typst/command-docs.md §10sexies).

**One example is one document and one run of Typst.** Putting a command's examples on the pages of a single document would be cheaper -- the fixed cost of starting Typst and reading data/ would be paid once instead of three times -- and it would be wrong: `#unit` sets the unit a dimension is printed in *from that line to the end of the document*, and the variable registry `#var` writes into is document-wide too (section 10quinquies). Example 2 of `unit` would then be compiled under example 1's unit table, and the page would not be the page that example produces. Per example also suits the interface, which renders nothing until an arrow is opened.

The page is the report's own: `conf` from config.typ, then a page 16 cm wide -- an A4 less the report's two 2.5 cm margins, which is the measure its text is set to -- and as tall as it needs to be. So the line breaks, the font and the right-hand citation column are the ones the printed page will have, and an example is not a picture of some other document.

**Nothing here imports Qt.** The window drives `typst` through QProcess, as it does for the report's own PDF, and tests/test_commands.py drives it through subprocess; both build the same document and the same argument list from this module, so what the test proves is what the tab shows.

**An example is compiled in examples/, from standard input, and needs no project (v0.81).** Its Typst root is the program's own examples/ folder -- the frozen data, the engine copied beside it, and the documentation's own config.typ -- whatever project is open, and the document is handed to `typst compile -` rather than written anywhere, so a render writes nothing where a project or an installed program keeps its files. Until v0.81 it wrote a .typ into .preview/ under the project's report folder, compiled with that folder as its root, and took the report's own config.typ: the documentation's pages depended on whichever report sat next to the code. Typst's output path is not bound by --root, so the page is written straight into the cache, outside any project, where NextCloud does not sync it.

**An example in the window's language** (`render_localised`): the committed pages are German (build_examples.py), and a French or English page is compiled when it is asked for and kept in the same cache -- the page a report of that language prints, the engine's words by `set-report-language` and Typst's own («Figure», its hyphenation) by `set text(lang:)`. It is the very document the website compiles for its pages in three languages (`document(..., document_language=True)`), so the window and the site cannot come to show one example two ways.
"""

import hashlib
import os
import re
import shutil
from pathlib import Path

import proc  # a child process starts without a console window flashing open (calc/proc.py)
import usersettings  # where Woodcore keeps its caches (usersettings.py)

ROOT = Path(__file__).resolve().parent.parent.parent  # 000-Python/, the program: its lib/ is the engine
# The Typst root of every example: the frozen data, the engine beside it, the documentation's own config.typ (build_examples.py). A document compiled here imports them from the root, "/config.typ" and "/commands.typ", whatever depth nothing is written at.
EXAMPLES = ROOT / "examples"

# Outside the project, beside the settings and the plans' renders -- the v0.48 arrangement (docs/ui/window.md §10quater): NextCloud does not sync it, Git does not version it, and deleting it costs a render.
CACHE_DIR = usersettings.cache_dir("examples")   # %LOCALAPPDATA%\Woodcore\examples, typst-katalog\examples until v0.83
CACHE_BYTES = 100 * 1024 * 1024

PAGE_WIDTH = "16cm"  # A4 less the report's two 2.5 cm margins: the measure the report's own text is set to
PAGE_MARGIN = "6pt"  # not zero: a glyph overhanging its box would be clipped at the edge
PPI = 192            # 2 x 96, so 16 cm comes to ~1210 px -- generous on a HiDPI panel, small on disk
LEVELS = (1, 2, 3)
DEFAULT_LEVEL = 2    # what Statischer Rapport.typ declares as its own base
DIGITS = 3           # what it sets beside it; a preview rounding differently would not be a preview

# Where Typst names a line of the document it compiled: `<stdin>`, reported after the path of the root it was compiled in (`preview.typ`, the file it was written to until v0.81, is still read). Nothing else is moved: a line of lib/ named in the same message is the engine's own.
ERROR_AT_RE = re.compile(r"(?:[^\s│┌─]*[\\/])?(<stdin>|preview\.typ):(\d+)(:\d+)?")

# An example that writes `level: 2` in its own call fixes the level of that line, whatever the report's base level is (docs/typst/report-engine.md §4). `auto` is not a fixed level -- it is the word for "follow the report". Nor is `0` (v0.94): it prints nothing (sections 3.7, 10quinquies), so an example declaring its variables at 0 and printing the line under them at the report's level follows the report -- which is how `var`, `var-unit`, `eq`, `val`, `var-line`, `verify` and `member` show a level 0, by examples of their own, and those are shown at 1 · 2 · 3 like any other. Until v0.94 a `level: 0` pinned them, and they had neither the selector nor their -L1/-L3 pages.
#
# Read here and nowhere else, which is why it lives here rather than in any of its readers: command_docs.example_levels decides from it which levels an example is shown at -- the tab's 1/2/3 selector, the pages build_examples.py renders, the website's level buttons -- and the tab's rule beside a pinned example names the level it matched.
FIXES_LEVEL = re.compile(r"\blevel\s*:\s*(?!(?:auto|0)\b)(\w+)")


def fixes_level(code):
    """The level an example pins in its own call -- the first it writes that prints something --, or None where it follows the report (a `level: 0` pins nothing)."""
    m = FIXES_LEVEL.search(code)
    return m.group(1) if m else None


# Typst's own words -- «Abbildung»/«Figure», the outline's title, the hyphenation -- as a report of each language sets them (config.typ's doc-lang and doc-region, docs/typst/language.md §4bis): a region only where the report has one. The examples' config.typ fixes German, so a page in another language restates them after it.
DOCUMENT_LANGUAGE = {"de": 'lang: "de", region: "CH"', "fr": 'lang: "fr", region: "CH"', "en": 'lang: "en"'}


def preamble(level, lang, config="/config.typ", commands="/commands.typ", document_language=False):
    """The lines before the example: the report's own setup, on a page the size of its text.

    The two import paths default to absolute ones, read from examples/ as the Typst root -- what a document compiled from standard input needs. The frozen MWEs, which are files, pass relative ones computed from where they are written (build_examples.imports_for).

    `document_language` also sets Typst's own language to `lang` (DOCUMENT_LANGUAGE), for a page printed as a report of that language prints it: the website's pages and the window's French and English ones. The committed German pages leave it out, config.typ being German already.
    """
    lines = [
        "// One worked example of one command, written from its /// block in lib/ (docs/typst/command-docs.md §10sexies).",
        "// Generated by calc/tools/build_examples.py -- do not edit: edit the /// block and run it again.",
        f'#import "{config}": conf',
        f'#import "{commands}": *',
        "#show: conf",
    ]
    if document_language:
        lines.append(f"#set text({DOCUMENT_LANGUAGE[lang]})")
    return lines + [
        # conf sets an A4 with a footer and a page number. There is no page here, so both go.
        f"#set page(width: {PAGE_WIDTH}, height: auto, margin: {PAGE_MARGIN}, "
        "header: none, footer: none, numbering: none)",
        f'#set-report-language("{lang}")',
        f"#report-level.update({int(level)})",
        f"#number-digits.update({DIGITS})",
    ]


def document(code, level, lang, config="/config.typ", commands="/commands.typ", document_language=False):
    """The .typ one example is compiled as.

    The level and the language are written into the file rather than passed as --input: those two flags are read by Statischer Rapport.typ, not by the engine, so stating them here is both shorter and one failure mode fewer -- and the file then records what it was rendered at, which is worth having when one looks at it.

    This is the one assembly of an example: the frozen MWEs (build_examples.py), the window's renders and the website's pages in three languages (website/build.py, with `document_language`) are all this document.
    """
    return "\n".join(preamble(level, lang, config, commands, document_language)) + "\n\n" + code.strip("\n") + "\n"


def offset(level=DEFAULT_LEVEL, lang="de", document_language=False):
    """How many lines stand before the example, so a line Typst names can be given back in the example's own numbering."""
    return len(preamble(level, lang, document_language=document_language)) + 1


def in_example(message, level=DEFAULT_LEVEL, lang="de", document_language=False):
    """Typst's message with every line number moved into the example's own numbering, and the path it was compiled in left out.

    Typst names a line of the document it compiled, and that document is an assembly. Without this, an error on the example's first line is reported as line 11 of something the reader never wrote.
    """
    shift = offset(level, lang, document_language)

    def move(m):
        return f"example line {max(int(m.group(2)) - shift, 1)}{m.group(3) or ''}"

    return ERROR_AT_RE.sub(move, message)


def generation():
    """A token that changes whenever anything a rendered example depends on changes: the engine, the documentation's styling, or the frozen data it reads.

    It goes into the cache key, so a re-freeze or an edited engine invalidates every render made before it, without anything having to remember which.
    """
    newest = 0
    watched = [EXAMPLES / "config.typ", EXAMPLES / "commands.typ"]
    watched += sorted((ROOT / "lib").glob("*.typ"))
    watched += sorted((EXAMPLES / "data").rglob("*.json"))
    for path in watched:
        try:
            newest = max(newest, path.stat().st_mtime_ns)
        except OSError:
            continue
    return str(newest)


def cache_key(code, level, lang, token, document_language=False):
    """One rendered example, identified by everything that decides what it looks like -- Typst's own language among it, where the document sets one."""
    digest = hashlib.sha256()
    parts = (code, str(level), lang, token, str(PPI), PAGE_WIDTH) + ((DOCUMENT_LANGUAGE[lang],) if document_language else ())
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:32]


def cached_png(key):
    """The page already rendered for this key, or None."""
    png = CACHE_DIR / f"{key}.png"
    if not png.exists():
        return None
    try:
        os.utime(png)  # its mtime is what prune() reads: least recently *used*, not least recently made
    except OSError:
        pass
    return png


def prune(limit=CACHE_BYTES):
    """Keeps the cache under its limit, the least recently used going first."""
    try:
        pngs = [(p.stat().st_mtime, p.stat().st_size, p) for p in CACHE_DIR.glob("*.png")]
    except OSError:
        return
    total = sum(size for _mtime, size, _p in pngs)
    for _mtime, size, png in sorted(pngs):
        if total <= limit:
            break
        try:
            png.unlink()
        except OSError:
            pass
        total -= size


def typst_args(png):
    """The arguments `typst` is called with to render a document handed on standard input -- by the window through QProcess and by the test through subprocess, so neither can drift from the other.

    PNG and not SVG: Typst writes every glyph as a `<use>` of a `<symbol>`, and QtSvg implements SVG Tiny 1.2, which has no `<symbol>` -- the text would simply not appear (docs/decisions.md §13). There is no `{p}` in the output name because there is exactly one page, and the format is named because the staging name does not end in `.png`.
    """
    Path(png).parent.mkdir(parents=True, exist_ok=True)
    return ["compile", "--root", str(EXAMPLES), "--format", "png", "--ppi", str(PPI), "-", str(png)]


def file_args(source, png):
    """The same, for a frozen MWE, which is a file of examples/."""
    Path(png).parent.mkdir(parents=True, exist_ok=True)
    return ["compile", "--root", str(EXAMPLES), "--format", "png", "--ppi", str(PPI), str(source), str(png)]


def staging_png(key):
    """Where Typst is told to write, before the page is moved into the cache.

    Compiling straight into the cache would let two processes rendering the same example write one path at once. Each stages under a name of its own -- the process id in it, and not ending in `.png`, so prune() never takes a page being written -- and the move is atomic, so a reader of the cache sees a whole page or no page.
    """
    return CACHE_DIR / f"{key}-{os.getpid()}.staging"


def store(staged, key):
    """Moves a freshly rendered page into the cache and gives its path there.

    ⚠️ Two processes rendering the same example arrive here at the same time with the same
    destination, and on Windows the second `os.replace` fails with `Access is denied` -- seen as a
    real failure the first time two suites were run together. Losing that race is not an error: the
    key is the content, so whatever is already there is our page. Take it and drop ours. The raise is
    kept for the case where the move failed and left nothing behind, which is a genuine fault.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    final = CACHE_DIR / f"{key}.png"
    try:
        os.replace(staged, final)
    except OSError:
        Path(staged).unlink(missing_ok=True)
        if not final.exists():
            raise
    return final


def have_typst():
    return shutil.which("typst") is not None


def run_typst(source, png):
    """Compiles one frozen MWE to one .png. Gives None where it worked, and Typst's message where it did not.

    The one blocking call on a file: build_examples.py renders the frozen examples through it. The window never calls it -- it drives its own renders through QProcess so the interface stays answerable.
    """
    result = proc.run(
        ["typst", *file_args(Path(source), Path(png))],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0 or not Path(png).exists():
        return (result.stderr or result.stdout or "").strip() or "typst failed without a message"
    return None


def render_blocking(code, level=DEFAULT_LEVEL, lang="de", use_cache=True, document_language=False):
    """Renders one example and gives (png_path, error).

    Blocking, through subprocess: this is what tests/test_commands.py calls, several at once from a thread pool -- which is safe because nothing is written but each render's own staging page. The window never calls it -- it drives the same arguments through QProcess so the interface stays answerable while Typst runs.
    """
    key = cache_key(code, level, lang, generation(), document_language)
    if use_cache:
        hit = cached_png(key)
        if hit is not None:
            return hit, None
    staged = CACHE_DIR / f"{key}-{os.getpid()}-{os.urandom(4).hex()}.staging"  # a thread pool renders the same key only once, but a name of its own costs nothing
    result = proc.run(
        ["typst", *typst_args(staged)], input=document(code, level, lang, document_language=document_language),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0 or not staged.exists():
        staged.unlink(missing_ok=True)
        return None, in_example((result.stderr or result.stdout or "").strip(), level, lang, document_language)
    png = store(staged, key)
    prune()
    return png, None


def render_localised(code, level=DEFAULT_LEVEL, lang="fr", use_cache=True):
    """The page one example prints in a report of `lang`, compiled on demand against the frozen snapshot and kept in the cache: (png_path, error).

    For a French or English window, whose committed pages are German (build_examples.LANG): the engine's words follow `set-report-language` and Typst's own follow `set text(lang:)` -- the document the website compiles its pages in three languages from. A second call for the same example, level and language is a load from the cache, until the engine, the examples' styling or the snapshot changes (generation()). Blocking: the window's own queue will drive the same document through QProcess.
    """
    if lang not in DOCUMENT_LANGUAGE:
        raise ValueError(f"no report language {lang!r} -- expected one of {', '.join(DOCUMENT_LANGUAGE)}")
    return render_blocking(code, level, lang, use_cache, document_language=True)
