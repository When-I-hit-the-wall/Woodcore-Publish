"""No third party's name anywhere in the repository (14.10.2026): the code is to be distributed, so neither the office whose templates served as a control, nor the engineer's own projects, nor the people his test data was copied from are named -- not in the code, the docs, the site, the tests or a file's name.

The names are held as SHA-256 digests of their lowercase spelling, so this file does not name them either. Every word of every file, its accents taken off, the repository holds -- its path, its text, and the member names and text of a zip archive (an .xlsx, a .docx) -- is hashed and compared. A new name is added by its digest: `hashlib.sha256(b"name").hexdigest()`.
"""

TIER = "fast"  # tests/run_tests.py --fast

import hashlib
import re
import subprocess
import unicodedata
import zipfile

from conftest import ROOT

FORBIDDEN = {
    "b5c770d2917caefdf89d0d6e43453995f076393dd43946f8bb7d3a5f38f3c5b2",
    "497df96b1f0f01b79bb5a76055e02b80fae11663ff6326d0a09672a533690b9d",
    "52672204eb55b633aa43ed87b5631eed17e2ab7fa538039ee96027d88f2065fd",
    "7b54def6d213b653ae9a74597e2bcd5b157621a8505783ac24ed79a48c6fb2e3",
    "66c1edc788aa35606a325f290b01e3e0da24306192070aed411263244732746e",
    "bd8fa67ee09bcc6e369bb68832c597b821750d89181103056955061a0bfc8716",
    "2f1d6699fa5b931962b86f968b726968ef43c3bcf5a6c5a9d364baaaca62cc3b",
}
# A word is a run of letters, its accents taken off: a name spelt with or without them is the same name
WORD = re.compile(r"[^\W\d_]+")


def _files():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [name for name in out.decode("utf-8").split("\0") if name]


def _named(data):
    text = unicodedata.normalize("NFKD", data.decode("utf-8", "ignore").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return any(hashlib.sha256(word.encode("utf-8")).hexdigest() in FORBIDDEN for word in set(WORD.findall(text)))


def test_no_file_names_a_third_party():
    found = []
    for name in _files():
        path = ROOT / name
        if not path.is_file():
            continue
        if name.lower().endswith(".pdf"):
            # a norm's PDF shipped with Woodcore (norm-library/, spec 2026-10-22-onglet-neige-type, D-24): ~170 MB of the publishers' own bytes, whose words are not this project's to choose -- its name is read, its content is not
            if _named(name.encode("utf-8")):
                found.append(name)
            continue

        data = path.read_bytes()
        if _named(name.encode("utf-8")) or _named(data):
            found.append(name)
        elif data[:2] == b"PK":
            with zipfile.ZipFile(path) as archive:
                if any(_named(member.encode("utf-8")) or _named(archive.read(member)) for member in archive.namelist()):
                    found.append(name)
    assert not found, "a third party is named in: " + ", ".join(found)
