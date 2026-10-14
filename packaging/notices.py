"""legal/THIRD-PARTY-NOTICES.txt: the licences of the third-party software the installed Woodcore carries.

    python packaging/notices.py            writes it
    python packaging/notices.py --check    says whether the committed file is the one this script writes

The installed program ships the Python runtime, Qt through PySide6, openpyxl, pypdf, numpy, ezdxf and its dependencies, PyInstaller's bootloader and typst.exe, whose fonts are inside it; distributing them obliges to hand their licences on with them. The texts are committed in legal/licenses/, read off the build environment's dist-info, the Python installation and Typst's release once, so that this file is written the same way on any machine; the versions are read from requirements.txt and packaging/build.py, which pin them. packaging/build.py refuses to build while the committed file is stale, ships it in the program's legal/ folder, and website/build.py publishes it beside the licence.
"""

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LEGAL = ROOT / "legal"
LICENSES = LEGAL / "licenses"
TARGET = LEGAL / "THIRD-PARTY-NOTICES.txt"
PYTHON = "3.13"   # the runtime the build freezes: packaging/build.py refuses another minor version
ET_XMLFILE = "2.0.0"   # openpyxl's one dependency, not pinned in requirements.txt: what the build environment installs with openpyxl 3.1.5
EZDXF_DEPENDENCIES = {"pyparsing": "3.2.5", "fonttools": "4.61.0", "typing_extensions": "4.16.0"}   # ezdxf's dependencies beside numpy, not pinned in requirements.txt: what the build environment installs with ezdxf 1.4.4


