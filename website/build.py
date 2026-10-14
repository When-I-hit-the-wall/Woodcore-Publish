"""Builds Woodcore's website: what Woodcore is, where to download it, how to begin, and every command of the report with its worked examples, in French, German and English (docs/conventions/build-and-release.md §12, v0.89).

    python website/build.py                      the site into public/, the examples as vector pages (Typst on PATH)
    python website/build.py --images png         the examples as the committed PNG pages instead -- no Typst needed
    python website/build.py --serve              and then serve it on http://localhost:8000/ to look at it
    python website/build.py --fetch-installer    and check the published installer, downloaded from its Release on GitHub (what the CI does)
    python website/build.py --installer dist/Woodcore-0.117.0-setup.exe   and check that local installer instead (a preview)

Cloudflare Pages serves it at https://woodcore.pages.dev/ (website/site.json's base_url), built and published by .github/workflows/site.yml on every push to the default branch. The build **exits with 1** where something the site must not go out without is wrong -- an installer that is not the one releases.json records, a file Cloudflare Pages would refuse -- and the workflow then does not deploy: a deployment replaces the one that is live, and a site without its download and its version.json would erase theirs.

**Nothing here is written twice.** The reference is read where Woodcore's commands tab reads it (section 10sexies): the `///` blocks of lib/ through build_reference, their French and German through command_docs (calc/i18n/commands.json), the calls to copy through build_reference's call_complete/call_minimal filled from the frozen snapshot (examples/data/), and the worked examples are the very fences the tab compiles. The order of the categories is build_reference.CATEGORIES', their names, the line introducing each and the words the reference says beside every command («Arguments», «Appel minimal», «Exemple 1») are calc/i18n/reference.json's (command_docs.category_label, command_docs.word), which Woodcore's commands tab reads too; which levels an example is shown at is command_docs.example_levels', which build_examples.py reads; an example's page is compiled from command_preview.document, the window's own assembly; and the code the home page shows is the fence of the example it shows. What the site adds is arrangement -- the pages, the navigation, the search -- and its own prose, which is in website/content/<lang>/ (the tutorial, the download page and the changes between versions, Markdown) and website/strings.json (everything else).

**The navigation beside a page depends on what the page is** (the engineer's decision): a page of the commands carries the search and the commands by category, a step of the tutorial the search, the tutorial's steps and one link to the reference, a page of what changed the list of versions, and the gallery of examples none, laid out at the width of the home page. On a narrow screen, where the bar at the top hides its links behind ☰, the sidebar carries them.

**What changes from one version to the next** (v0.89, the engineer: «des informations sur les changements entre mises à jour et ce que cela signifie pour le user»). `content/<lang>/changes/<version>.md` is one page per version a user can have installed -- what is new, what moves in a report already written, and what to do, with the calls and the examples -- and `content/<lang>/changes.md` the page that says how to update at all. They are written by hand, like the tutorial: what a change *means* for a report is not something the code can say. The update window links to the page of the version it announces (`changes` in version.json).

**The examples are vector pages here, not the committed PNGs.** A browser reads SVG with `<symbol>` and `<use>`, which QtSvg cannot (section 10sexies), so each example is compiled once more, to SVG, from its fence -- against the frozen snapshot, through the frozen engine copy, as the PNGs were -- and its numbers rounded to a hundredth of a point and its layout whitespace removed: 29 MB of pages come to about 15 MB, every file of them far under the 25 MiB Cloudflare Pages takes (the installer, 95 MB, is not in the site: it is a Release on GitHub). The PNGs remain the fallback where no Typst is at hand (`--images png`), level 2 only for the same reason.

**Every example is shown in the page's language** (v0.89, the engineer: «tous les exemples … disponibles en 3 langues»): compiled three times, with `set-report-language` and Typst's own `text(lang:)` set to the page's, where Woodcore's window showed them in German until v0.94. A page the three languages print alike -- a formula, a number -- is stored once, its file named after its content, which keeps three languages to about 1.4 times the weight of one. The PNG fallback is German.

**What is not published** (website/site.json, `masked`): the example pages that set a norm table in full -- SIA 261 Tabelle 8 and SIA 265 Tabellen 24 to 41 -- the engineer's choice for a site anyone can read. Their code and calls stay, their picture is a note.

**An address that moved keeps working** (website/site.json, `moved`, v0.96): a page renamed -- the tutorial's step on the window was `tutorial/katalog/` until the Katalog became Woodcore, and is `tutorial/window/` -- leaves at its old address, in every language, a small page that sends the reader on, so a link kept in a bookmark, an e-mail or an older program still arrives. The next rename is one line of site.json.

**The installer and version.json.** website/releases.json lists the published versions, newest first, each with its notes in three languages and, once packaging/publish.py has uploaded it, its installer's file name, size, SHA-256, where it is kept (`hosted`) and its public address (`url`, written there and nowhere else). The installer is **never put in the site**: Cloudflare Pages takes no file over 25 MiB. Where the newest one kept on GitHub (`hosted`: "github") is downloaded from that address -- by calc/tools/updates.py's own `download`, which an installed Woodcore uses too -- or given with --installer, and matches its size and SHA-256, the site links to it and writes `version.json`, the manifest every installed Woodcore reads at its start. Where none is kept on GitHub yet, the site is built all the same, says the download is not published yet, and writes no manifest: no Woodcore is told of a version it could not download. Where one is and the check fails (`--fetch-installer`), the build fails and the workflow does not deploy. The versions published before v0.117 (`hosted`: "gitlab") stay in GitLab's registry, which is no longer updated: the site neither fetches nor offers them, but their notes and their page of changes remain.
"""

import argparse
import fnmatch
import hashlib
import html
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT / "calc" / "tools"), str(ROOT / "calc")]

import build_examples as bex  # noqa: E402
import build_reference as ref  # noqa: E402
import command_docs as docs  # noqa: E402
import command_preview as preview  # noqa: E402
import project  # noqa: E402
import theme  # noqa: E402  -- the colours and the fonts, which dress Woodcore's window too: site.css's tokens are written in from them (v0.90)
import typst_syntax  # noqa: E402  -- how a Typst call is cut into what gets a colour, in Woodcore's window too (v0.92)
import updates  # noqa: E402  -- the installed program's own download and its rule for where an installer may come from: the build checks the installer with them (v0.117)

LANGS = ("fr", "de", "en")
CONFIG = json.loads((HERE / "site.json").read_text(encoding="utf-8"))
STRINGS = json.loads((HERE / "strings.json").read_text(encoding="utf-8"))
RELEASES = HERE / "releases.json"
CONTENT = HERE / "content"
LEGAL = ROOT / "legal"   # the licence in three languages and the third-party notices, published under legal/ (packaging/notices.py writes the notices)
LEGAL_FILES = ("LICENSE-fr.txt", "LICENSE-de.txt", "LICENSE-en.txt", "licenses/GPL-3.0.txt", "THIRD-PARTY-NOTICES.txt")   # the GPL's own text beside the three presentations of it, under the path they name
ASSETS = HERE / "assets"
ICON = ROOT / "calc" / "tools" / "woodcore.svg"
SCRATCH = bex.EXAMPLES / ".site"   # the MWEs compiled to SVG, beside the frozen engine they import (gitignored)
MANIFEST_SCHEMA = "1.0"            # calc/tools/updates.py's SCHEMA_VERSION, held equal by tests/test_site.py
FILE_LIMIT = 25 * 2**20            # Cloudflare Pages' largest file (the free plan, a deployment by wrangler)
FILES_LIMIT = 20_000               # and its most files
HOSTED = ("github", "gitlab")      # where website/releases.json says an installer is kept; packaging/publish.py writes "github"
# What the style, the script and the search index are asked for with, `site.css?v=…`: a browser keeps them for a while, and a site rebuilt with another would otherwise be read with the old one. The hash of what changes them -- the two files, the words, the content, the /// blocks of lib/.
ASSET_STAMP = hashlib.sha256(b"".join(
    p.read_bytes() for p in sorted([*ASSETS.iterdir(), theme.TOKENS_FILE, HERE / "strings.json", *CONTENT.rglob("*.md"), *(ROOT / "lib").glob("*.typ"), docs.PATH, docs.REFERENCE_PATH])
    if p.is_file())).hexdigest()[:10]

# The categories the site lists, in the one order both the site and Woodcore's window follow (build_reference.CATEGORIES); the engine's internals are not a reader's business here.
CATEGORY_KEYS = [key for key, _names in ref.CATEGORIES]

# The sections of the site, as the bar at the top links them -- and the sidebar, on a screen too narrow for that bar's links.
SECTIONS = (("docs", "nav_docs", "docs/"), ("tutorial", "nav_tutorial", "tutorial/"),
            ("examples", "nav_examples", "examples/"), ("changes", "nav_changes", "changes/"))


# The line of assets/site.css its tokens are written in at: every colour, the radius and the two font stacks live in calc/tools/theme.json, which Woodcore's window builds its palette and style sheet from too (v0.90), so the site and the window cannot come to show two teals.
TOKENS_MARKER = re.compile(r"^/\* @tokens\b.*?\*/$", re.M)


