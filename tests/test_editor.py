"""The report can still be *edited* -- tinymist survives analysing every file of it.

A Typst file can compile perfectly and still be impossible to work on. v0.60's `lib/formula.typ` did exactly that: the report built at every level and in every language, `tinymist lint` was silent, and the PDF was correct -- while in VS Code the language server died within seconds of the cursor entering any section, with `thread 'tokio-rt-worker' has overflowed its stack` and exit code 3221225725 (STATUS_STACK_OVERFLOW). Nothing in the folder caught it, because every check here asked whether the report *compiles*.

What killed it was `tokenize`: one chain of nine `else if` branches, two of them long, inside the `while` loop. tinymist's type checker -- which runs on every keystroke, for completion and for inlay hints -- recursed over that chain until its stack ran out. Removing either long branch was enough to stop it, so what costs is the weight of the chain as a whole and not any one construct in it; a bigger stack does not help (`RUST_MIN_STACK` up to 1 GB was tried). The fix was to make every case of `read-token` one line and read what it needs in a function of its own (v0.60.1).

That fix is a threshold, not a proof, which is exactly why it needs a test: a chain that grows back, here or anywhere else the report imports, breaks the editor again and nothing else would say so. The two requests below are the ones that crashed and the two that matter while typing -- `completion` is the autocomplete, `inlayHint` fires on every visible range.

⚠️ Skipped where tinymist is not installed: a machine that only builds the report is a legitimate machine.
"""

import json
import os
import subprocess
import threading
import time
import urllib.parse
from pathlib import Path

import conftest
from conftest import ROOT, Skip

TYPST_ROOT = conftest.TYPST_ROOT             # the Typst root of the example project the tests work on: its own folder, the example being laid out in three documents
PROJECT = conftest.PROJECT
STACK_OVERFLOW = 3221225725                   # STATUS_STACK_OVERFLOW, as Windows reports it
TIMEOUT = 60


def _tinymist():
    """The tinymist binary: the VS Code extension's own, else one on the path."""
    import shutil
    found = sorted(Path.home().glob(".vscode*/extensions/myriad-dreamin.tinymist-*/out/tinymist.exe"))
    if found:
        return str(found[-1])
    on_path = shutil.which("tinymist")
    if on_path:
        return on_path
    raise Skip("tinymist is not installed")


def _uri(path):
    return "file:///" + urllib.parse.quote(str(path).replace(os.sep, "/"), safe="/:")