def pins():
    """{package: version} from requirements.txt, and Typst's from typst-version.txt."""
    out = {}
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z0-9_.-]+)==([^\s#]+)", line.strip())
        if m:
            out[m.group(1).lower()] = m.group(2)
    for line in (HERE / "requirements-build.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z0-9_.-]+)==([^\s#]+)", line.strip())
        if m:
            out[m.group(1).lower()] = m.group(2)
    pinned = (ROOT / "typst-version.txt").read_text(encoding="utf-8").strip() if (ROOT / "typst-version.txt").is_file() else ""
    out["typst"] = pinned or "?"
    return out


def components(v):
    """(name, version, licence, where its source is, what it covers, [licence files]) of every third-party part of the installed program."""
    return [
        ("Python", PYTHON, "Python Software Foundation License Version 2 (PSF-2.0)", "https://www.python.org/downloads/source/",
         "The Python runtime (python3*.dll and its standard library), with the libraries it carries: OpenSSL, libffi, zlib, bzip2, xz, SQLite, Expat, mpdecimal and others, each listed with its licence in the text below.",
         ["Python-PSF.txt"]),
        ("Qt 6 and PySide6 (PySide6, PySide6_Essentials, PySide6_Addons, shiboken6)", v.get("pyside6", "?"),
         "GNU Lesser General Public License v3 (LGPL-3.0-only)",
         "https://code.qt.io/cgit/pyside/pyside-setup.git/ (tag v%s) and https://download.qt.io/official_releases/qt/" % v.get("pyside6", "?"),
         "Woodcore's window. Qt and PySide6 are used unmodified, as the separate library files of the program's _internal\\PySide6 folder: you may replace them with a compatible version of your own. Qt itself includes third-party code, listed with its licences at https://doc.qt.io/qt-6/licenses-used-in-qt.html. The LGPL-3.0 adds its terms to the GPL-3.0, whose text follows it.",
         ["LGPL-3.0.txt", "GPL-3.0.txt"]),
        ("openpyxl", v.get("openpyxl", "?"), "MIT License", "https://foss.heptapod.net/openpyxl/openpyxl",
         "Reads the Excel workbooks.", ["openpyxl-MIT.txt"]),
        ("et_xmlfile", ET_XMLFILE, "MIT License", "https://foss.heptapod.net/openpyxl/et_xmlfile",
         "openpyxl's XML writer.", ["et_xmlfile-MIT.txt"]),
        ("pypdf", v.get("pypdf", "?"), "BSD 3-Clause License", "https://github.com/py-pdf/pypdf",
         "Reads the architect's PDF plans.", ["pypdf-BSD-3-Clause.txt"]),
        ("numpy", v.get("numpy", "?"), "BSD 3-Clause License, with the licences of the code it bundles", "https://github.com/numpy/numpy",
         "What a script of the project computes with, and what ezdxf draws with.", ["numpy-BSD-3-Clause.txt"]),
        ("ezdxf", v.get("ezdxf", "?"), "MIT License", "https://github.com/mozman/ezdxf",
         "Reads the architect's CAD drawings (DXF) and draws their layouts.", ["ezdxf-MIT.txt"]),
        ("pyparsing", EZDXF_DEPENDENCIES["pyparsing"], "MIT License", "https://github.com/pyparsing/pyparsing",
         "A dependency of ezdxf.", ["pyparsing-MIT.txt"]),
        ("fontTools", EZDXF_DEPENDENCIES["fonttools"], "MIT License", "https://github.com/fonttools/fonttools",
         "A dependency of ezdxf: reads the fonts a CAD drawing's text is measured with.", ["fonttools-MIT.txt"]),
        ("typing_extensions", EZDXF_DEPENDENCIES["typing_extensions"], "Python Software Foundation License Version 2 (PSF-2.0)",
         "https://github.com/python/typing_extensions", "A dependency of ezdxf.", ["typing_extensions-PSF.txt"]),
        ("Typst", v.get("typst", "?"), "Apache License 2.0", "https://github.com/typst/typst",
         "typst.exe, which compiles the reports. Its NOTICE follows its licence.", ["Typst-Apache-2.0.txt", "Typst-NOTICE.txt"]),
        ("Libertinus Serif (a font inside typst.exe)", "", "SIL Open Font License 1.1", "https://github.com/alerque/libertinus",
         "The report's default typeface.", ["OFL-1.1-Libertinus.txt"]),
        ("New Computer Modern (a font inside typst.exe)", "", "GUST Font License", "https://ctan.org/pkg/newcomputermodern",
         "Typst's default mathematics typeface.", ["GUST-Font-License.txt"]),
        ("DejaVu Sans Mono (a font inside typst.exe)", "", "DejaVu Fonts License (Bitstream Vera, Arev)", "https://dejavu-fonts.github.io/",
         "Typst's default monospaced typeface.", ["DejaVu-Fonts.txt"]),
        ("OpenSSL 3", "", "Apache License 2.0", "https://www.openssl.org/source/",
         "libssl and libcrypto, shipped by Python and by Qt for the update check over HTTPS. The Apache License 2.0 is reproduced with Typst's above.", []),
        ("PyInstaller bootloader", v.get("pyinstaller", "?"), "GNU General Public License v2 or later, with the Bootloader Exception",
         "https://github.com/pyinstaller/pyinstaller",
         "The start-up code of Woodcore.exe, woodcore-cli.exe and Woodcore-Launcher.exe. The Bootloader Exception allows it to be distributed with a program under any licence.",
         ["PyInstaller-COPYING.txt"]),
        ("Microsoft Visual C++ Redistributable (vcruntime140.dll, vcruntime140_1.dll)", "", "Microsoft Software License Terms, redistributable code",
         "https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist",
         "The C runtime Python and Qt are built against, redistributed as Microsoft allows.", []),
    ]


def render():
    v = pins()
    rule = "=" * 78
    lines = [
        "WOODCORE — THIRD-PARTY NOTICES",
        "",
        "Woodcore is © 2026 Florian Lamprecht (woodcore@pineo.ch), all rights reserved; its own terms are in LICENSE-fr.txt, LICENSE-de.txt and LICENSE-en.txt.",
        "The installed program also contains the third-party software listed below, each under its own licence, reproduced in full after the list. Nothing in Woodcore's terms restricts the rights these licences grant.",
        "",
        "This file is written by packaging/notices.py; do not edit it by hand.",
        "",
    ]
    parts = components(v)
    for i, (name, version, licence, source, what, _files) in enumerate(parts, 1):
        lines.append(f"{i:2d}. {name}{' ' + version if version else ''}")
        lines.append(f"    Licence: {licence}")
        lines.append(f"    Source:  {source}")
        lines.append(f"    {what}")
        lines.append("")
    done = set()
    for name, version, licence, source, what, files in parts:
        for file in files:
            if file in done:
                continue
            done.add(file)
            text = (LICENSES / file).read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip("\n")
            lines += [rule, f"{name}{' ' + version if version else ''} — {file}", rule, "", text, ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def stale():
    """None where the committed file is what render() writes, else a sentence saying so."""
    if not TARGET.is_file():
        return f"{TARGET} is missing -- run python packaging/notices.py"
    if TARGET.read_text(encoding="utf-8") != render():
        return f"{TARGET} is not what packaging/notices.py writes for the versions pinned -- run python packaging/notices.py"
    return None


def main():
    parser = argparse.ArgumentParser(prog="packaging/notices.py", description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="only say whether the committed file is current")
    args = parser.parse_args()
    if args.check:
        problem = stale()
        print(problem or f"{TARGET} is current")
        sys.exit(1 if problem else 0)
    TARGET.write_text(render(), encoding="utf-8", newline="\n")
    print(f"wrote {TARGET}")


if __name__ == "__main__":
    main()
