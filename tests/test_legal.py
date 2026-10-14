"""Woodcore's copyright, its licence and the third-party notices (legal/, packaging/notices.py, calc/tools/legal.py, packaging/woodcore.iss).

The engineer's choice (23.09.2026): «© 2026 Florian Lamprecht», woodcore@pineo.ch, a short proprietary licence in French, German and English -- not open source for now --, and the licences of what the installer carries, shipped with the program and published on the site. What is held here: the three licences say the same thing in their three languages, the notices are the ones the pinned versions call for, the installer shows the licence and names its holder, the program carries the files, and the window shows the line and the dialog.
"""

import os
import re
import sys

import conftest
from conftest import ROOT

LEGAL = ROOT / "legal"
PACKAGING = ROOT / "packaging"
LANGS = ("fr", "de", "en")


def _licence(lang):
    return (LEGAL / f"LICENSE-{lang}.txt").read_text(encoding="utf-8-sig")


def test_the_three_licences_name_the_holder_and_say_the_same_things():
    sections = {}
    for lang in LANGS:
        raw = (LEGAL / f"LICENSE-{lang}.txt").read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf"), f"LICENSE-{lang}.txt without its BOM: Inno Setup would read it as ANSI"
        text = _licence(lang)
        assert "© 2026 Florian Lamprecht" in text and "woodcore@pineo.ch" in text, lang
        assert "Art. 100" in text or "art. 100" in text, f"{lang}: the reservation of gross negligence is gone"
        assert "THIRD-PARTY-NOTICES.txt" in text and '"updates": {"enabled": false}' in text, lang
        sections[lang] = re.findall(r"^(\d+)\. ", text, re.M)
    assert sections["fr"] == sections["de"] == sections["en"] == [str(n) for n in range(1, 11)], sections
    assert "ß" not in _licence("de"), "Swiss German writes ss"


def test_the_notices_are_what_the_pinned_versions_call_for():
    sys.path.insert(0, str(PACKAGING))
    import notices
    assert notices.stale() is None, notices.stale()
    text = (LEGAL / "THIRD-PARTY-NOTICES.txt").read_text(encoding="utf-8")
    pins = notices.pins()
    for package in ("openpyxl", "pypdf", "pyside6", "pyinstaller", "typst"):
        assert pins[package] in text, f"{package} {pins[package]} is not named in the notices"
    for words in ("GNU LESSER GENERAL PUBLIC LICENSE", "GNU GENERAL PUBLIC LICENSE", "Apache License", "PYTHON SOFTWARE FOUNDATION LICENSE", "SIL OPEN FONT LICENSE", "Bootloader Exception"):
        assert words in text, f"the notices lack {words}"
    used = {f for c in notices.components(pins) for f in c[5]}
    assert used == {p.name for p in (LEGAL / "licenses").iterdir()}, "a licence text nothing names, or one named and missing"


def test_the_notices_go_stale_when_a_pin_moves():
    sys.path.insert(0, str(PACKAGING))
    import notices
    saved = notices.pins
    notices.pins = lambda: dict(saved(), pypdf="99.0.0")
    try:
        assert notices.stale() and "notices.py" in notices.stale()
    finally:
        notices.pins = saved


def test_the_installer_shows_the_licence_and_names_its_holder():
    iss = (PACKAGING / "woodcore.iss").read_text(encoding="utf-8")
    assert re.search(r"^AppPublisher=Florian Lamprecht$", iss, re.M)
    assert re.search(r"^AppCopyright=© 2026 Florian Lamprecht$", iss, re.M)
    assert re.search(r"^AppContact=woodcore@pineo\.ch$", iss, re.M)
    for lang in LANGS:
        m = re.search(rf'^Name: "{lang}";.*LicenseFile: "([^"]+)"', iss, re.M)
        assert m, f"the {lang} wizard shows no licence"
        assert (PACKAGING / m.group(1).replace("\\", "/")).resolve() == (LEGAL / f"LICENSE-{lang}.txt").resolve()
    build = (PACKAGING / "build.py").read_text(encoding="utf-8")
    assert "LegalCopyright" in build and "notices.stale()" in build
    assert 'tree("legal")' in (PACKAGING / "woodcore.spec").read_text(encoding="utf-8"), "the program would not carry legal/"


def _qt():
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def test_the_window_s_words_and_files_exist_in_every_language():
    _qt()
    import legal
    keys = set(legal.TEXTS["fr"])
    for lang in LANGS:
        assert set(legal.TEXTS[lang]) == keys, lang
        assert legal.licence_path(lang).is_file()
        assert "ß" not in "".join(legal.TEXTS["de"].values())
    assert legal.notices_path().is_file()
    assert legal.copyright_line() == "© 2026 Florian Lamprecht · woodcore@pineo.ch"


def test_the_about_dialog_opens_the_licence_and_the_notices():
    _qt()
    import legal
    opened = []
    saved = legal.QDesktopServices.openUrl
    legal.QDesktopServices.openUrl = staticmethod(lambda url: opened.append(url.toLocalFile()) or True)
    try:
        for lang in LANGS:
            dialog = legal.AboutDialog(None, lang)
            texts = " ".join(w.text() for w in dialog.findChildren(legal.QLabel))
            assert "© 2026 Florian Lamprecht" in texts and "woodcore@pineo.ch" in texts, lang
            dialog.licence_button.click()
            dialog.notices_button.click()
            dialog.deleteLater()
    finally:
        legal.QDesktopServices.openUrl = saved
    assert [os.path.basename(p) for p in opened] == [x for lang in LANGS for x in (f"LICENSE-{lang}.txt", "THIRD-PARTY-NOTICES.txt")]


def test_the_start_page_carries_the_copyright_line():
    _qt()
    import home_page
    from PySide6.QtWidgets import QLabel
    page = home_page.HomeWindow(lambda file: False)
    lines = [w for w in page.findChildren(QLabel) if "© 2026 Florian Lamprecht" in w.text()]
    assert lines and "woodcore@pineo.ch" in lines[0].text() and lines[0].objectName() == "meta"
    page.close()


def test_the_file_menu_offers_about():
    _qt()
    import legal
    import test_home
    window = test_home._main_window()
    menu = window.menuBar().actions()[0].menu()
    texts = [a.text() for a in menu.actions() if not a.isSeparator()]
    assert legal.text(window.lang, "about_menu") in texts, texts


def test_the_site_publishes_the_licence_the_notices_and_a_legal_page():
    build = (ROOT / "website" / "build.py").read_text(encoding="utf-8")
    assert "self.page_legal(lang)" in build and 'class="footer-legal">© 2026 Florian Lamprecht' in build and "mailto:woodcore@pineo.ch" in build
    names = re.search(r"LEGAL_FILES = \(([^)]*)\)", build).group(1)
    for name in re.findall(r'"([^"]+)"', names):
        assert (LEGAL / name).is_file(), name
    for lang in LANGS:
        page = (ROOT / "website" / "content" / lang / "legal.md").read_text(encoding="utf-8")
        assert "© 2026 Florian Lamprecht" in page and "woodcore@pineo.ch" in page and "version.json" in page, lang
        for target in re.findall(r"\]\((/legal/[^)]+)\)", page):
            assert (LEGAL / target.split("/")[-1]).is_file(), (lang, target)
        assert f"/legal/LICENSE-{lang}.txt" in page and "/legal/THIRD-PARTY-NOTICES.txt" in page, lang