def site_css(path=ASSETS / "site.css"):
    """assets/site.css with theme.json's tokens written in where its marker stands."""
    text = path.read_text(encoding="utf-8")
    if len(TOKENS_MARKER.findall(text)) != 1:
        raise ValueError(f"{path.name}: expected one /* @tokens ... */ line, found {len(TOKENS_MARKER.findall(text))}")
    return TOKENS_MARKER.sub(lambda _m: theme.css_tokens().rstrip("\n"), text)


# --- words ------------------------------------------------------------------------------------------------------

def t(lang, key, **values):
    text = STRINGS[lang].get(key)
    if text is None:
        raise KeyError(f"website/strings.json: no '{key}' in {lang}")
    return text.format(**values) if values else text


def rw(lang, key, **values):
    """One of the reference's own words -- «Commandes», «Arguments», «Exemple {n}» -- which the site and Woodcore's commands tab say alike: calc/i18n/reference.json, through command_docs."""
    return docs.word(key, lang, **values)


def esc(text):
    return html.escape(str(text), quote=True)


def prose_html(text):
    """A paragraph of a /// block, as Woodcore's window sets it: code in <code>, **bold**, *italic*, the rest escaped (command_docs.prose)."""
    return docs.prose(text, lambda code: f"<code>{html.escape(code)}</code>",
                      lambda words: html.escape(words, quote=False), r"<strong>\1</strong>", r"<em>\1</em>")


def prose_plain(text):
    return docs.prose(text, lambda code: code, lambda words: words, r"\1", r"\1")


# --- Typst, highlighted -----------------------------------------------------------------------------------------

# The tokeniser is calc/tools/typst_syntax.py's, which Woodcore's window colours its calls with too (v0.92); this file's own copy read `#show` as a keyword inside `#show-calc`.
TYPST_TOKEN = typst_syntax.TYPST_TOKEN


def highlight(code, lang="typ"):
    """Code as HTML, Typst's syntax coloured the way typst.app colours it: comments, strings and raw blocks, calls, named arguments, numbers."""
    if lang not in ("typ", "typst", "typ-dry"):
        if lang in ("bash", "sh", "powershell", "ps"):
            return re.sub(r"(^|\n)(#[^\n]*)", lambda m: m.group(1) + f'<span class="c">{m.group(2)}</span>', html.escape(code))
        return html.escape(code)
    out, pos = [], 0
    for m in TYPST_TOKEN.finditer(code):
        out.append(html.escape(code[pos:m.start()]))
        kind = m.lastgroup
        cls = typst_syntax.SITE_CLASS[kind]
        out.append(f'<span class="{cls}">{html.escape(m.group())}</span>')
        pos = m.end()
    out.append(html.escape(code[pos:]))
    return "".join(out)


def code_block(code, lang="typ", copy_label="", extra_class=""):
    """A code block with its copy button."""
    button = f'<button class="copy" type="button" data-copy aria-label="{esc(copy_label)}">{esc(copy_label)}</button>' if copy_label else ""
    return (f'<div class="code {extra_class}">{button}'
            f'<pre><code class="lang-{esc(lang)}">{highlight(code, lang)}</code></pre></div>')


# --- Markdown, the little the content needs ---------------------------------------------------------------------

INLINE_CODE = re.compile(r"`([^`]+)`")
LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)")
STRONG = re.compile(r"\*\*(.+?)\*\*")
EMPH = re.compile(r"(?<![\w*])\*(?=\S)([^*]+?)(?<=\S)\*(?![\w*])")
KBD = re.compile(r"\[\[([^\]]+)\]\]")


def inline(text, page):
    """One line of Markdown: `code`, **bold**, *italic*, [[key]], [links](~/docs/var/) and images -- a target starting with `~/` is this language's, one starting with `/` the site's root."""
    spans = []

    def park(value):
        spans.append(value)
        return f"\x00{len(spans) - 1}\x00"

    text = INLINE_CODE.sub(lambda m: park(f"<code>{html.escape(m.group(1))}</code>"), text)

    def link(m):
        bang, label, target = m.groups()
        url = page.link(target)
        if bang:
            return park(f'<img src="{esc(url)}" alt="{esc(label)}" loading="lazy">')
        external = target.startswith("http")
        attrs = ' rel="noopener" target="_blank"' if external else ""
        return park(f'<a href="{esc(url)}"{attrs}>') + label + park("</a>")

    text = LINK.sub(link, text)
    text = html.escape(text, quote=False)
    text = KBD.sub(lambda m: f"<kbd>{m.group(1)}</kbd>", text)
    text = STRONG.sub(r"<strong>\1</strong>", text)
    text = EMPH.sub(r"<em>\1</em>", text)
    return re.sub("\x00(\\d+)\x00", lambda m: spans[int(m.group(1))], text)


