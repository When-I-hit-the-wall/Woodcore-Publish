"""Woodcore's website and the publishing of an installer (website/build.py, packaging/publish.py, .gitlab-ci.yml, docs/conventions/build-and-release.md §12, v0.89).

The site is built here with the committed PNG pages (`--images png`), which needs no Typst: what is held is what the site says and where it links, not how Typst draws -- tests/test_commands.py compiles every example already. Held: the three languages carry the same words, the same tutorial and the same pages; the categories and the reference's words are calc/i18n/reference.json's, which Woodcore's commands tab reads too, and neither it nor the site writes them again; every command has its page in every language; the sidebar is the one the page's kind asks for; the home page shows the fences of its examples; every link and every picture of every page leads somewhere, and an address that moved leads to the page that replaced it; the pages that set a norm table in full are not published; no version.json is written before an installer is, and the one written with it is one the update check accepts; and the publishing refuses a version with no notes, sends the installer where the site fetches it from, and records what the site checks it against.
"""

import hashlib
import html.parser
import importlib.util
import io
import json
import pathlib
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import conftest
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"
for path in (TOOLS, ROOT / "packaging"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_reference as ref  # noqa: E402
import command_docs as docs  # noqa: E402
import publish  # noqa: E402
import updates  # noqa: E402


def _site_module():
    spec = importlib.util.spec_from_file_location("website_build", ROOT / "website" / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SITE = _site_module()
_BUILT = {}


def _built():
    """The site, built once for this file, with the PNG pages."""
    if "site" not in _BUILT:
        out = conftest.tmpdir("website")
        site = SITE.Site(out, images="png")
        site.build()
        _BUILT["site"] = site
    return _BUILT["site"]


# --- words and content -------------------------------------------------------------------------------------

def test_the_three_languages_carry_the_same_words():
    keys = set(SITE.STRINGS["fr"])
    for lang in SITE.LANGS:
        assert set(SITE.STRINGS[lang]) == keys, f"{lang}: {sorted(keys ^ set(SITE.STRINGS[lang]))}"
        for key, text in SITE.STRINGS[lang].items():
            assert text.strip(), f"{lang}.{key} is empty"
    assert "ß" not in json.dumps(SITE.STRINGS["de"], ensure_ascii=False), "Swiss German writes ss"



def test_the_slogan_is_the_brands_own_words_and_stands_beside_both_wordmarks():
    """«Woodcore — Make the numbers vibe» (v0.110), the engineer's own line for the site.

    ⚠️ The **same English in the three languages**, deliberately and not by omission: a slogan is the brand's own words, which §4bis and §13's v0.54 rule («what the engineer writes by hand is never translated») keep exactly as he writes them -- and «vibe» carries a pun no translation of it keeps. So this check **refuses** a translated slogan rather than requiring one, which is the opposite of what it asks of every other word on this site; a slogan that ever is translated is a decision to take out loud, here.

    It stands beside both wordmarks -- the top bar's and the footer's -- which is where a slogan belongs and what makes it a lockup rather than a sentence dropped on the home page. On a narrow screen the media query's `.brand span` rule hides it with the wordmark it follows, so the nav does not wrap.
    """
    slogan = SITE.STRINGS["fr"]["slogan"]
    assert slogan == "Make the numbers vibe", slogan
    for lang in SITE.LANGS:
        assert SITE.STRINGS[lang]["slogan"] == slogan, f"{lang}: a slogan is the brand's own words and is not translated"
    mark = f'<span class="slogan">{slogan}</span>'
    site = _built()
    for lang in SITE.LANGS:
        for page in ("index.html", "download/index.html"):
            html = (site.out / lang / page).read_text(encoding="utf-8")
            assert html.count(mark) == 2, f"{lang}/{page}: the slogan stands beside {html.count(mark)} wordmark(s), not both"
    css = (pathlib.Path(SITE.__file__).parent / "assets" / "site.css").read_text(encoding="utf-8")
    for rule in (".brand .slogan", ".footer-brand .slogan"):
        assert rule in css, f"{rule} is not set, so the slogan is drawn at the wordmark's own weight"

def test_the_window_reads_the_reference_s_words_and_carries_no_copy():
    """One name per category and one word per notion, for the site and the window: calc/i18n/reference.json, which Woodcore's commands tab reads through command_docs since v0.94 -- its STRINGS carry no copy of a category's name or of a word the file says, and its title is the file's own word under the key the window names the tab by (tests/test_commands.py holds what the tab then shows)."""
    try:
        import commands_tab
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    table = docs.reference()
    for lang in SITE.LANGS:
        strings = commands_tab.STRINGS[lang]
        assert strings["tab_commands"] == docs.word("commands", lang)
        said = {docs.category_label(key, lang) for key in ref.CATEGORY_KEYS} | {docs.word(word, lang) for word in table["words"]}
        copies = sorted(key for key, text in strings.items() if key != "tab_commands" and (text in said or key.startswith("ref_cat_")))
        assert not copies, f"the commands tab says again what calc/i18n/reference.json says ({lang}): {copies}"
    source = "".join((ROOT / "calc" / "tools" / name).read_text(encoding="utf-8") for name in ("commands_tab.py", "command_list.py", "command_page_view.py"))
    assert "docs.category_label(" in source and "docs.word(" in source, "the commands tab no longer reads calc/i18n/reference.json"


def test_the_reference_s_words_are_written_once():
    """calc/i18n/reference.json names every category of build_reference.CATEGORIES in the three languages and introduces every category of commands, and website/strings.json says none of it again."""
    table = docs.reference()
    assert set(table["categories"]) == set(ref.CATEGORY_KEYS), sorted(set(table["categories"]) ^ set(ref.CATEGORY_KEYS))
    for lang in docs.REFERENCE_LANGUAGES:
        for key in ref.CATEGORY_KEYS:
            assert docs.category_label(key, lang)
            if key != ref.INTERNAL:
                assert docs.category_lead(key, lang)
        for word in table["words"]:
            assert docs.word(word, lang, n=1)
    text = json.dumps(table, ensure_ascii=False)
    assert "ß" not in text, "Swiss German writes ss"
    for lang in SITE.LANGS:
        again = [k for k in SITE.STRINGS[lang] if k.startswith(("cat_", "catlead_")) or k in table["words"]]
        assert not again, f"website/strings.json ({lang}) says again what calc/i18n/reference.json says: {again}"
    entries = list(table["words"].values()) + [part for category in table["categories"].values() for part in category.values()]
    for entry in entries:
        assert not re.search(r"(?<!\u202f)[:;](?=\s)", entry["fr"]), f"French puts a narrow no-break space before a colon: {entry['fr']!r}"


def test_the_categories_are_in_the_one_order():
    """The categories follow build_reference.CATEGORIES everywhere -- calculating in the report first, the engineer's order -- and the site's navigation lists them so."""
    assert [key for key, _names in ref.CATEGORIES][:2] == ["formula", "display"]
    assert SITE.CATEGORY_KEYS == [key for key, _names in ref.CATEGORIES]
    page = (_built().out / "fr" / "docs" / "index.html").read_text(encoding="utf-8")
    shown = re.findall(r'<h2 id="cat-([a-z]+)"', page)
    assert shown == SITE.CATEGORY_KEYS, shown


def test_every_language_has_the_same_pages():
    slugs = {lang: sorted(p.name for p in (SITE.CONTENT / lang / "tutorial").glob("*.md")) for lang in SITE.LANGS}
    assert slugs["fr"] and all(names == slugs["fr"] for names in slugs.values()), slugs
    for lang in SITE.LANGS:
        assert (SITE.CONTENT / lang / "download.md").is_file()


def test_every_example_the_site_names_exists_and_is_published():
    stems = {e["stem"] for e in _built().examples.values()}
    named = [SITE.CONFIG["hero_example"], SITE.CONFIG["levels_example"]] + list(SITE.CONFIG["gallery"])
    for lang in SITE.LANGS:
        for path in (SITE.CONTENT / lang).rglob("*.md"):
            named += re.findall(r"\{\{example\s+([\w.+-]+)\}\}", path.read_text(encoding="utf-8"))
    for stem in named:
        assert stem in stems, f"{stem}: no such example"
        assert not SITE.Site.masked(stem), f"{stem} is masked and cannot be shown"
    for stem in SITE.CONFIG["gallery"]:
        assert f"gallery_{stem}" in SITE.STRINGS["en"] and _built().examples[stem]["command"] in _built().by_name


def test_every_masked_pattern_masks_something_and_the_norm_tables_are_masked():
    stems = [e["stem"] for e in _built().examples.values()]
    for pattern in SITE.CONFIG["masked"]:
        assert any(SITE.fnmatch.fnmatch(s, pattern) for s in stems), f"{pattern} masks nothing"
    for stem in ("distance-1", "distance-2-L3"):
        assert SITE.Site.masked(stem), stem
    for stem in ("domain-1", "eq-2", "position-2"):
        assert not SITE.Site.masked(stem), stem
    out = _built().out
    for stem in stems:
        if SITE.Site.masked(stem):
            assert not (out / "img" / f"{stem}.png").exists() and not (out / "img" / f"{stem}.svg").exists(), stem


# --- the pages ------------------------------------------------------------------------------------------------

def test_every_command_has_its_page_in_every_language():
    site = _built()
    public = [name for _key, names in ref.CATEGORIES for name in names]
    assert [c["name"] for c in site.commands] == public
    for lang in SITE.LANGS:
        for name in public:
            page = site.out / lang / "docs" / name / "index.html"
            assert page.is_file(), page
        text = (site.out / lang / "docs" / "distance" / "index.html").read_text(encoding="utf-8")
        assert 'lang="' + lang + '"' in text and "#distance(d, connector" in re.sub(r"<[^>]+>", "", text)
        index = json.loads((site.out / "search" / f"{lang}.json").read_text(encoding="utf-8"))
        assert {e["t"] for e in index if e["k"] == "cmd"} == set(public)


def _sidebar(page):
    """The sidebar of a built page, without the site's sections it carries for a narrow screen: (its own navigation, the sections), or None where the page has none."""
    aside = re.search(r'<aside class="sidebar"[^>]*>(.*?)</aside>', page.read_text(encoding="utf-8"), re.S)
    if aside is None:
        return None
    sections = re.search(r'<nav class="sidebar-sections"[^>]*>(.*?)</nav>', aside.group(1), re.S)
    return aside.group(1).replace(sections.group(0), "") if sections else aside.group(1), sections.group(1) if sections else ""


def test_the_sidebar_is_the_one_the_page_s_kind_asks_for():
    """The engineer's decision: the commands beside the commands, the tutorial and one link to the reference beside the tutorial, the versions beside what changed, and nothing beside the gallery -- and on a narrow screen, where the bar at the top hides its links, the sidebar carries them."""
    site = _built()
    out = site.out
    for lang in SITE.LANGS:
        commands, reference = docs.word("commands", lang), SITE.t(lang, "sidebar_reference")
        for page in (out / lang / "docs" / "index.html", out / lang / "docs" / "var" / "index.html"):
            own, _sections = _sidebar(page)
            assert "data-search" in own and own.count('class="cmd') == len(site.commands), page
            assert not re.search(r'href="[^"]*(tutorial|changes|examples)/', own), f"{page}: the commands' sidebar links elsewhere"
            assert f">{commands}</a>" in own, page
            text = page.read_text(encoding="utf-8")
            assert f">{reference}<" not in text, f"{page}: the word «{reference}» has left the pages of the commands"
        crumbs = re.search(r'<p class="crumbs">(.*?)</p>', (out / lang / "docs" / "var" / "index.html").read_text(encoding="utf-8")).group(1)
        assert f">{commands}</a>" in crumbs, crumbs
        opened = re.findall(r"<details( open)?><summary>([^<]+)</summary>", _sidebar(out / lang / "docs" / "var" / "index.html")[0])
        assert [name for is_open, name in opened if is_open] == [SITE.esc(docs.category_label("formula", lang))], opened
        for page in (out / lang / "tutorial").rglob("index.html"):
            if page.relative_to(out).as_posix() in site.moved:
                continue   # a page that only sends the reader on (site.json's `moved`) has no sidebar
            own, _sections = _sidebar(page)
            assert "data-search" in own and own.count('class="step"') == len(site.tutorial[lang]), page
            assert len(re.findall(r'href="[^"]*docs/"', own)) == 1 and f">{reference}</a>" in own, page
            assert 'class="cmd' not in own and not re.search(r'href="[^"]*(changes|examples)/', own), f"{page}: the tutorial's sidebar links elsewhere"
        for page in (out / lang / "changes").rglob("index.html"):
            own, _sections = _sidebar(page)
            assert "data-search" not in own and own.count("<li>") == len(site.changes[lang]), page
            assert not re.search(r'href="[^"]*(docs|tutorial|examples)/', own), f"{page}: the versions' sidebar links elsewhere"
        assert _sidebar(out / lang / "examples" / "index.html") is None, "the gallery carries no sidebar"
    for page in out.rglob("index.html"):
        found = _sidebar(page)
        if found is not None:
            assert "data-menu" in page.read_text(encoding="utf-8"), f"{page}: a sidebar with no ☰ to open it on a narrow screen"
            assert found[1].count("<a ") == len(SITE.SECTIONS), f"{page}: on a narrow screen the sidebar carries the bar's sections"


class _Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.links.append(value)


def test_every_link_and_picture_leads_somewhere():
    out = _built().out
    broken = []
    for page in out.rglob("*.html"):
        if page.name == "404.html":
            continue   # its links are absolute, to the published site
        parser = _Links()
        parser.feed(page.read_text(encoding="utf-8"))
        for link in parser.links:
            if link.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            path = link.split("#")[0].split("?")[0]   # `site.css?v=…` is the file site.css (the stamp only defeats a browser's cache)
            target = (page.parent / path).resolve()
            if path.endswith("/") or target.is_dir():
                target = target / "index.html"
            if not target.exists():
                broken.append(f"{page.relative_to(out)} -> {link}")
    assert not broken, "\n".join(broken[:20])


def test_the_home_page_and_the_tutorial_in_every_language():
    site = _built()
    out = site.out
    for lang in SITE.LANGS:
        home = (out / lang / "index.html").read_text(encoding="utf-8")
        assert SITE.STRINGS[lang]["hero_title"].split()[0] in home and "#domain" in home
        # the code beside each picture is its example's own fence, not a copy of it in site.json
        for stem in (SITE.CONFIG["hero_example"], SITE.CONFIG["levels_example"]):
            assert SITE.highlight(site.examples[stem]["code"]) in home, f"{lang}: the home page does not show the fence of {stem}"
        steps = [p for p in (out / lang / "tutorial").glob("*/index.html") if p.relative_to(out).as_posix() not in site.moved]
        assert len(steps) == len(list((SITE.CONTENT / lang / "tutorial").glob("*.md")))
    assert (out / "index.html").is_file() and (out / "404.html").is_file()


def test_an_address_that_moved_leads_to_the_page_that_replaced_it():
    """A page renamed keeps its old address working (website/site.json's `moved`, v0.96): the tutorial's step on the window was `tutorial/katalog/` while the window was the Katalog. In every language the old address is a page that sends the reader on -- a meta refresh, a line of script and a link, all three to the same address -- and that address is a page of the site, not another page that sends on; the old step's leads to a step of the tutorial."""
    site = _built()
    out = site.out.resolve()
    moved = SITE.CONFIG["moved"]
    assert moved.get("tutorial/katalog/"), "the tutorial's old address for the window's step is no longer kept"
    for old, new in moved.items():
        for lang in SITE.LANGS:
            page = out / lang / old / "index.html"
            assert page.relative_to(out).as_posix() in site.moved, page
            text = page.read_text(encoding="utf-8")
            refresh = html.unescape(re.search(r'<meta http-equiv="refresh" content="0; url=([^"]+)">', text).group(1))
            script = re.search(r'location\.replace\("([^"]+)" \+ location\.hash\)', text).group(1)
            links = [html.unescape(link) for link in re.findall(r'<a [^>]*href="([^"]+)"', text)]
            assert links == [refresh] and script == refresh, (refresh, script, links)
            target = (page.parent / refresh).resolve() / "index.html"
            assert target == (out / lang / new / "index.html").resolve() and target.is_file(), f"{page.relative_to(out)} -> {refresh}"
            assert target.relative_to(out).as_posix() not in site.moved and 'http-equiv="refresh"' not in target.read_text(encoding="utf-8"), target
    slug = moved["tutorial/katalog/"].strip("/").split("/")[-1]
    for lang in SITE.LANGS:
        assert slug in [step["slug"] for step in site.tutorial[lang]], f"{lang}: tutorial/katalog/ leads to no step of the tutorial"
    assert not [w for w in site.warnings if "moved to" in w or "sends nobody" in w], site.warnings


def test_a_moved_address_never_covers_a_page_and_says_where_it_leads_nowhere():
    """page_moved writes nothing over a page the site has at the old address, and says so where the new address has no page -- the two ways a line of site.json's `moved` can go stale."""
    folder = conftest.tmpdir("website_moved")
    site = SITE.Site.__new__(SITE.Site)
    site.out, site.warnings, site.moved, site.written = folder, [], [], 0
    (folder / "fr" / "tutorial" / "kept").mkdir(parents=True)
    (folder / "fr" / "tutorial" / "kept" / "index.html").write_text("a page", encoding="utf-8")
    site.page_moved("fr", "tutorial/kept/", "tutorial/window/")
    assert (folder / "fr" / "tutorial" / "kept" / "index.html").read_text(encoding="utf-8") == "a page" and not site.moved
    assert any("sends nobody" in w for w in site.warnings), site.warnings
    site.page_moved("fr", "tutorial/old/", "tutorial/nowhere/")
    assert site.moved == ["fr/tutorial/old/index.html"] and (folder / "fr" / "tutorial" / "old" / "index.html").is_file()
    assert any("moved to fr/tutorial/nowhere/" in w for w in site.warnings), site.warnings


# --- the installer and the manifest ----------------------------------------------------------------------------

RELEASE = "https://github.com/When-I-hit-the-wall/woodcore-releases/releases/download/v9.9.9/Woodcore-9.9.9-setup.exe"
PAYLOAD = b"MZ" + b"woodcore" * 5000


class _Served(io.BytesIO):
    def __init__(self, data, final):
        super().__init__(data)
        self.final = final

    def geturl(self):
        return self.final


class _Downloads:
    """urllib's urlopen as a Release answers it, for the time of a `with`: `served` maps an address to its bytes, anything else is not found. What an installed Woodcore's download -- and so the build's check -- goes through."""

    def __init__(self, served):
        self.served, self.asked = served, []

    def __enter__(self):
        import urllib.error
        import urllib.request
        self.real = urllib.request.urlopen

        def urlopen(request, timeout=None):
            self.asked.append(request.full_url)
            if request.full_url not in self.served:
                raise urllib.error.URLError("not found")
            return _Served(self.served[request.full_url], request.full_url)

        urllib.request.urlopen = urlopen
        return self

    def __exit__(self, *args):
        import urllib.request
        urllib.request.urlopen = self.real
        return False


def _releases(folder, payload=PAYLOAD, **installer):
    """A releases.json with one version, 9.9.9, its installer recorded as kept on GitHub."""
    info = {"file": "Woodcore-9.9.9-setup.exe", "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "hosted": "github", "url": RELEASE}
    info.update(installer)
    path = folder / "releases.json"
    path.write_text(json.dumps({"schema_version": "1.0", "releases": [{
        "version": "9.9.9", "date": "2026-10-01", "installer": info,
        "notes": {"fr": "Nouveau.", "de": "Neu.", "en": "New."}}]}), encoding="utf-8")
    return path


def test_no_manifest_is_written_before_an_installer_is():
    # A releases.json of its own: the committed one records 0.117.0 on GitHub since it was published (311a920), so it no longer holds the case.
    folder = conftest.tmpdir("website_no_installer")
    releases = _releases(folder, hosted="gitlab", url=None)
    saved = SITE.RELEASES
    SITE.RELEASES = releases
    try:
        site = SITE.Site(folder / "public", images="png")
        site.build()
    finally:
        SITE.RELEASES = saved
    assert site.published is None, "no installer kept on GitHub, so none is published"
    assert not (site.out / "version.json").exists()
    assert not (site.out / "download").exists(), "the installer is never put in the site"
    assert not site.errors and not [w for w in site.warnings if "installer" in w], (site.errors, site.warnings)
    assert any("no installer kept on GitHub" in n for n in site.notices), site.notices


def test_the_manifest_written_with_an_installer_is_one_the_update_check_accepts_and_the_installer_is_never_in_the_site():
    folder = conftest.tmpdir("website_release")
    installer = folder / "Woodcore-9.9.9-setup.exe"
    installer.write_bytes(PAYLOAD)
    releases = _releases(folder)
    saved = SITE.RELEASES
    SITE.RELEASES = releases
    try:
        out = folder / "public"
        site = SITE.Site(out, images="png", installer=installer)
        site.build()
        manifest = json.loads((out / "version.json").read_text(encoding="utf-8"))
        assert updates.validate(manifest, updates.FEED_URL) == [], updates.validate(manifest, updates.FEED_URL)
        assert manifest["version"] == "9.9.9" and manifest["installer"]["url"] == RELEASE, "the address is the one releases.json records, read as it is"
        assert "changes" not in manifest, "no page says what 9.9.9 changes, so the manifest names none"
        assert not (out / "download").exists() and not list(out.rglob("*.exe")), "no installer in the site: Cloudflare Pages takes no file over 25 MiB"
        assert not site.errors, site.errors
        digest = hashlib.sha256(PAYLOAD).hexdigest()
        for lang in SITE.LANGS:
            page = (out / lang / "download" / "index.html").read_text(encoding="utf-8")
            assert "9.9.9" in page and digest in page, lang
            assert f'href="{RELEASE}"' in page, f"{lang}: the button does not lead to the Release"
            assert not re.search(r'href="[^"]*github[^"]*"[^>]*\sdownload[\s>]', page), f"{lang}: a `download` attribute, which a link to another site ignores"
            assert SITE.esc(SITE.STRINGS[lang]["download_origin"]) in page, f"{lang}: the page does not say where the installer comes from"
        # an installer that is not the one recorded is left out, and no manifest names it (a preview: a warning, nothing is deployed from it)
        installer.write_bytes(PAYLOAD + b"!")
        site = SITE.Site(out, images="png", installer=installer)
        site.build()
        assert not (out / "version.json").exists() and site.published is None
        assert any("is not the one website/releases.json records" in w for w in site.warnings), site.warnings
    finally:
        SITE.RELEASES = saved


def test_a_check_that_fails_stops_the_build_and_no_manifest_is_written():
    folder = conftest.tmpdir("website_fetch")
    releases = _releases(folder)
    saved = SITE.RELEASES
    SITE.RELEASES = releases
    try:
        out = folder / "public"
        args = ["--out", str(out), "--images", "png", "--fetch-installer"]
        with _Downloads({RELEASE: PAYLOAD}) as net:
            assert SITE.main(args) == 0
        assert net.asked == [RELEASE], "downloaded once, without a token, from the address releases.json records"
        manifest = json.loads((out / "version.json").read_text(encoding="utf-8"))
        assert updates.validate(manifest, updates.FEED_URL) == [] and not list(out.rglob("*.exe"))
        for name, served in (("a file that is not the one recorded", {RELEASE: PAYLOAD + b"!"}), ("a file of the wrong content", {RELEASE: PAYLOAD[::-1]}), ("no answer", {})):
            with _Downloads(served):
                assert SITE.main(args) == 1, f"{name}: the build went on"
            assert not (out / "version.json").exists(), f"{name}: a manifest was written"
    finally:
        SITE.RELEASES = saved


def test_the_installers_of_the_gitlab_years_are_neither_fetched_nor_offered_and_say_nothing():
    real = json.loads(SITE.RELEASES.read_text(encoding="utf-8"))["releases"]
    legacy = [r for r in real if isinstance(r.get("installer"), dict) and r["installer"].get("hosted") == "gitlab"]
    assert len(legacy) >= 10, "the ten versions published before 0.117.0"
    site = SITE.Site.__new__(SITE.Site)
    site.releases, site.warnings, site.notices, site.errors = legacy, [], [], []
    site.installer_source, site.fetch_installer, site.published = None, True, None
    with _Downloads({}) as net:
        site.place_installer()
    assert net.asked == [] and site.published is None, "nothing is fetched for them"
    assert site.warnings == [] and site.errors == [], (site.warnings, site.errors)
    assert not any(site.has_download(r) for r in legacy), "and the download page lists none of them"


def test_every_release_with_an_installer_says_where_it_is_hosted():
    real = json.loads(SITE.RELEASES.read_text(encoding="utf-8"))["releases"]
    recorded = [r for r in real if isinstance(r.get("installer"), dict) and r["installer"].get("sha256")]
    assert recorded
    for release in recorded:
        info = release["installer"]
        assert info.get("hosted") in SITE.HOSTED, f"{release['version']}: hosted is {info.get('hosted')!r}"
        if info["hosted"] == "github":
            assert info["url"] == publish.asset_url(release["version"], info["file"]), f"{release['version']}: the address is written by publish.py and nowhere else"
            assert updates.installer_address_problem(info["url"], updates.FEED_URL) == ""
    site = SITE.Site.__new__(SITE.Site)
    for bad, words in (({"file": "x", "size": 1, "sha256": "ab" * 32}, "hosted"),
                       ({"file": "x", "size": 1, "sha256": "ab" * 32, "hosted": "elsewhere"}, "hosted"),
                       ({"file": "x", "size": 1, "sha256": "ab" * 32, "hosted": "github"}, "not HTTPS"),
                       ({"file": "x", "size": 1, "sha256": "ab" * 32, "hosted": "github", "url": "https://example.com/x.exe"}, "neither on the manifest")):
        site.releases, site.errors = [{"version": "1.0.0", "installer": bad}], []
        site.check_releases()
        assert site.errors and words in site.errors[0], (bad, site.errors)


def test_the_build_refuses_a_file_or_a_count_cloudflare_would_refuse():
    folder = conftest.tmpdir("website_limits")
    saved = SITE.FILE_LIMIT, SITE.FILES_LIMIT
    try:
        SITE.FILE_LIMIT = 1000
        site = SITE.Site(folder / "big", images="png")
        site.build()
        assert any("Cloudflare Pages takes no file over" in e for e in site.errors), site.errors
        assert SITE.main(["--out", str(folder / "big"), "--images", "png"]) == 1
        SITE.FILE_LIMIT, SITE.FILES_LIMIT = saved[0], 10
        site = SITE.Site(folder / "many", images="png")
        site.build()
        assert any("no more than 10" in e for e in site.errors), site.errors
    finally:
        SITE.FILE_LIMIT, SITE.FILES_LIMIT = saved
    assert SITE.FILE_LIMIT == 25 * 2**20 and SITE.FILES_LIMIT == 20_000
    assert not _built().errors, "the site as it is stays under both"
    assert max(p.stat().st_size for p in _built().out.rglob("*") if p.is_file()) < SITE.FILE_LIMIT


def test_every_version_published_says_what_it_changes_in_every_language():
    site = _built()
    versions = {lang: [c["version"] for c in site.changes[lang]] for lang in SITE.LANGS}
    assert versions["fr"] and all(v == versions["fr"] for v in versions.values()), versions
    assert versions["fr"] == sorted(versions["fr"], key=SITE.version_tuple, reverse=True), "newest first"
    for lang in SITE.LANGS:
        assert (SITE.CONTENT / lang / "changes.md").is_file()
        for version in versions[lang]:
            text = (site.out / lang / "changes" / version / "index.html").read_text(encoding="utf-8")
            assert re.search(r'<h2 id="[^"]+">', text), f"{lang} {version}: no section"
        index = (site.out / lang / "changes" / "index.html").read_text(encoding="utf-8")
        missing = [v for v in versions[lang] if f'href="{v}/"' not in index]   # the list links each page, relative to itself
        assert not missing, f"{lang}: the list names no page for {missing}"
    for release in json.loads(SITE.RELEASES.read_text(encoding="utf-8"))["releases"]:
        if isinstance(release.get("installer"), dict):
            assert release["version"] in versions["fr"], f"{release['version']} is published and no page says what it changes"


def test_the_manifest_names_the_page_of_what_the_version_changes():
    folder = conftest.tmpdir("website_changes")
    payload = b"MZ" + b"changes" * 3000
    version = _built().changes["fr"][0]["version"]
    installer = folder / f"Woodcore-{version}-setup.exe"
    installer.write_bytes(payload)
    releases = folder / "releases.json"
    release_url = publish.asset_url(version, installer.name)
    releases.write_text(json.dumps({"schema_version": "1.0", "releases": [{
        "version": version, "date": "2026-09-23",
        "installer": {"file": installer.name, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "hosted": "github", "url": release_url},
        "notes": {"fr": "a", "de": "b", "en": "c"}}]}), encoding="utf-8")
    saved = SITE.RELEASES
    SITE.RELEASES = releases
    try:
        out = folder / "public"
        SITE.Site(out, images="png", installer=installer).build()
        manifest = json.loads((out / "version.json").read_text(encoding="utf-8"))
        for lang in SITE.LANGS:
            assert manifest["changes"][lang] == SITE.CONFIG["base_url"] + f"{lang}/changes/{version}/"
            assert updates.changes(manifest, lang) == manifest["changes"][lang], "the update window would not offer it"
            assert f"changes/{version}/" in (out / lang / "download" / "index.html").read_text(encoding="utf-8")
    finally:
        SITE.RELEASES = saved


def test_a_list_may_carry_a_list_and_a_line_after_it():
    page = SITE.Page(None, "fr", "fr/x/index.html", "none")
    html_text, _toc = SITE.markdown("- one\n  - a\n  - b\n  after\n- two\n\nnext", page)
    assert html_text == "<ul><li>one<ul><li>a</li><li>b</li></ul><p>after</p></li><li>two</li></ul>\n<p>next</p>", html_text
    html_text, _toc = SITE.markdown("1. first\n   - sub\n2. second", page)
    assert html_text == "<ol><li>first<ul><li>sub</li></ul></li><li>second</li></ol>", html_text


def test_the_workflow_builds_the_site_with_the_typst_the_program_carries_and_trusts_only_what_it_must():
    path = ROOT / ".github" / "workflows" / "site.yml"
    assert not (ROOT / ".gitlab-ci.yml").exists(), "the site is no longer built by GitLab"
    ci = path.read_text(encoding="utf-8")
    assert "--fetch-installer" in ci and "website/build.py --out public" in ci, "the build, which checks the installer and exits with 1 where it is not the one recorded"
    # its Typst is the pinned one, installed by the one recipe that checks its SHA-256 (v0.117): no version written here, no second download
    assert "python tests/bootstrap.py --typst-only" in ci, "the site installs Typst through tests/bootstrap.py"
    pinned = (ROOT / "typst-version.txt").read_text(encoding="utf-8").strip()
    assert "TYPST_VERSION" not in ci and "releases/download" not in ci and pinned not in ci, "a Typst version written in site.yml: typst-version.txt is its one source"
    assert "public/" in (ROOT / ".gitignore").read_text(encoding="utf-8")
    # what may start it: a push and a hand, never a pull request (which would hand the secrets to a branch nobody reviewed)
    triggers = re.search(r"^on:\n((?:[ \t]+.*\n|\n)+?)(?=^\S)", ci, re.M).group(1)
    assert re.findall(r"^  ([a-z_]+):", triggers, re.M) == ["push", "workflow_dispatch"], triggers
    assert "pull_request" not in ci.replace("never `pull_request` or `pull_request_target`", "")
    # what it may do: read the repository, and nothing else
    assert re.search(r"^permissions:\n  contents: read\n(?=\S|\n)", ci, re.M), "the token of the workflow may only read"
    assert not re.search(r"^\s+(contents|packages|id-token|pull-requests|actions): write", ci, re.M)
    # whom it trusts: the actions GitHub publishes, pinned by commit; wrangler at an exact version; the Cloudflare token only in the deploy step
    for action in re.findall(r"^\s+- uses: (\S+)", ci, re.M):
        assert action.startswith("actions/") and re.search(r"@[0-9a-f]{40}$", action), f"{action}: only GitHub's own actions, pinned by the commit"
    assert re.search(r'WRANGLER_VERSION: "\d+\.\d+\.\d+"', ci) and 'wrangler@${WRANGLER_VERSION}' in ci
    assert '--branch="${PAGES_BRANCH}"' in ci and "PAGES_BRANCH=" in ci and "--project-name=woodcore" in ci
    assert "production_branch" in ci and "PAGES_BRANCH: " not in ci, "the branch is read from the Pages project, not written down: a wrong one is a Preview and a green run proves nothing"
    assert ci.count("secrets.CLOUDFLARE_API_TOKEN") == 1 and ci.count("secrets.CLOUDFLARE_ACCOUNT_ID") == 1
    deploy = ci[ci.index("- name: Deploy to Cloudflare Pages"):]
    assert "secrets.CLOUDFLARE_API_TOKEN" in deploy and "secrets" not in ci[:ci.index("- name: Deploy to Cloudflare Pages")].replace("# ", "").split("jobs:")[1]
    assert "cancel-in-progress: true" in ci and "paths-ignore:" in ci


def test_every_copy_of_the_site_address_is_site_jsons():
    """The installed program has no website/ to read the address from, so every copy it carries -- and the licence, the installer's script and the README, which name it -- is held equal to website/site.json here (docs/architecture/principles.md rule 1)."""
    import legal as legal_texts
    base = SITE.CONFIG["base_url"]
    assert base == "https://woodcore.pages.dev/"
    assert updates.FEED_URL == base + "version.json"
    assert updates.INSTALLER_HOST == "github.com" and updates.INSTALLER_PREFIX == f"/{SITE.CONFIG['releases_repo']}/releases/download/"
    assert publish.repository() == SITE.CONFIG["releases_repo"]
    assert legal_texts.SITE == base
    iss = (ROOT / "packaging" / "woodcore.iss").read_text(encoding="utf-8", errors="replace")
    assert f"AppPublisherURL={base}\n" in iss.replace("\r\n", "\n") and f"AppSupportURL={base}\n" in iss.replace("\r\n", "\n")
    for lang in SITE.LANGS:   # utf-8-sig: the licence keeps its BOM, which Inno Setup needs (tests/test_legal.py)
        assert base in (ROOT / "legal" / f"LICENSE-{lang}.txt").read_text(encoding="utf-8-sig"), f"LICENSE-{lang}.txt does not name {base}"
    assert base in (ROOT / "README.md").read_text(encoding="utf-8")


def test_no_live_file_names_the_retired_host():
    """The site and the installers left GitLab in v0.117: nothing the program, the installer, the licence or the site carries may still name its host, its CI file or its tokens. (website/releases.json keeps the installers' file names of those years, and `hosted: gitlab` says so.)"""
    retired = re.compile(r"ti\.bfh\.ch|gitlab\.(?:com|ti)|\.gitlab-ci|GITLAB_TOKEN|CI_JOB_TOKEN|CI_API_V4_URL|CI_PROJECT_ID", re.I)
    suffixes = {".py", ".json", ".md", ".txt", ".yml", ".iss", ".js", ".css", ".html", ".typ", ".bat", ".svg"}
    files = [ROOT / "README.md"]
    for folder in ("calc", "packaging", "legal", "website", ".github"):
        files += [p for p in (ROOT / folder).rglob("*") if p.is_file() and p.suffix.lower() in suffixes and "__pycache__" not in p.parts]
    # the word itself, anywhere else than where the history is told: the `hosted: gitlab` marker and what it means (the build, site.json's comment) and the page of changes that announces the move
    history = {"website/build.py", "website/site.json", "website/content/fr/changes/0.117.0.md", "website/content/de/changes/0.117.0.md", "website/content/en/changes/0.117.0.md"}
    found = []
    for path in files:
        if path == SITE.RELEASES:
            continue
        relative = path.relative_to(ROOT).as_posix()
        pattern = retired if relative in history else re.compile(retired.pattern + "|gitlab", re.I)
        for number, line in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1):
            if pattern.search(line):
                found.append(f"{relative}:{number}: {line.strip()[:100]}")
    assert not found, "\n".join(found)


def test_the_svg_pages_are_made_lighter_and_drawn_the_same():
    glyph = "g97A53DD53F1F3AFACE25FEC65E373B85"
    text = ('<svg>\n  <g class="typst-group">\n    <path class="typst-shape" fill-rule="nonzero" d="M 0.5609999 -0.0000001 L 12.3456789 4.25"/>\n'
            f'    <use xlink:href="#{glyph}" x="5.25" y="0" fill="#000000"/>\n    <image xlink:href="data:image/png;base64,AAAA1234567BBBB"/>\n  </g>\n'
            f'  <defs><symbol id="{glyph}"><path d="M 0 0m 8.129 5.841 c 0 0.56 -0.29 0.99"/></symbol></defs>\n</svg>')
    small = SITE.minify_svg(text)
    assert small == ('<svg><g><path d="M.56 0L12.35 4.25"/><use href="#g0" x="5.25"/><image href="data:image/png;base64,AAAA1234567BBBB"/></g>'
                     '<defs><symbol id="g0"><path d="M0 0m8.13 5.84c0 .56-.29 .99"/></symbol></defs></svg>'), small


def test_every_example_is_compiled_in_the_page_s_language_and_a_page_alike_is_stored_once():
    if not conftest.have_typst():
        raise conftest.Skip("typst is not on PATH")
    out = conftest.tmpdir("website_langs")
    site = SITE.Site(out, images="svg")
    site.examples = {stem: site.examples[stem] for stem in ("position-2", "eq-2")}
    site.render_examples()
    assert not site.failures, site.failures
    for stem in site.examples:
        assert all(site.image_exists(stem, lang) for lang in SITE.LANGS), stem
    worded = {site.image_path("position-2", lang) for lang in SITE.LANGS}
    assert len(worded) == 3, "a page with the engine's words is one page per language"
    assert len({site.image_path("eq-2", lang) for lang in SITE.LANGS}) == 1, "a formula the three languages print alike is one file"
    assert len(list((out / "img").glob("*.svg"))) == 4


def test_typst_is_highlighted():
    code = SITE.highlight('#verify-compression("S001", N: -40) // Stütze')
    assert '<span class="f">#verify-compression</span>' in code
    assert '<span class="s">&quot;S001&quot;</span>' in code
    assert '<span class="n">N</span>' in code and '<span class="d">-40</span>' in code
    assert '<span class="c">// Stütze</span>' in code


# --- publishing ------------------------------------------------------------------------------------------------

def test_the_publishing_refuses_a_version_with_no_notes():
    data = {"releases": [{"version": "9.9.9", "notes": {"fr": "x", "de": "", "en": "y"}}]}
    for version, words in (("9.9.8", "no entry"), ("9.9.9", "no notes in de")):
        try:
            publish.entry_for(data, version)
        except publish.PublishError as exc:
            assert words in str(exc), exc
        else:
            raise AssertionError(f"{version} was accepted")
    releases = publish.load_releases()
    assert publish.entry_for(releases, releases["releases"][0]["version"]), "the committed releases.json carries its notes"


class _GitHub:
    """What GitHub says to publish.py, and what it was sent: a fake `opener` that answers by method and path, so that the requests built are the ones that would go out."""

    def __init__(self, release=None, assets=(), upload_url="https://uploads.github.com/repos/When-I-hit-the-wall/woodcore-releases/releases/7/assets{?name,label}"):
        self.release, self.assets, self.upload_url, self.sent = release, list(assets), upload_url, []

    def __call__(self, request, timeout):
        import io
        import urllib.error
        body = request.data.read() if hasattr(request.data, "read") else request.data
        self.sent.append({"method": request.get_method(), "url": request.full_url, "headers": dict(request.header_items()), "body": body})
        path = request.full_url.split("github.com", 1)[1]
        if request.get_method() == "GET" and "/releases/tags/" in path:
            if self.release is None:
                raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, io.BytesIO(b'{"message": "Not Found"}'))
            return _Answer({**self.release, "assets": self.assets, "upload_url": self.upload_url})
        if request.get_method() == "POST" and path.endswith("/releases"):
            self.release = {"id": 7}
            return _Answer({"id": 7, "assets": [], "upload_url": self.upload_url})
        if request.get_method() == "DELETE":
            self.assets = [a for a in self.assets if f"/assets/{a['id']}" not in path]
            return _Answer(None)
        if request.get_method() == "POST" and "/assets" in path:
            name = urllib.parse.parse_qs(urllib.parse.urlsplit(request.full_url).query)["name"][0]
            return _Answer({"id": 9, "name": name, "browser_download_url": f"https://github.com/{publish.repository()}/releases/download/v9.9.9/{name}"})
        raise AssertionError(f"unexpected request {request.get_method()} {request.full_url}")


class _Answer:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return b"" if self.data is None else json.dumps(self.data).encode("utf-8")


def _installer(name="Woodcore-9.9.9-setup.exe", payload=b"MZ-installer"):
    folder = conftest.tmpdir("publish_upload")
    path = folder / name
    path.write_bytes(payload)
    return path


def test_the_installer_is_sent_to_the_release_of_its_version_in_the_public_repository():
    assert publish.repository() == SITE.CONFIG["releases_repo"], "the one place the repository is written is website/site.json"
    assert publish.asset_url("9.9.9", "Woodcore-9.9.9-setup.exe") == "https://github.com/When-I-hit-the-wall/woodcore-releases/releases/download/v9.9.9/Woodcore-9.9.9-setup.exe"
    assert publish.address_problem(publish.asset_url("9.9.9", "Woodcore-9.9.9-setup.exe")) == "", "the address is one the installed program accepts"
    github = _GitHub()   # no Release yet: created, then the asset uploaded to the address GitHub itself gave
    url = publish.upload(_installer(), "9.9.9", "secret", opener=github)
    assert url == publish.asset_url("9.9.9", "Woodcore-9.9.9-setup.exe")
    methods = [(s["method"], s["url"].split("github.com", 1)[1].split("?")[0]) for s in github.sent]
    assert methods == [("GET", "/repos/When-I-hit-the-wall/woodcore-releases/releases/tags/v9.9.9"),
                       ("POST", "/repos/When-I-hit-the-wall/woodcore-releases/releases"),
                       ("POST", "/repos/When-I-hit-the-wall/woodcore-releases/releases/7/assets")], methods
    created = json.loads(github.sent[1]["body"])
    assert created["tag_name"] == "v9.9.9" and created["draft"] is False and "/fr/changes/9.9.9/" in created["body"], created
    assert "notes" not in created, "the notes are releases.json's: a second copy would age"
    upload = github.sent[2]
    assert upload["body"] == b"MZ-installer" and upload["headers"]["Content-length"] == str(len(b"MZ-installer"))
    assert upload["headers"]["Content-type"] == "application/octet-stream" and upload["url"].endswith("?name=Woodcore-9.9.9-setup.exe")
    for sent in github.sent:
        assert sent["headers"]["Authorization"] == "Bearer secret" and sent["headers"]["Accept"] == "application/vnd.github+json"
        assert sent["headers"]["X-github-api-version"] == publish.API_VERSION


def test_a_release_that_exists_is_reused_and_an_asset_that_exists_is_never_replaced_unless_asked():
    path = _installer()
    release = {"id": 7}
    github = _GitHub(release=release, assets=[{"id": 3, "name": path.name}])
    try:
        publish.upload(path, "9.9.9", "secret", opener=github)
    except publish.PublishError as exc:
        assert "--replace" in str(exc) and path.name in str(exc), exc
    else:
        raise AssertionError("an asset already there was replaced without being asked")
    assert [s["method"] for s in github.sent] == ["GET"], "nothing was created, deleted or uploaded"
    assert publish.upload(path, "9.9.9", "secret", replace=True, opener=github) == publish.asset_url("9.9.9", path.name)
    assert [s["method"] for s in github.sent[1:]] == ["GET", "DELETE", "POST"], "the old asset deleted, then the new one sent, the Release not created again"
    assert github.sent[2]["url"].endswith("/releases/assets/3")


def test_the_token_goes_to_github_and_nowhere_else_and_is_not_replayed_on_a_redirect():
    path = _installer()
    github = _GitHub(release={"id": 7}, upload_url="https://uploads.evil.example/repos/x/y/releases/7/assets{?name,label}")
    try:
        publish.upload(path, "9.9.9", "secret", opener=github)
    except publish.PublishError as exc:
        assert "uploads.evil.example" in str(exc), exc
    else:
        raise AssertionError("an upload address on another host was used")
    assert all("evil" not in s["url"] for s in github.sent), "nothing, the token above all, was sent to the other host"
    request = urllib.request.Request("https://api.github.com/x")
    request.add_unredirected_header("Authorization", "Bearer secret")
    assert "Authorization" not in request.headers and request.unredirected_hdrs["Authorization"] == "Bearer secret", "urllib does not replay an unredirected header on a redirect"
    text = (ROOT / "packaging" / "publish.py").read_text(encoding="utf-8")
    assert "add_unredirected_header" in text


def test_only_the_woodcore_token_is_read_and_a_refusal_from_github_is_said():
    saved = {name: os.environ.pop(name, None) for name in ("WOODCORE_GITHUB_TOKEN", "GITHUB_TOKEN", "GH_TOKEN")}

    class NoTerminal:
        """A stdin that is not a terminal: Windows says `isatty()` of NUL and of a console alike, and publish.token() would then wait for a password nobody types."""
        def isatty(self):
            return False

    real_stdin, sys.stdin = sys.stdin, NoTerminal()
    try:
        os.environ["GITHUB_TOKEN"] = "a-token-for-everything"
        try:
            publish.token()
        except publish.PublishError as exc:
            assert "WOODCORE_GITHUB_TOKEN" in str(exc) and "Contents" in str(exc), exc
        else:
            raise AssertionError("GITHUB_TOKEN, a token for everything, was read")
        os.environ["WOODCORE_GITHUB_TOKEN"] = "the-fine-grained-one"
        assert publish.token() == "the-fine-grained-one"
    finally:
        sys.stdin = real_stdin
        for name, value in saved.items():
            os.environ.pop(name, None)
            if value is not None:
                os.environ[name] = value

    def refusing(request, timeout):
        import io
        import urllib.error
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, io.BytesIO(b'{"message": "Resource not accessible by personal access token"}'))

    try:
        publish.upload(_installer(), "9.9.9", "secret", opener=refusing)
    except publish.PublishError as exc:
        assert "403" in str(exc) and "Resource not accessible" in str(exc), exc
    else:
        raise AssertionError("a refusal was taken for an upload")