class _Server:
    """One tinymist over stdio, opened on one file. Not a general client: it speaks just enough LSP to ask the questions this test asks."""

    def __init__(self, exe, path, root=None):
        self.proc = subprocess.Popen([exe, "lsp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, bufsize=0)
        self.root = PROJECT.root if root is None else root   # the Typst root the server is told, as tinymist.rootPath
        self.diagnostics = []                                 # every message of every textDocument/publishDiagnostics
        self.answered = set()
        self.next_id = 0
        threading.Thread(target=self._read, daemon=True).start()
        self.text = path.read_text(encoding="utf-8")
        self.uri = _uri(path)
        self._handshake()

    def _read(self):
        buf = b""
        while True:
            one = self.proc.stdout.read(1)
            if not one:
                return
            buf += one
            if not buf.endswith(b"\r\n\r\n"):
                continue
            header = buf.decode("utf-8", "replace")
            length = int(next(h for h in header.split("\r\n") if h.lower().startswith("content-length")).split(":")[1])
            body = b""
            while len(body) < length:
                more = self.proc.stdout.read(length - len(body))
                if not more:
                    return
                body += more
            message = json.loads(body)
            if "id" in message and ("result" in message or "error" in message):
                self.answered.add(message["id"])
            if message.get("method") == "textDocument/publishDiagnostics":
                self.diagnostics += [d.get("message", "") for d in message["params"].get("diagnostics", [])]
            buf = b""

    def _send(self, message):
        data = json.dumps(message).encode("utf-8")
        self.proc.stdin.write(b"Content-Length: %d\r\n\r\n" % len(data) + data)
        self.proc.stdin.flush()

    def _handshake(self):
        capabilities = {"textDocument": {"synchronization": {"dynamicRegistration": True},
                                         "completion": {"completionItem": {"snippetSupport": True}},
                                         "inlayHint": {}},
                        "workspace": {"configuration": True}}
        # the workspace VS Code opens on the project: the project's own folder, which is also its Typst root (and what its .vscode/settings.json states as tinymist.rootPath)
        self.ask("initialize", {"processId": None, "rootUri": _uri(PROJECT.root),
                                "capabilities": capabilities,
                                "workspaceFolders": [{"uri": _uri(PROJECT.root), "name": "project"}],
                                # and the root the project's .vscode/settings.json states, as the VS Code extension hands it over once it has substituted ${workspaceFolder} (Tinymist takes an absolute root only)
                                "initializationOptions": {"projectResolution": "singleFile", "rootPath": str(self.root)}})
        self._send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
        time.sleep(0.8)
        self._send({"jsonrpc": "2.0", "method": "textDocument/didOpen",
                    "params": {"textDocument": {"uri": self.uri, "languageId": "typst",
                                                "version": 1, "text": self.text}}})
        time.sleep(1.5)

    def open(self, path):
        """Another file opened in the same server, as VS Code does when the engineer opens the next tab: what the files share -- the engine, commands.typ -- is analysed once, which is what lets every file of the report be asked in minutes rather than one server started per file (issue #22)."""
        self.text = path.read_text(encoding="utf-8")
        self.uri = _uri(path)
        self._send({"jsonrpc": "2.0", "method": "textDocument/didOpen",
                    "params": {"textDocument": {"uri": self.uri, "languageId": "typst",
                                                "version": 1, "text": self.text}}})

    def ask(self, method, params):
        """Returns None when the server answered, else why it did not."""
        self.next_id += 1
        which = self.next_id
        try:
            self._send({"jsonrpc": "2.0", "id": which, "method": method, "params": params})
        except OSError:
            return f"the server was already dead (exit {self.proc.returncode})"
        started = time.time()
        while time.time() - started < TIMEOUT:
            if which in self.answered:
                return None
            if self.proc.poll() is not None:
                code = self.proc.returncode
                crash = " -- a stack overflow" if code == STACK_OVERFLOW else ""
                return f"the server died on {method} (exit {code}{crash})"
            time.sleep(0.05)
        return f"the server did not answer {method} in {TIMEOUT} s"

    def close(self):
        try:
            self.proc.kill()
        except OSError:
            pass


def _asked(server):
    """The reason `server` did not survive the two requests that crashed it, on the file it has open, or None."""
    whole = {"start": {"line": 0, "character": 0},
             "end": {"line": server.text.count("\n") + 1, "character": 0}}
    failed = server.ask("textDocument/inlayHint", {"textDocument": {"uri": server.uri}, "range": whole})
    if failed:
        return failed
    # in the middle of the file, where a call site is likelier than the header comments
    line = max(0, server.text.count("\n") // 2)
    return server.ask("textDocument/completion",
                      {"textDocument": {"uri": server.uri},
                       "position": {"line": line, "character": 0},
                       "context": {"triggerKind": 1}})


def _survives(path):
    """The reason the language server did not survive analysing `path`, or None."""
    server = _Server(_tinymist(), path)
    try:
        return _asked(server)
    finally:
        server.close()


def _report_files():
    # the report's entry and sections in its own folder, what the three documents share at the top, the two other documents' entries and sections
    files = [PROJECT.report_typ, PROJECT.commands_typ, PROJECT.config_typ]
    files += sorted((PROJECT.document_dir("rs") / "Sections").glob("*.typ"))
    for mode in PROJECT.modes:
        if mode != "rs":
            files += [PROJECT.document_typ(mode)] + sorted((PROJECT.document_dir(mode) / "Sections").glob("*.typ"))
    files += sorted((conftest.PROJECT.generated_dir / "lib").glob("*.typ"))  # the engine the report imports: the copy beside its export
    return [f for f in files if f.exists()]


def test_the_language_server_survives_every_file_of_the_report():
    """Every .typ the engineer opens: the entry point, commands.typ, config.typ, each section, each library file."""
    exe = _tinymist()                            # skips here when it is not installed
    # ⚠️ One server for every file, each opened in turn as in VS Code (issue #22). Until then each of the 181 files of the example started a server of its own -- 2.3 s of handshake each, and up to 60 s per request on a busy machine -- and this one test held a sequential run of the suite for hours. A server dies on the file that kills it whatever came before, so the file is still named.
    files = _report_files()
    server = _Server(exe, files[0])
    try:
        for path in files:
            if path != files[0]:
                server.open(path)
            failed = _asked(server)
            assert failed is None, f"{path.relative_to(PROJECT.root)}: {failed}"
    finally:
        server.close()


def test_the_language_server_survives_a_call_into_the_engine():
    """The case that actually broke: a section that imports commands.typ and calls one command. Merely importing never crashed -- the type checker only walks a module once something in it is called."""
    _tinymist()
    directory = conftest.probe_dir("editor")
    probe = directory / "call.typ"
    relative = os.path.relpath(conftest.PROJECT.commands_typ, directory).replace(os.sep, "/")
    probe.write_text(f'#import "{relative}": *\n\n#var("c", 1.5)\n\n#var("a", 2)\n#var("b", 3)\n#eq("x", `a dot b`)\n',
                     encoding="utf-8")
    # The probe must itself compile: until the audit of 260916 it called `#show-eq(..., where: ...)`, a command removed in v0.61, and the test passed without calling the engine at all (AUD-6-17).
    if conftest.have_typst():
        import subprocess
        built = subprocess.run(["typst", "compile", "--root", str(TYPST_ROOT), str(probe), str(directory / "call.pdf")],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        assert built.returncode == 0, f"the probe calls something the engine no longer has: {built.stderr[:600]}"
    failed = _survives(probe)
    assert failed is None, f"a call into the engine: {failed}"


def test_tinymist_takes_the_project_s_folder_for_the_root_its_settings_state():
    """The engineer's safety net (30.09.2026): a project in three documents is compiled from its own folder -- a section imports the engine as `"/000-Typst-Config/commands.typ"` -- and its `.vscode/settings.json` states `"tinymist.rootPath": "${workspaceFolder}"`, which the VS Code extension substitutes with the folder VS Code was opened on before Tinymist reads it. Held from both ends: the example's settings state it, and Tinymist told that root finds `/commands.typ` from a section of the report in its own folder -- where told the document's folder, the root it takes when VS Code is opened on that folder instead, it does not, which is what shows the check can fail."""
    exe = _tinymist()
    settings = (PROJECT.root / ".vscode" / "settings.json").read_text(encoding="utf-8")
    import project_migrate
    assert json.loads(project_migrate.jsonc_plain(settings)).get("tinymist.rootPath") == "${workspaceFolder}", "the example's settings do not state the project's folder as Tinymist's root"
    section = PROJECT.document_dir("rs") / "Sections" / "003-baustoffe.typ"
    assert section.read_text(encoding="utf-8").startswith('#import "/000-Typst-Config/commands.typ"'), "the section does not import from the project's root"

    def not_found(root):
        server = _Server(exe, section, root=root)
        try:
            started = time.time()
            while time.time() - started < 8 and not server.diagnostics:
                time.sleep(0.25)
            return [m for m in server.diagnostics if "not found" in m]
        finally:
            server.close()

    assert not not_found(PROJECT.root), "Tinymist told the project's folder as its root does not find /commands.typ"
    assert not_found(PROJECT.document_dir("rs")), "Tinymist told the document's folder found /commands.typ all the same -- this check cannot fail"