def slugify(text):
    import unicodedata
    text = unicodedata.normalize("NFKD", prose_plain(text)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"


def markdown(text, page):
    """Markdown to HTML: headings (their ids collected for the page's table of contents), paragraphs, lists, fenced code, block quotes as notes, tables, and `{{example stem}}` -- a worked example set as the reference sets it. Returns (html, [(level, id, title)])."""
    lines = text.replace("\r\n", "\n").split("\n")
    out, toc, i = [], [], 0
    para = []

    def flush():
        if para:
            out.append(f"<p>{inline(' '.join(para), page)}</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            lang = stripped[3:].strip() or "text"
            body = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            out.append(code_block("\n".join(body), lang, t(page.lang, "copy")))
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            flush()
            level, title = len(m.group(1)), m.group(2)
            anchor = slugify(title)
            if level == 1:
                out.append(f"<h1>{inline(title, page)}</h1>")
            else:
                toc.append((level, anchor, prose_plain(re.sub(r"`", "", title))))
                out.append(f'<h{level} id="{anchor}"><a class="anchor" href="#{anchor}" aria-hidden="true">#</a>{inline(title, page)}</h{level}>')
            i += 1
            continue
        m = re.match(r"^\{\{example\s+([\w.+-]+)\}\}$", stripped)
        if m:
            flush()
            out.append(page.site.example_card(m.group(1), page))
            i += 1
            continue
        if stripped == "{{download}}":
            flush()
            out.append(page.site.download_card(page))
            i += 1
            continue
        if re.match(r"^([-*]|\d+\.)\s+", line):   # a list starts at column 0; the loop below would never pass an indented first item
            flush()
            ordered = bool(re.match(r"^\d+\.", stripped))
            # One level of nesting: an item at column 0, the items indented under it, and the indented lines that carry on
            # the one or the other -- under a sub-list, a line indented as its parent's text carries on the parent, after the sub-list.
            items = []
            while i < len(lines):
                raw = lines[i]
                item = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", raw)
                if item and not item.group(1):
                    items.append({"text": item.group(3), "children": [], "child_ordered": False, "after": ""})
                elif item and items:
                    items[-1]["children"].append(item.group(3))
                    items[-1]["child_ordered"] = item.group(2)[0].isdigit()
                elif raw.startswith("  ") and raw.strip() and items:
                    indent = len(raw) - len(raw.lstrip())
                    if items[-1]["children"] and indent >= 4:
                        items[-1]["children"][-1] += " " + raw.strip()
                    elif items[-1]["children"]:
                        items[-1]["after"] += " " + raw.strip()
                    else:
                        items[-1]["text"] += " " + raw.strip()
                else:
                    break
                i += 1
            tag = "ol" if ordered else "ul"
            html_items = []
            for item in items:
                sub = ""
                if item["children"]:
                    sub_tag = "ol" if item["child_ordered"] else "ul"
                    sub = f"<{sub_tag}>" + "".join(f"<li>{inline(child, page)}</li>" for child in item["children"]) + f"</{sub_tag}>"
                after = f"<p>{inline(item['after'].strip(), page)}</p>" if item["after"].strip() else ""
                html_items.append(f"<li>{inline(item['text'], page)}{sub}{after}</li>")
            out.append(f"<{tag}>" + "".join(html_items) + f"</{tag}>")
            continue
        if stripped.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            kind = "note"
            if quote and re.match(r"^\[!(\w+)\]$", quote[0]):
                kind = quote.pop(0)[2:-1].lower()
            paragraphs, current = [], []
            for q in quote + [""]:
                if q:
                    current.append(q)
                elif current:
                    paragraphs.append(" ".join(current))
                    current = []
            out.append(f'<div class="callout {esc(kind)}">' + "".join(f"<p>{inline(p, page)}</p>" for p in paragraphs) + "</div>")
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?\s*:?-{3,}", lines[i + 1].strip()):
            flush()
            head = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append('<div class="table-wrap"><table><thead><tr>' + "".join(f"<th>{inline(c, page)}</th>" for c in head)
                       + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{inline(c, page)}</td>" for c in row) + "</tr>" for row in rows)
                       + "</tbody></table></div>")
            continue
        if not stripped:
            flush()
        else:
            para.append(stripped)
        i += 1
    flush()
    return "\n".join(out), toc


# --- SVG, smaller ------------------------------------------------------------------------------------------------

LONG_NUMBER = re.compile(r"-?\d+\.\d{3,}")


def _rounded(match):
    text = f"{float(match.group()):.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def minify_svg(text):
    """Typst's SVG, lighter and drawn the same: its numbers rounded to a hundredth of a point (a thirtieth of a pixel on the page), the whitespace between its tags and the class names nothing styles removed. A number inside an embedded image's base64 carries no dot, so it is never touched."""
    text = re.sub(r">\s+<", "><", text)
    text = LONG_NUMBER.sub(_rounded, text)
    for attribute in (' class="typst-text"', ' class="typst-group"', ' class="typst-shape"', ' class="typst-image"', ' fill-rule="nonzero"', ' x="0" y="0"'):
        text = text.replace(attribute, "")
    # The rest is lossless and is what keeps three languages under Pages' 100 MB (v0.89): path data written as SVG allows it
    # (no space around a command letter or before a minus, no leading zero), Typst's 32-digit glyph ids made short -- an id
    # is local to its file --, the default y and black of a glyph's <use> left out, and `href` for SVG 1.1's `xlink:href`.
    text = re.sub(r' d="([^"]*)"', lambda m: ' d="' + _compact_path(m.group(1)) + '"', text)
    ids = {}

    def short(match):
        return ids.setdefault(match.group(1), "g" + format(len(ids), "x"))

    text = GLYPH_ID.sub(short, text)
    text = re.sub(r'(<use [^>]*?) y="0"', r"\1", text)
    text = re.sub(r'(<use [^>]*?) fill="#000000"', r"\1", text)
    text = text.replace('fill="#000000"', 'fill="#000"').replace('fill="#ffffff"', 'fill="#fff"').replace("xlink:href=", "href=")
    return text


GLYPH_ID = re.compile(r"\b(g[0-9A-F]{32})\b")


def _compact_path(d):
    """One path's data, the same path: no space around a command letter or before a minus, `.5` for `0.5`."""
    d = re.sub(r"\s*([A-Za-z])\s*", r"\1", d)
    d = re.sub(r"(?<![\d.])0\.(\d)", r".\1", d)
    d = d.replace("-0.", "-.")
    d = re.sub(r"\s+-", "-", d)
    return re.sub(r"\s+", " ", d).strip()


# --- the pages --------------------------------------------------------------------------------------------------

class Page:
    """One HTML page of the site: where it is written, in which language, and how it links to the rest."""

    def __init__(self, site, lang, path, section):
        self.site, self.lang, self.path, self.section = site, lang, path, section

    def url(self, target):
        """A site-root path (`fr/docs/`, `img/x.svg`, `` for the root) as a link relative to this page."""
        base = posixpath.dirname(self.path)
        rel = posixpath.relpath(target or ".", base or ".")
        if (target == "" or target.endswith("/")) and not rel.endswith("/"):
            rel = "./" if rel == "." else rel + "/"
        return rel

    def link(self, target):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            return target
        if target.startswith("~/"):
            return self.url(f"{self.lang}/{target[2:]}")
        return self.url(target.lstrip("/"))

    def root(self):
        return self.url("") or "./"


class Site:
    def __init__(self, out, images="svg", installer=None, fetch_installer=False, jobs=None):
        self.out = Path(out)
        self.images = images
        self.installer_source = Path(installer) if installer else None
        self.fetch_installer = fetch_installer
        self.jobs = jobs or max(2, (os.cpu_count() or 4))
        self.written = 0
        self.warnings = []
        self.notices = []       # what is worth saying and is not wrong
        self.errors = []        # what the site must not go out with: main() exits with 1 (and the workflow does not deploy)
        self.samples = ref.sample_arguments(bex.EXAMPLES / "data")
        self.commands = self._commands()
        self.by_name = {c["name"]: c for c in self.commands}
        self.examples = {e["stem"]: e for c in self.commands for ex in c["examples"] for e in ex["variants"].values()}
        self.releases = json.loads(RELEASES.read_text(encoding="utf-8"))["releases"]
        self.published = None   # the release whose installer is in the site
        self.images_of = {}     # (example, language) -> its page, filled by render_examples
        self.compiled, self.failures = 0, []
        self.moved = []         # the pages that only send the reader on to where a page moved (site.json's `moved`)
        self.tutorial = {lang: self._tutorial(lang) for lang in LANGS}
        self.changes = {lang: self._changes(lang) for lang in LANGS}

    # -- what the reference reads --

    def _commands(self):
        records = {r["name"]: r for r in ref.lib_bindings(ROOT)}
        commands = []
        for key in CATEGORY_KEYS:
            for name in dict(ref.CATEGORIES)[key]:
                record = records.get(name)
                if record is None:
                    continue
                block = ref.parse_doc_block(record["doc_lines"])
                examples = []
                for index, example in enumerate(block["examples"]):
                    variants = {}
                    for level in docs.example_levels(record, block, example):   # the levels Woodcore's window and build_examples.py show it at
                        stem = bex.stem(name, index, level)
                        variants[level] = {"stem": stem, "command": name, "index": index, "level": level,
                                           "code": example["code"], "masked": self.masked(stem)}
                    examples.append({"index": index, "code": example["code"], "render": example["render"], "variants": variants})
                commands.append({**record, "block": block, "examples": examples,
                                 "defaults": dict(ref.split_params(record["params"] or ""))})
        return commands

    @staticmethod
    def masked(stem):
        return any(fnmatch.fnmatch(stem, pattern) for pattern in CONFIG["masked"])

    def localised(self, command, lang):
        if lang == "en":
            return command["block"], 0
        return docs.localise(command["name"], command["block"], lang)

    def _tutorial(self, lang):
        pages = []
        for path in sorted((CONTENT / lang / "tutorial").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), path.stem)
            slug = re.sub(r"^\d+-", "", path.stem)
            pages.append({"slug": slug, "title": title, "text": text, "file": path})
        return pages

    def _changes(self, lang):
        """The pages of what changed, one per version, the newest first: `content/<lang>/changes/<version>.md`."""
        pages = []
        for path in (CONTENT / lang / "changes").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), path.stem)
            pages.append({"version": path.stem, "title": title, "text": text, "file": path})
        return sorted(pages, key=lambda p: version_tuple(p["version"]), reverse=True)

    def change_page(self, lang, version):
        """The address of what `version` changes, in `lang`, or None where no page says it."""
        return f"{lang}/changes/{version}/" if any(p["version"] == version for p in self.changes[lang]) else None

    # -- writing --

    def write(self, rel, text):
        target = self.out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
        self.written += 1

    def build(self):
        # emptied rather than removed: a server showing the site (--serve, .claude/launch.json) keeps its folder
        self.out.mkdir(parents=True, exist_ok=True)
        for child in self.out.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        self.copy_assets()
        self.render_examples()
        self.place_installer()
        for lang in LANGS:
            self.page_home(lang)
            self.page_download(lang)
            self.page_docs_index(lang)
            for command in self.commands:
                self.page_command(lang, command)
            self.page_examples(lang)
            for position in range(len(self.tutorial[lang])):
                self.page_tutorial(lang, position)
            self.page_tutorial_index(lang)
            self.page_changes_index(lang)
            self.page_legal(lang)
            for position in range(len(self.changes[lang])):
                self.page_change(lang, position)
            self.write(f"search/{lang}.json", json.dumps(self.search_index(lang), ensure_ascii=False, separators=(",", ":")))
        for old, new in CONFIG.get("moved", {}).items():   # after every page, so that what a moved page leads to is there to be checked
            for lang in LANGS:
                self.page_moved(lang, old, new)
        self.page_root()
        self.page_404()
        self.write_manifest()
        return self.report()

    def copy_assets(self):
        for path in ASSETS.iterdir():
            if path.is_file():
                (self.out / "assets").mkdir(parents=True, exist_ok=True)
                if path.name == "site.css":
                    self.write("assets/site.css", site_css(path))
                else:
                    shutil.copy2(path, self.out / "assets" / path.name)
        shutil.copy2(ICON, self.out / "assets" / "logo.svg")
        for name in LEGAL_FILES:
            (self.out / "legal" / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(LEGAL / name, self.out / "legal" / name)

    # -- the examples --

    def image_path(self, stem, lang):
        """Where the page of example `stem` in `lang` is, from the site's root -- None where there is none."""
        return self.images_of.get((stem, lang))

    def image_exists(self, stem, lang):
        return self.image_path(stem, lang) is not None

    def render_examples(self):
        """Every published example compiled in each of the three languages, as the report of that language prints it (the engine's words by `set-report-language`, Typst's by `set text(lang:)`): command_preview.document with its document language, the assembly Woodcore's window compiles a French or English page from (render_localised).

        An example whose three pages are the same -- a formula, a number, nothing the engine or Typst words -- is stored once: each page is named after its content (`img/<stem>-<hash>.svg`), so identical pages are one file, which is what keeps three languages from tripling the site. `self.images_of` maps (stem, language) to the file.
        """
        self.images_of = {}
        wanted = [e for e in self.examples.values() if not e["masked"]]
        (self.out / "img").mkdir(parents=True, exist_ok=True)
        if self.images == "png":
            # the committed pages are German and level 2 alone: every language shows them, and the build says so
            for entry in wanted:
                if entry["level"] != preview.DEFAULT_LEVEL:
                    continue   # the level variants stay out of the PNG fallback: they would double its weight
                source = bex.OUT / f"{entry['stem']}.png"
                if source.is_file():
                    shutil.copy2(source, self.out / "img" / source.name)
                    for lang in LANGS:
                        self.images_of[(entry["stem"], lang)] = f"img/{source.name}"
                else:
                    self.warnings.append(f"no committed page for {entry['stem']}")
            self.warnings.append("the PNG fallback shows every example in German, the language of the committed pages")
            return
        typst = os.environ.get("TYPST") or shutil.which("typst")
        if typst is None:
            raise SystemExit("website/build.py: typst is not on PATH -- install Typst 0.14, or build with --images png")
        bex.refresh_engine()
        SCRATCH.mkdir(parents=True, exist_ok=True)
        config, commands = bex.imports_for(SCRATCH)
        jobs = [(entry, lang) for entry in wanted for lang in LANGS]

        def one(job):
            entry, lang = job
            name = f"{entry['stem']}-{lang}"
            document = preview.document(entry["code"], entry["level"], lang, config=config, commands=commands, document_language=True)
            source = SCRATCH / f"{name}.typ"
            source.write_text(document, encoding="utf-8")
            target = SCRATCH / f"{name}.svg"
            result = subprocess.run([typst, "compile", "--root", str(bex.EXAMPLES), str(source), str(target)],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            if result.returncode != 0 or not target.is_file():
                return job, None, f"{name}: {result.stderr.strip().splitlines()[0] if result.stderr.strip() else 'no output'}"
            return job, minify_svg(target.read_text(encoding="utf-8")), None

        with ThreadPoolExecutor(max_workers=self.jobs) as pool:
            results = list(pool.map(one, jobs))
        self.compiled = len(jobs)
        for (entry, lang), svg, failure in results:
            if failure:
                self.warnings.append(f"example did not compile: {failure}")
                continue
            digest = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:10]
            rel = f"img/{entry['stem']}-{digest}.svg"
            if not (self.out / rel).exists():
                (self.out / rel).write_text(svg, encoding="utf-8", newline="\n")
            self.images_of[(entry["stem"], lang)] = rel
        self.failures = [f for _job, _svg, f in results if f]
        shutil.rmtree(SCRATCH, ignore_errors=True)

    def example_of(self, stem):
        """The command and the worked example one page's stem names -- `show-calc-1` is show-calc's first -- as website/content and site.json name them."""
        entry = self.examples.get(stem)
        if entry is None:
            raise SystemExit(f"website: no example '{stem}' (website/content or site.json names it)")
        command = self.by_name[entry["command"]]
        return command, command["examples"][entry["index"]]

    def example_card(self, stem, page, heading=None, show_code=True):
        """One worked example: its code and its page, with the 1 · 2 · 3 levels where it has them -- or the note that says why its page is not here."""
        command, example = self.example_of(stem)
        return self._example_html(command, example, page, heading, show_code, only_level=None)

    def _example_html(self, command, example, page, heading, show_code, only_level=None):
        lang = page.lang
        parts = [f'<figure class="example">']
        if heading:
            parts.append(f"<figcaption>{heading}</figcaption>")
        if show_code:
            parts.append(code_block(example["code"], "typ", t(lang, "copy")))
        variants = example["variants"]
        if not example["render"]:
            parts.append(f'<div class="callout note"><p>{esc(rw(lang, "not_rendered"))}</p></div>')
        elif any(v["masked"] for v in variants.values()):
            parts.append(f'<div class="callout norm"><p>{esc(t(lang, "masked_note", commands=rw(lang, "commands")))}</p></div>')
        else:
            shown = {lvl: v for lvl, v in variants.items() if self.image_exists(v["stem"], lang)}
            if not shown:
                parts.append(f'<div class="callout note"><p>{esc(t(lang, "example_missing"))}</p></div>')
            else:
                levels = sorted(shown)
                default = preview.DEFAULT_LEVEL if preview.DEFAULT_LEVEL in shown else levels[0]
                parts.append('<div class="preview" data-levels>')
                if len(levels) > 1:
                    parts.append(f'<div class="levels" role="tablist" aria-label="{esc(rw(lang, "level"))}"><span>{esc(rw(lang, "level"))}</span>'
                                 + "".join(f'<button type="button" role="tab" data-level="{lvl}" aria-selected="{"true" if lvl == default else "false"}">{lvl}</button>' for lvl in levels)
                                 + "</div>")
                for lvl in levels:
                    hidden = "" if lvl == default else " hidden"
                    alt = t(lang, "example_alt", command=command["name"], level=lvl)
                    parts.append(f'<div class="paper" data-level="{lvl}"{hidden}><img src="{esc(page.url(self.image_path(shown[lvl]["stem"], lang)))}" alt="{esc(alt)}" loading="lazy"></div>')
                parts.append("</div>")
        parts.append("</figure>")
        return "".join(parts)

    # -- the installer and the manifest --

    @staticmethod
    def has_download(release):
        """Whether the site can offer this release's installer: recorded, and kept on GitHub. The ones recorded before v0.117 stay in GitLab's registry, which is no longer updated -- their notes and their page of changes remain, their download does not."""
        info = release.get("installer")
        return isinstance(info, dict) and bool(info.get("sha256")) and info.get("hosted") == "github"

    def release_with_installer(self):
        return next((r for r in self.releases if self.has_download(r)), None)

    def check_releases(self):
        """releases.json says, for every installer it records, where it is kept: a record that does not is malformed, and stops the build rather than being skipped or fetched at a guess."""
        for release in self.releases:
            info = release.get("installer")
            if not isinstance(info, dict) or not info.get("sha256"):
                continue
            if info.get("hosted") not in HOSTED:
                self.errors.append(f"website/releases.json, {release.get('version')}: installer.hosted is {info.get('hosted')!r}, expected one of {', '.join(HOSTED)}")
            elif info["hosted"] == "github":
                problem = updates.installer_address_problem(info.get("url"), CONFIG["base_url"] + "version.json")
                if problem:
                    self.errors.append(f"website/releases.json, {release.get('version')}: {problem}")

    def place_installer(self):
        """Checks the newest installer kept on GitHub, and marks its release as the published one. The installer is not copied into the site (Cloudflare Pages takes no file over 25 MiB): the site links to its Release."""
        self.check_releases()
        if self.errors:
            return
        release = self.release_with_installer()
        if release is None:
            self.notices.append("website/releases.json records no installer kept on GitHub yet (packaging/publish.py): the site offers no download and writes no version.json")
            return
        if self.installer_source is None and not self.fetch_installer:
            return
        info = release["installer"]
        try:
            if self.installer_source is not None:
                if self.installer_source.stat().st_size != info["size"] or sha256(self.installer_source) != info["sha256"]:
                    raise ValueError("its size or its SHA-256 is not the one recorded")
            else:
                with tempfile.TemporaryDirectory() as folder:   # downloaded as an installed Woodcore would, checked, and thrown away
                    updates.download({"version": release["version"], "installer": {"url": info["url"], "size": info["size"], "sha256": info["sha256"]}}, folder=folder)
        except (OSError, ValueError, KeyError, updates.UpdateError) as exc:
            message = f"the installer of {release['version']} ({info['file']}) is not the one website/releases.json records: {exc}"
            (self.errors if self.fetch_installer else self.warnings).append(message)   # a preview with a local file stops nothing: nothing is deployed from it
            return
        self.published = release

    def write_manifest(self):
        if self.published is None:
            return
        release = self.published
        manifest = {
            "schema_version": MANIFEST_SCHEMA,
            "version": release["version"],
            "date": release.get("date", ""),
            "installer": {"url": release["installer"]["url"], "sha256": release["installer"]["sha256"], "size": release["installer"]["size"]},
            "notes": release.get("notes", {}),
            "page": {lang: CONFIG["base_url"] + f"{lang}/download/" for lang in LANGS},
        }
        # what the version changes, per language, where a page says it: the update window links to it (update_gui.py)
        changes = {lang: CONFIG["base_url"] + self.change_page(lang, release["version"]) for lang in LANGS if self.change_page(lang, release["version"])}
        if changes:
            manifest["changes"] = changes
        self.write("version.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    # -- the frame every page shares --

    def frame(self, page, title, body, sidebar=None, toc=None, description="", wide=False, body_class=""):
        lang = page.lang
        links = self.section_links(page)
        switch = []
        for other in LANGS:
            twin = page.path.replace(f"{lang}/", f"{other}/", 1) if page.path.startswith(f"{lang}/") else f"{other}/index.html"
            target = posixpath.dirname(twin) + "/"
            current = ' aria-current="true"' if other == lang else ""
            switch.append(f'<a href="{esc(page.url(target))}" hreflang="{other}" lang="{other}" data-lang="{other}"{current}>{other.upper()}</a>')
        alternates = "".join(
            f'<link rel="alternate" hreflang="{other}" href="{esc(CONFIG["base_url"] + posixpath.dirname(page.path.replace(f"{lang}/", f"{other}/", 1)) + "/")}">'
            for other in LANGS if page.path.startswith(f"{lang}/"))
        version = self.latest_version()
        download = f'<a class="button small" href="{esc(page.url(f"{lang}/download/"))}">{esc(t(lang, "nav_download"))}</a>'
        menu_button = f'<button class="menu-toggle" type="button" data-menu aria-label="{esc(t(lang, "menu"))}"><span></span><span></span><span></span></button>' if sidebar else ""
        layout = "doc-layout" if sidebar else ("wide-layout" if wide else "page-layout")
        side = f'<aside class="sidebar" data-sidebar>{sidebar}</aside>' if sidebar else ""
        right = ""
        if toc:
            right = f'<nav class="toc" aria-label="{esc(t(lang, "on_this_page"))}"><p>{esc(t(lang, "on_this_page"))}</p><ul>' + "".join(
                f'<li class="lvl{lvl}"><a href="#{esc(anchor)}">{esc(text)}</a></li>' for lvl, anchor, text in toc) + "</ul></nav>"
        return f"""<!DOCTYPE html>
<html lang="{lang}" data-root="{esc(page.root())}" data-lang="{lang}" data-stamp="{ASSET_STAMP}" data-t-copied="{esc(t(lang, 'copied'))}" data-t-empty="{esc(t(lang, 'search_empty'))}" data-t-cmd="{esc(rw(lang, 'command'))}" data-t-tut="{esc(t(lang, 'search_kind_tut'))}" data-t-page="{esc(t(lang, 'search_kind_page'))}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description or t(lang, 'meta_description'))}">
<meta name="theme-color" content="#239dad">
<link rel="icon" href="{esc(page.url('assets/logo.svg'))}" type="image/svg+xml">
<link rel="stylesheet" href="{esc(page.url('assets/site.css'))}?v={ASSET_STAMP}">
{alternates}
<script src="{esc(page.url('assets/site.js'))}?v={ASSET_STAMP}" defer></script>
</head>
<body class="{esc(body_class)}">
<a class="skip" href="#main">{esc(t(lang, "skip"))}</a>
<header class="topbar">
  <div class="topbar-inner">
    {menu_button}
    <a class="brand" href="{esc(page.url(f'{lang}/'))}"><img src="{esc(page.url('assets/logo.svg'))}" alt="" width="28" height="28"><span>Woodcore</span><span class="slogan">{esc(t(lang, 'slogan'))}</span></a>
    <nav class="mainnav" aria-label="{esc(t(lang, 'nav_label'))}">{links}</nav>
    <div class="topbar-right">
      <div class="langs" aria-label="{esc(t(lang, 'language'))}">{''.join(switch)}</div>
      {download}
    </div>
  </div>
</header>
<div class="{layout}">
{side}
<main id="main" class="content">
{body}
</main>
{right}
</div>
<footer class="footer">
  <div class="footer-inner">
    <div class="footer-brand"><img src="{esc(page.url('assets/logo.svg'))}" alt="" width="24" height="24"> <strong>Woodcore</strong> <span class="slogan">{esc(t(lang, 'slogan'))}</span> <span>{esc(t(lang, 'footer_tagline'))}</span></div>
    <div class="footer-links">
      <a href="{esc(page.url(f'{lang}/docs/'))}">{esc(t(lang, 'nav_docs'))}</a>
      <a href="{esc(page.url(f'{lang}/tutorial/'))}">{esc(t(lang, 'nav_tutorial'))}</a>
      <a href="{esc(page.url(f'{lang}/download/'))}">{esc(t(lang, 'nav_download'))}</a>
      <a href="{esc(page.url(f'{lang}/legal/'))}">{esc(t(lang, 'footer_legal'))}</a>
    </div>
    <p class="footer-note">{esc(t(lang, 'footer_note', version=version or '—'))}</p>
    <p class="footer-legal">© 2026 Florian Lamprecht — {esc(t(lang, 'footer_licensed'))} · <a href="mailto:woodcore@pineo.ch">woodcore@pineo.ch</a> · <a href="{esc(page.url(f'legal/LICENSE-{lang}.txt'))}">{esc(t(lang, 'footer_licence'))}</a> · <a href="{esc(page.url('legal/THIRD-PARTY-NOTICES.txt'))}">{esc(t(lang, 'footer_notices'))}</a></p>
  </div>
</footer>
</body>
</html>
"""

    def latest_version(self):
        return (self.published or {}).get("version") or (self.releases[0]["version"] if self.releases else project.VERSION)

    def section_links(self, page):
        """The site's sections as links, the one of this page marked: the bar at the top, and the sidebar on a narrow screen."""
        lang = page.lang
        return "".join(f'<a href="{esc(page.url(f"{lang}/{url}"))}"{" class=active" if page.section == key else ""}>{esc(t(lang, label))}</a>'
                       for key, label, url in SECTIONS)

    def sidebar(self, page, nav, search=True):
        """A sidebar: the site's sections for a narrow screen (where the bar at the top hides them behind ☰), the search where the page has one, then the page's own navigation, `nav`."""
        lang = page.lang
        parts = [f'<nav class="sidebar-sections" aria-label="{esc(t(lang, "nav_label"))}">{self.section_links(page)}</nav>']
        if search:
            parts += [f'<div class="search"><input type="search" data-search placeholder="{esc(t(lang, "search_placeholder"))}" aria-label="{esc(t(lang, "search_placeholder"))}" autocomplete="off" spellcheck="false"><kbd>/</kbd></div>',
                      '<ol class="results" data-results hidden></ol>']
        parts.append(f'<nav class="sidenav" data-sidenav>{nav}</nav>')
        return "".join(parts)

    @staticmethod
    def group_link(page, url, label, active):
        return f'<p class="group"><a href="{esc(page.url(url))}"{" class=active" if active else ""}>{esc(label)}</a></p>'

    def sidebar_docs(self, page, current):
        """Beside the commands, as typst.app/docs lays them out: the search, then «Commandes» and the commands by category, the category of the page open. Nothing else: the tutorial and what changed have sidebars of their own."""
        lang = page.lang
        parts = [self.group_link(page, f"{lang}/docs/", rw(lang, "commands"), current == ("docs", None))]
        for key in CATEGORY_KEYS:
            names = [c for c in self.commands if c["category"] == key]
            open_ = any(current == ("command", c["name"]) for c in names)
            parts.append(f'<details{" open" if open_ else ""}><summary>{esc(docs.category_label(key, lang))}</summary><ul>')
            for command in names:
                active = ' active" aria-current="page' if current == ("command", command["name"]) else ""
                parts.append(f'<li><a class="cmd{active}" href="{esc(page.url(f"{lang}/docs/{command["name"]}/"))}">{esc(command["name"])}</a></li>')
            parts.append("</ul></details>")
        return self.sidebar(page, "".join(parts))

    def sidebar_tutorial(self, page, current):
        """Beside the tutorial: the search, its steps, and the reference as one link."""
        lang = page.lang
        parts = [self.group_link(page, f"{lang}/tutorial/", t(lang, "sidebar_tutorial"), current == ("tutorial", None)), "<ul>"]
        for position, step in enumerate(self.tutorial[lang]):
            url = f"{lang}/tutorial/{step['slug']}/"
            active = ' class="active" aria-current="page"' if current == ("tutorial", step["slug"]) else ""
            parts.append(f'<li><a href="{esc(page.url(url))}"{active}><span class="step">{position + 1}</span>{esc(prose_plain(step["title"]))}</a></li>')
        parts.append("</ul>")
        parts.append(self.group_link(page, f"{lang}/docs/", t(lang, "sidebar_reference"), False))
        return self.sidebar(page, "".join(parts))

    def sidebar_changes(self, page, current):
        """Beside what changed: the list of versions, and nothing else."""
        lang = page.lang
        parts = [self.group_link(page, f"{lang}/changes/", t(lang, "sidebar_changes"), current == ("changes", None)), "<ul>"]
        for change in self.changes[lang]:
            active = ' class="active" aria-current="page"' if current == ("change", change["version"]) else ""
            parts.append(f'<li><a href="{esc(page.url(f"{lang}/changes/{change["version"]}/"))}"{active}>{esc(prose_plain(change["title"]))}</a></li>')
        parts.append("</ul>")
        return self.sidebar(page, "".join(parts), search=False)

    # -- the pages themselves --

    def page_root(self):
        page = Page(self, CONFIG["default_language"], "index.html", "root")
        choices = "".join(f'<a class="lang-choice" href="{l}/" hreflang="{l}" lang="{l}">{esc(t(l, "language_name"))}</a>' for l in LANGS)
        self.write("index.html", f"""<!DOCTYPE html>
<html lang="{CONFIG['default_language']}" data-root="./">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Woodcore</title>
<link rel="icon" href="assets/logo.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/site.css">
<script>
(function () {{
  var langs = {json.dumps(list(LANGS))}, chosen = null;
  try {{ chosen = localStorage.getItem("woodcore-lang"); }} catch (e) {{}}
  if (langs.indexOf(chosen) < 0) {{
    var wanted = (navigator.languages || [navigator.language || ""]);
    for (var i = 0; i < wanted.length && !chosen; i++) {{
      var code = String(wanted[i]).slice(0, 2).toLowerCase();
      if (langs.indexOf(code) >= 0) chosen = code;
    }}
  }}
  location.replace((chosen || {json.dumps(CONFIG['default_language'])}) + "/");
}})();
</script></head>
<body class="root-page"><main class="root-choice"><img src="assets/logo.svg" alt="" width="64" height="64"><h1>Woodcore</h1><div>{choices}</div></main></body></html>
""")
        del page

    def page_404(self):
        lang = CONFIG["default_language"]
        page = Page(self, lang, "404.html", "none")
        body = "".join(f'<section class="notfound" lang="{l}"><h1>{esc(t(l, "notfound_title"))}</h1><p>{esc(t(l, "notfound_text"))}</p><p><a class="button" href="{esc(CONFIG["base_url"] + l + "/")}">{esc(t(l, "notfound_home"))}</a></p></section>' for l in LANGS)
        # a 404 is served at whatever address was asked for, so its links are absolute
        html_text = self.frame(page, "Woodcore — 404", body).replace(f'data-root="{page.root()}"', f'data-root="{CONFIG["base_url"]}"')
        html_text = re.sub(r'(href|src)="(?!https?:|#|mailto:)([^"]*)"', lambda m: f'{m.group(1)}="{CONFIG["base_url"]}{m.group(2).lstrip("./")}"', html_text)
        self.write("404.html", html_text)

    def page_moved(self, lang, old, new):
        """An address the site no longer has a page at, kept working (site.json's `moved`, v0.96): a small page there sends the reader on to the page that replaced it -- a meta refresh, a line of script keeping the anchor, and a link for a browser that follows neither. `old` and `new` are read from a language's root (`tutorial/katalog/`), so one line of site.json serves the three languages. Nothing is written over a page the site has at that address, and a new address the site has no page at is said."""
        page = Page(self, lang, f"{lang}/{old.strip('/')}/index.html", "none")
        target = f"{lang}/{new.strip('/')}/"
        if (self.out / page.path).exists():
            self.warnings.append(f"{page.path}: the site has a page there, so it sends nobody on to {target}")
            return
        if not (self.out / target / "index.html").is_file():
            self.warnings.append(f"{page.path}: moved to {target}, where the site has no page")
        link = page.url(target)
        self.moved.append(page.path)
        self.write(page.path, f"""<!DOCTYPE html>
<html lang="{lang}" data-root="{esc(page.root())}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(t(lang, "moved_title"))} — Woodcore</title>
<meta name="robots" content="noindex"><link rel="canonical" href="{esc(CONFIG["base_url"] + target)}">
<meta http-equiv="refresh" content="0; url={esc(link)}">
<link rel="icon" href="{esc(page.url('assets/logo.svg'))}" type="image/svg+xml"><link rel="stylesheet" href="{esc(page.url('assets/site.css'))}?v={ASSET_STAMP}">
<script>location.replace({json.dumps(link)} + location.hash);</script></head>
<body class="root-page"><main class="root-choice"><img src="{esc(page.url('assets/logo.svg'))}" alt="" width="64" height="64"><h1>{esc(t(lang, "moved_title"))}</h1><div><a class="lang-choice" href="{esc(link)}">{esc(t(lang, "moved_link"))}</a></div></main></body></html>
""")

    def page_home(self, lang):
        page = Page(self, lang, f"{lang}/index.html", "home")
        hero_stem = CONFIG["hero_example"]
        hero_img = (f'<img src="{esc(page.url(self.image_path(hero_stem, lang)))}" alt="{esc(t(lang, "hero_image_alt"))}">'
                    if self.image_exists(hero_stem, lang) else "")
        # the button names a version only once one can be downloaded
        download_label = t(lang, "hero_download", version=self.published["version"]) if self.published else t(lang, "nav_download")
        features = "".join(
            f'<article class="feature"><div class="feature-icon" aria-hidden="true">{FEATURE_ICONS[i - 1]}</div><h3>{esc(t(lang, f"feature_{i}_title"))}</h3><p>{inline(t(lang, f"feature_{i}_text"), page)}</p></article>'
            for i in range(1, 7))
        steps = "".join(
            f'<li><span class="num">{i}</span><div><h3>{esc(t(lang, f"how_{i}_title"))}</h3><p>{inline(t(lang, f"how_{i}_text"), page)}</p></div></li>'
            for i in range(1, 5))
        # the code beside each picture is the fence of the example the picture is, not a copy of it
        _command, hero_example = self.example_of(hero_stem)
        levels_command, levels_example = self.example_of(CONFIG["levels_example"])
        levels = self._example_html(levels_command, levels_example, page, None, show_code=False)
        norms = "".join(f'<span class="norm-chip">{esc(n)}</span>' for n in ("SIA 260", "SIA 261", "SIA 263", "SIA 265", "SN EN 14592", "STE Compact 02"))
        body = f"""
<section class="hero">
  <div class="hero-text">
    <p class="eyebrow">{esc(t(lang, "hero_eyebrow"))}</p>
    <h1>{inline(t(lang, "hero_title"), page)}</h1>
    <p class="lead">{inline(t(lang, "hero_lead"), page)}</p>
    <div class="cta">
      <a class="button" href="{esc(page.url(f'{lang}/download/'))}">{esc(download_label)}</a>
      <a class="button ghost" href="{esc(page.url(f'{lang}/tutorial/'))}">{esc(t(lang, "hero_tutorial"))}</a>
    </div>
    <p class="hero-note">{esc(t(lang, "hero_note"))}</p>
  </div>
  <div class="editor" aria-label="{esc(t(lang, 'hero_editor_label'))}">
    <div class="editor-bar"><span></span><span></span><span></span><em>Sections/005-bemessung.typ</em></div>
    <div class="editor-panes">
      <div class="editor-code"><pre><code>{highlight("// " + t(lang, "hero_code_comment") + chr(10) + hero_example["code"])}</code></pre></div>
      <div class="editor-preview">{hero_img}</div>
    </div>
  </div>
</section>
<section class="band how">
  <h2>{esc(t(lang, "how_title"))}</h2>
  <p class="section-lead">{inline(t(lang, "how_lead"), page)}</p>
  <ol class="steps">{steps}</ol>
</section>
<section class="band">
  <h2>{esc(t(lang, "features_title"))}</h2>
  <div class="features">{features}</div>
</section>
<section class="band levels-band">
  <div class="split">
    <div>
      <h2>{esc(t(lang, "levels_title"))}</h2>
      <p>{inline(t(lang, "levels_text"), page)}</p>
      <ul class="checks"><li>{inline(t(lang, "levels_1"), page)}</li><li>{inline(t(lang, "levels_2"), page)}</li><li>{inline(t(lang, "levels_3"), page)}</li></ul>
      {code_block(levels_example["code"], "typ", t(lang, "copy"))}
    </div>
    <div>{levels}</div>
  </div>
</section>
<section class="band">
  <div class="split">
    <div>
      <h2>{esc(t(lang, "norms_title"))}</h2>
      <p>{inline(t(lang, "norms_text"), page)}</p>
      <div class="norm-chips">{norms}</div>
    </div>
    <div>
      <h2>{esc(t(lang, "window_title"))}</h2>
      <p>{inline(t(lang, "window_text"), page)}</p>
    </div>
  </div>
</section>
<section class="cta-band">
  <h2>{esc(t(lang, "cta_title"))}</h2>
  <p>{inline(t(lang, "cta_text"), page)}</p>
  <div class="cta">
    <a class="button light" href="{esc(page.url(f'{lang}/download/'))}">{esc(t(lang, "nav_download"))}</a>
    <a class="button ghost light" href="{esc(page.url(f'{lang}/docs/'))}">{esc(t(lang, "nav_docs"))}</a>
  </div>
</section>
"""
        self.write(page.path, self.frame(page, t(lang, "home_title"), body, wide=True, body_class="home"))

    def page_download(self, lang):
        page = Page(self, lang, f"{lang}/download/index.html", "download")
        text = (CONTENT / lang / "download.md").read_text(encoding="utf-8")
        if "{{download}}" not in text:
            text = "{{download}}\n\n" + text
        body, toc = markdown(text, page)
        history = []
        # a version is listed once its installer is recorded as kept on GitHub (packaging/publish.py): notes written ahead of a publication are not a publication, and one kept in GitLab's registry can no longer be downloaded
        for release_ in (r for r in self.releases if self.has_download(r)):
            notes = release_.get("notes", {}).get(lang) or release_.get("notes", {}).get("en", "")
            more = self.change_page(lang, release_["version"])
            more = f' <a href="{esc(page.url(more))}">{esc(t(lang, "changes_more"))} →</a>' if more else ""
            history.append(f'<li><h3>Woodcore {esc(release_["version"])} <span class="date">{esc(release_.get("date", ""))}</span></h3><p>{inline(notes, page)}{more}</p></li>')
        if history:
            anchor = "history"
            body += f'<h2 id="{anchor}"><a class="anchor" href="#{anchor}" aria-hidden="true">#</a>{esc(t(lang, "download_history"))}</h2><ul class="releases">{"".join(history)}</ul>'
        self.write(page.path, self.frame(page, f"{t(lang, 'nav_download')} — Woodcore", f'<article class="prose">{body}</article>'))

    def download_card(self, page):
        """The latest installer, its size, its date and its SHA-256 -- or, before one is published, a line saying so."""
        lang, release = page.lang, self.published
        if release is None:
            return f'<div class="download-card pending"><h2>{esc(t(lang, "download_pending_title"))}</h2><p>{esc(t(lang, "download_pending"))}</p></div>'
        info = release["installer"]
        return f"""<div class="download-card">
  <div><p class="eyebrow">{esc(t(lang, "download_latest"))}</p><h2>Woodcore {esc(release["version"])}</h2>
  <p class="meta">{esc(t(lang, "download_meta", date=release.get("date", ""), size=f"{info['size'] / 2**20:.0f}"))}</p></div>
  <a class="button big" href="{esc(info['url'])}">{esc(t(lang, "download_button"))}</a>
  <p class="sha"><span>SHA-256</span> <code>{esc(info["sha256"])}</code></p>
  <p class="meta">{esc(t(lang, "download_origin"))}</p>{self._whatsnew(page, release["version"])}
</div>"""

    def _whatsnew(self, page, version):
        target = self.change_page(page.lang, version)
        return f'\n  <p class="whatsnew"><a href="{esc(page.url(target))}">{esc(t(page.lang, "download_whatsnew", version=version))} →</a></p>' if target else ""

    def page_docs_index(self, lang):
        page = Page(self, lang, f"{lang}/docs/index.html", "docs")
        parts = [f'<article class="prose"><p class="eyebrow">{esc(t(lang, "nav_docs"))}</p><h1>{esc(rw(lang, "commands"))}</h1><p class="lead">{inline(t(lang, "docs_lead", commands=rw(lang, "commands")), page)}</p>',
                 code_block('#import "../commands.typ": *', "typ", t(lang, "copy")), f'<p>{inline(t(lang, "docs_import"), page)}</p>']
        toc = []
        for key in CATEGORY_KEYS:
            anchor = f"cat-{key}"
            toc.append((2, anchor, docs.category_label(key, lang)))
            parts.append(f'<h2 id="{anchor}"><a class="anchor" href="#{anchor}" aria-hidden="true">#</a>{esc(docs.category_label(key, lang))}</h2><p>{inline(docs.category_lead(key, lang), page)}</p><div class="cards">')
            for command in (c for c in self.commands if c["category"] == key):
                block, _missing = self.localised(command, lang)
                summary = prose_plain(block["paragraphs"][0]) if block["paragraphs"] else ""
                if len(summary) > 180:
                    summary = summary[:177].rsplit(" ", 1)[0] + "…"
                parts.append(f'<a class="card" href="{esc(page.url(f"{lang}/docs/{command["name"]}/"))}"><code>{esc(command["name"])}</code><span>{esc(summary)}</span></a>')
            parts.append("</div>")
        parts.append("</article>")
        self.write(page.path, self.frame(page, f"{rw(lang, 'commands')} — Woodcore", "".join(parts), sidebar=self.sidebar_docs(page, ("docs", None)), toc=toc))

    def page_command(self, lang, command):
        name = command["name"]
        page = Page(self, lang, f"{lang}/docs/{name}/index.html", "docs")
        block, missing = self.localised(command, lang)
        returns = command["block"]["returns"]
        signature = f"#{name}({command['params']})" if command["kind"] == "function" else command["signature"]
        if returns:
            signature += f" -> {returns}"
        parts = [f'<article class="prose command"><p class="crumbs"><a href="{esc(page.url(f"{lang}/docs/"))}">{esc(rw(lang, "commands"))}</a> › <a href="{esc(page.url(f"{lang}/docs/"))}#cat-{command["category"]}">{esc(docs.category_label(command["category"], lang))}</a></p>',
                 f'<h1><code>{esc(name)}</code></h1>',
                 f'<div class="signature"><pre><code>{highlight(signature)}</code></pre></div>']
        for paragraph in block["paragraphs"]:
            parts.append(f"<p>{prose_html(paragraph)}</p>")
        if missing:
            parts.append(f'<div class="callout note"><p>{esc(rw(lang, "untranslated", n=missing))}</p></div>')
        toc = []
        if block["bullets"]:
            toc.append((2, "arguments", rw(lang, "arguments")))
            parts.append(f'<h2 id="arguments"><a class="anchor" href="#arguments" aria-hidden="true">#</a>{esc(rw(lang, "arguments"))}</h2><dl class="params">')
            for arg, kind, text in block["bullets"]:
                default = command["defaults"].get(arg)
                types = "".join(f'<span class="type">{esc(x.strip())}</span>' for x in re.split(r"[,|]", kind) if x.strip())
                badge = (f'<span class="default">{esc(t(lang, "default"))} <code>{esc(default)}</code></span>' if default is not None
                         else (f'<span class="required">{esc(t(lang, "required"))}</span>' if not arg.startswith("..") else f'<span class="required">{esc(t(lang, "variadic"))}</span>'))
                parts.append(f'<dt id="arg-{esc(arg.lstrip("."))}"><code>{esc(arg)}</code>{types}{badge}</dt><dd>{prose_html(text.strip())}</dd>')
            parts.append("</dl>")
        if command["kind"] == "function" or name in ref.WRITTEN_CALLS:
            toc.append((2, "calls", t(lang, "calls")))
            complete, minimal = ref.call_complete(command, self.samples), ref.call_minimal(command, self.samples)
            parts.append(f'<h2 id="calls"><a class="anchor" href="#calls" aria-hidden="true">#</a>{esc(t(lang, "calls"))}</h2>')
            parts.append(f'<p class="label">{esc(rw(lang, "call_minimal"))}</p>' + code_block(minimal, "typ", t(lang, "copy")))
            if complete != minimal:
                parts.append(f'<p class="label">{esc(rw(lang, "call_complete"))}</p>' + code_block(complete, "typ", t(lang, "copy")))
        if command["examples"]:
            toc.append((2, "examples", t(lang, "examples")))
            parts.append(f'<h2 id="examples"><a class="anchor" href="#examples" aria-hidden="true">#</a>{esc(t(lang, "examples"))}</h2>')
            for example in command["examples"]:
                parts.append(self._example_html(command, example, page, esc(rw(lang, "example", n=example["index"] + 1)), True))
        parts.append(f'<p class="defined">{esc(rw(lang, "defined_in"))} <code>lib/{esc(command["file"])}:{command["line"]}</code></p>')
        siblings = [c for c in self.commands]
        position = siblings.index(command)
        prev_ = siblings[position - 1] if position > 0 else None
        next_ = siblings[position + 1] if position + 1 < len(siblings) else None
        parts.append(self.pager(page, prev_ and (f"{lang}/docs/{prev_['name']}/", prev_["name"]), next_ and (f"{lang}/docs/{next_['name']}/", next_["name"])))
        parts.append("</article>")
        summary = prose_plain(block["paragraphs"][0]) if block["paragraphs"] else ""
        self.write(page.path, self.frame(page, f"{name} — Woodcore", "".join(parts), sidebar=self.sidebar_docs(page, ("command", name)), toc=toc, description=summary[:200]))

    def pager(self, page, prev_, next_):
        lang = page.lang
        cells = []
        if prev_:
            cells.append(f'<a class="prev" href="{esc(page.url(prev_[0]))}"><span>{esc(t(lang, "previous"))}</span><strong>{esc(prose_plain(prev_[1]))}</strong></a>')
        else:
            cells.append("<span></span>")
        if next_:
            cells.append(f'<a class="next" href="{esc(page.url(next_[0]))}"><span>{esc(t(lang, "next"))}</span><strong>{esc(prose_plain(next_[1]))}</strong></a>')
        return f'<nav class="pager">{"".join(cells)}</nav>'

    def page_changes_index(self, lang):
        """How to update, and every version's page with the line that sums it up."""
        page = Page(self, lang, f"{lang}/changes/index.html", "changes")
        intro, toc = markdown((CONTENT / lang / "changes.md").read_text(encoding="utf-8"), page)
        items = "".join(
            f'<li><a href="{esc(page.url(f"{lang}/changes/{c["version"]}/"))}"><span class="num">{esc(".".join(c["version"].split(".")[:2]))}</span><strong>{esc(prose_plain(c["title"]))}</strong><span>{esc(self.first_paragraph(c["text"]))}</span></a></li>'
            for c in self.changes[lang])
        anchor = "versions"
        toc = toc + [(2, anchor, t(lang, "changes_versions"))]
        body = (f'<article class="prose">{intro}<h2 id="{anchor}"><a class="anchor" href="#{anchor}" aria-hidden="true">#</a>{esc(t(lang, "changes_versions"))}</h2>'
                f'<ol class="tutorial-list versions">{items}</ol></article>')
        self.write(page.path, self.frame(page, f"{t(lang, 'changes_title')} — Woodcore", body, sidebar=self.sidebar_changes(page, ("changes", None)), toc=toc))

    def page_legal(self, lang):
        """Contact, copyright and licence, the disclaimer, the update check and what the site stores: `content/<lang>/legal.md`, linking the files of legal/ copy_assets publishes."""
        page = Page(self, lang, f"{lang}/legal/index.html", "legal")
        body, toc = markdown((CONTENT / lang / "legal.md").read_text(encoding="utf-8"), page)
        self.write(page.path, self.frame(page, f"{t(lang, 'legal_title')} — Woodcore", f'<article class="prose">{body}</article>', toc=toc))

    def page_change(self, lang, position):
        """What one version changes: new, changed in a report already written, to do."""
        change = self.changes[lang][position]
        page = Page(self, lang, f"{lang}/changes/{change['version']}/index.html", "changes")
        content, toc = markdown(change["text"], page)
        versions = self.changes[lang]
        older = versions[position + 1] if position + 1 < len(versions) else None
        newer = versions[position - 1] if position > 0 else None
        body = (f'<article class="prose"><p class="eyebrow">{esc(t(lang, "changes_version", version=change["version"]))}</p>{content}'
                + self.pager(page, older and (f"{lang}/changes/{older['version']}/", older["title"]), newer and (f"{lang}/changes/{newer['version']}/", newer["title"]))
                + "</article>")
        self.write(page.path, self.frame(page, f"{prose_plain(change['title'])} — Woodcore", body, sidebar=self.sidebar_changes(page, ("change", change["version"])), toc=toc))

    def page_examples(self, lang):
        """The gallery: no sidebar, the width of the home page, two examples a row where the screen holds them."""
        page = Page(self, lang, f"{lang}/examples/index.html", "examples")
        parts = [f'<article class="prose gallery-page"><div class="gallery-head"><h1>{esc(t(lang, "examples_title"))}</h1><p class="lead">{inline(t(lang, "examples_lead"), page)}</p></div><div class="gallery-grid">']
        for stem in CONFIG["gallery"]:
            command, _example = self.example_of(stem)
            title = t(lang, f"gallery_{stem}")
            parts.append(f'<section class="gallery-item"><h2 id="{stem}"><a class="anchor" href="#{stem}" aria-hidden="true">#</a>{esc(title)}</h2>')
            parts.append(f'<p>{inline(t(lang, f"gallery_{stem}_text"), page)} <a href="{esc(page.url(f"{lang}/docs/{command["name"]}/"))}"><code>{esc(command["name"])}</code> →</a></p>')
            parts.append(self.example_card(stem, page) + "</section>")
        parts.append("</div></article>")
        self.write(page.path, self.frame(page, f"{t(lang, 'examples_title')} — Woodcore", "".join(parts), wide=True, body_class="gallery"))

    def page_tutorial(self, lang, position):
        step = self.tutorial[lang][position]
        page = Page(self, lang, f"{lang}/tutorial/{step['slug']}/index.html", "tutorial")
        content, toc = markdown(step["text"], page)
        steps = self.tutorial[lang]
        prev_ = steps[position - 1] if position > 0 else None
        next_ = steps[position + 1] if position + 1 < len(steps) else None
        body = (f'<article class="prose"><p class="eyebrow">{esc(t(lang, "tutorial_step", n=position + 1, total=len(steps)))}</p>{content}'
                + self.pager(page, prev_ and (f"{lang}/tutorial/{prev_['slug']}/", prev_["title"]), next_ and (f"{lang}/tutorial/{next_['slug']}/", next_["title"]))
                + "</article>")
        self.write(page.path, self.frame(page, f"{prose_plain(step['title'])} — Woodcore", body, sidebar=self.sidebar_tutorial(page, ("tutorial", step["slug"])), toc=toc))

    def page_tutorial_index(self, lang):
        page = Page(self, lang, f"{lang}/tutorial/index.html", "tutorial")
        items = "".join(
            f'<li><a href="{esc(page.url(f"{lang}/tutorial/{s["slug"]}/"))}"><span class="num">{i + 1}</span><strong>{esc(prose_plain(s["title"]))}</strong><span>{esc(self.first_paragraph(s["text"]))}</span></a></li>'
            for i, s in enumerate(self.tutorial[lang]))
        body = f'<article class="prose"><h1>{esc(t(lang, "tutorial_title"))}</h1><p class="lead">{inline(t(lang, "tutorial_lead"), page)}</p><ol class="tutorial-list">{items}</ol></article>'
        self.write(page.path, self.frame(page, f"{t(lang, 'tutorial_title')} — Woodcore", body, sidebar=self.sidebar_tutorial(page, ("tutorial", None))))

    @staticmethod
    def first_paragraph(text):
        for block in text.split("\n\n"):
            block = block.strip()
            if block and not block.startswith(("#", "```", ">", "-", "|", "{{")):
                plain = prose_plain(re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", block))
                return plain if len(plain) < 200 else plain[:197].rsplit(" ", 1)[0] + "…"
        return ""

    def search_index(self, lang):
        """The entries the sidebar's search reads: `t` the title, `u` the address, `k` the kind, `c` its category, `s` the line shown, `a` the arguments and `x` the rest of the text, matched and never shown -- so «Schnee» finds the tutorial page and the example about snow, where only the first paragraph was read."""
        entries = []
        for command in self.commands:
            block, _m = self.localised(command, lang)
            entries.append({"t": command["name"], "u": f"{lang}/docs/{command['name']}/", "k": "cmd",
                            "c": docs.category_label(command["category"], lang),
                            "s": prose_plain(block["paragraphs"][0])[:200] if block["paragraphs"] else "",
                            "a": " ".join(b[0] for b in block["bullets"]),
                            "x": " ".join(prose_plain(p) for p in block["paragraphs"][1:])[:1500]})
        for position, step in enumerate(self.tutorial[lang]):
            entries.append({"t": prose_plain(step["title"]), "u": f"{lang}/tutorial/{step['slug']}/", "k": "tut",
                            "c": t(lang, "tutorial_step", n=position + 1, total=len(self.tutorial[lang])),
                            "s": self.first_paragraph(step["text"]),
                            "x": self.plain_text(step["text"])[:4000]})
        for change in self.changes[lang]:
            entries.append({"t": prose_plain(change["title"]), "u": f"{lang}/changes/{change['version']}/", "k": "page",
                            "c": t(lang, "changes_title"), "s": self.first_paragraph(change["text"]),
                            "x": change["version"] + " " + self.plain_text(change["text"])[:4000]})
        for stem in CONFIG["gallery"]:
            entries.append({"t": t(lang, f"gallery_{stem}"), "u": f"{lang}/examples/#{stem}", "k": "page",
                            "c": t(lang, "examples_title"), "s": t(lang, f"gallery_{stem}_text"), "x": self.examples[stem]["command"]})
        for title, url in ((t(lang, "legal_title"), f"{lang}/legal/"), (t(lang, "nav_download"), f"{lang}/download/"), (t(lang, "examples_title"), f"{lang}/examples/"), (rw(lang, "commands"), f"{lang}/docs/")):
            entries.append({"t": title, "u": url, "k": "page", "c": "", "s": ""})
        return entries

    @staticmethod
    def plain_text(markdown_text):
        """A Markdown page as words to match: its code fences, markers and link targets dropped."""
        text = re.sub(r"```.*?```", " ", markdown_text, flags=re.S)
        text = re.sub(r"\{\{[^}]*\}\}", " ", text)
        text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
        text = re.sub(r"[#>*`|]+", " ", text)
        return " ".join(text.split())

    # -- what was built --

    def report(self):
        size = sum(p.stat().st_size for p in self.out.rglob("*") if p.is_file())
        images = sum(p.stat().st_size for p in (self.out / "img").glob("*") if p.is_file())
        if self.compiled:
            print(f"website: {self.compiled} example pages compiled (three languages), {len(set(self.images_of.values()))} distinct, {len(self.failures)} failed")
        print(f"website: {self.written} files written into {self.out}, {size / 2**20:.1f} MB ({images / 2**20:.1f} MB of example pages)"
              + (f", installer {self.published['version']}" if self.published else ", no installer"))
        files = [p for p in self.out.rglob("*") if p.is_file()]
        for big in (p for p in files if p.stat().st_size > FILE_LIMIT):
            self.errors.append(f"{big.relative_to(self.out).as_posix()} is {big.stat().st_size / 2**20:.1f} MiB: Cloudflare Pages takes no file over {FILE_LIMIT / 2**20:.0f} MiB")
        if len(files) > FILES_LIMIT:
            self.errors.append(f"{len(files)} files: Cloudflare Pages takes no more than {FILES_LIMIT}")
        for notice in self.notices:
            print(f"  note: {notice}")
        for warning in self.warnings:
            print(f"  warning: {warning}")
        for error in self.errors:
            print(f"  error: {error}")
        return size


FEATURE_ICONS = [
    '<svg viewBox="0 0 24 24"><path d="M4 4h16v16H4z M4 9h16 M9 9v11" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>',
    '<svg viewBox="0 0 24 24"><path d="M5 19V5 M5 19h14 M8 15l3-4 3 2 4-6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    '<svg viewBox="0 0 24 24"><path d="M4 6h16 M4 12h10 M4 18h13" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    '<svg viewBox="0 0 24 24"><path d="M6 3h9l3 3v15H6z M9 12l2 2 4-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
    '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3.5 12h17 M12 3.5c2.5 2.6 2.5 14.4 0 17 M12 3.5c-2.5 2.6-2.5 14.4 0 17" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
    '<svg viewBox="0 0 24 24"><path d="M12 3v12 M7 10l5 5 5-5 M5 20h14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
]


def version_tuple(text):
    """0.89.0 -> (0, 89, 0), as the launcher and the update check read a version."""
    return tuple(int("".join(ch for ch in piece if ch.isdigit()) or 0) for piece in str(text).split("."))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build Woodcore's website into public/.")
    parser.add_argument("--out", default=str(ROOT / "public"), help="where to write the site (default: public/)")
    parser.add_argument("--images", choices=("svg", "png"), default="svg", help="the example pages: compiled to SVG (Typst on PATH), or the committed PNGs")
    parser.add_argument("--installer", help="a local installer to put in the site (a preview)")
    parser.add_argument("--fetch-installer", action="store_true", help="download the published installer from its Release on GitHub and check it (the workflow); a failed check exits with 1")
    parser.add_argument("--jobs", type=int, help="how many examples are compiled at once")
    parser.add_argument("--serve", action="store_true", help="serve the site on http://localhost:8000/ once built")
    args = parser.parse_args(argv)
    site = Site(args.out, images=args.images, installer=args.installer, fetch_installer=args.fetch_installer, jobs=args.jobs)
    site.build()
    if site.errors:
        print(f"website: {len(site.errors)} error(s): nothing should be deployed from this build", file=sys.stderr)
        return 1
    if args.serve:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=args.out)
        print("serving on http://localhost:8000/  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