def test_the_release_records_what_the_site_checks_the_installer_against():
    import datetime
    data = {"releases": [{"version": "9.9.9", "notes": {"fr": "a", "de": "b", "en": "c"}}]}
    url = publish.asset_url("9.9.9", "Woodcore-9.9.9-setup.exe")
    publish.record(data, data["releases"][0], "Woodcore-9.9.9-setup.exe", 12, "ab" * 32, url, today=datetime.date(2026, 10, 1))
    assert data["releases"][0]["installer"] == {"file": "Woodcore-9.9.9-setup.exe", "size": 12, "sha256": "ab" * 32, "hosted": "github", "url": url}
    assert data["releases"][0]["date"] == "2026-10-01"
    site = SITE.Site.__new__(SITE.Site)
    site.releases = data["releases"]
    assert site.release_with_installer() is data["releases"][0]


def test_the_dry_run_sends_nothing_and_writes_nothing():
    folder = conftest.tmpdir("publish_dry")
    (folder / "Woodcore-9.9.9-setup.exe").write_bytes(b"MZ")
    releases = folder / "releases.json"
    releases.write_text(json.dumps({"releases": [{"version": "9.9.9", "notes": {"fr": "a", "de": "b", "en": "c"}}]}), encoding="utf-8")
    before = releases.read_text(encoding="utf-8")
    saved = publish.DIST, publish.RELEASES
    publish.DIST, publish.RELEASES = folder, releases
    try:
        assert publish.main(["--version", "9.9.9", "--dry-run"]) == 0
        assert publish.main(["--version", "9.9.7", "--dry-run"]) == 1, "no installer for that version"
    finally:
        publish.DIST, publish.RELEASES = saved
    assert releases.read_text(encoding="utf-8") == before


def test_a_command_s_page_is_the_condensed_page_with_its_bubbles():
    """UI-011 (spec 2026-10-24-onglet-commandes-pages, issue #115): the page of #var in each language carries the line of the command, the key points, the table of the arguments and a bubble for each argument and each default; every print a bubble shows is a published sheet; the norm tables of #distance stay off the site; the search reads the name and the lead alone."""
    import command_pages
    site = _built()
    for lang in SITE.LANGS:
        page = (site.out / lang / "docs" / "var" / "index.html").read_text(encoding="utf-8")
        assert 'class="cmdline"' in page and 'class="keys"' in page and 'class="atab"' in page, lang
        assert html.escape(command_pages.entry("var")["lead"][lang], quote=False).split()[0] in page
        for arg in command_pages.entry("var")["arguments"]:
            assert f'id="tip-arg-{html.escape(arg)}"' in page, (lang, arg)
        assert 'id="tip-val-display"' in page and 'data-tip="val-display"' in page
        for sheet in set(re.findall(r"url\(\.\./\.\./\.\./values/([^)]+)\)", page)):
            assert (site.out / "values" / sheet).is_file(), sheet
        distance = (site.out / lang / "docs" / "distance" / "index.html").read_text(encoding="utf-8")
        assert "values/" + lang + "-distance.png" not in distance and not (site.out / "values" / f"{lang}-distance.png").exists()
        index = json.loads((site.out / "search" / f"{lang}.json").read_text(encoding="utf-8"))
        var = next(e for e in index if e["k"] == "cmd" and e["t"] == "var")
        assert set(var) == {"t", "u", "k", "c", "s"}, "a command is searched by its name and its lead, nothing else"
    assert "[data-tipbox]" in (ROOT / "website" / "assets" / "site.js").read_text(encoding="utf-8")
