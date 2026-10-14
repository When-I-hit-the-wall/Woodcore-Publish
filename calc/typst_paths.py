"""The paths a Typst file writes, found and rewritten when what they name moves (the three document modes, work package 1.3).

A report names files in strings: `#import "../commands.typ": *`, `#include "Sections/001-einleitung.typ"`, `image("../Images/Situation.png")`, `json("../data/project.json")`, `show-bibliography(project: "references.bib")`. A string is resolved against the file that holds it, or against the Typst root where it starts with «/», and Typst cannot be asked where a path leads without compiling. When a project's report folder moves from `<project>/Statischer Bericht (typst)/` to `<project>/3_Statischer Bericht/` and its `config.typ`, `commands.typ`, `references.bib`, `Images/` and `_woodcore/` move up to the project folder, which becomes the root, every such string whose target moved has to follow — and one that cannot be made to follow has to be said, never left to fail at the next compile.

Qt-free and standard library only, so that the migration (`calc/project_migrate.py`) and the creation of a project from a report-shaped template can both call it.

**Finding them** (`literals`). A file is read by a small lexer that knows where code is and where it is not, since the same characters mean different things in each: in markup a `"` is a smart quote, `//` starts a comment except inside `https://…`, and `[` and `]` nest; in code `"` opens a string and a `//` inside it is nothing; a raw block is neither; and a comment is skipped whole, nested block comments included. Modelled on Typst's own lexer and parser and held against the committed reports and the engine's own `lib/*.typ`. A literal is reported when it is

- the string after `import` or `include` (`#import "x.typ": *`, and `include "x.typ"` inside a code block such as `#{ set heading(offset: 1); include "Sections/x.typ" }`),
- the first string argument of `image(`, `read(`, `json(`, `csv(`, `yaml(`, `toml(`, `xml(`, `cbor(`, `plugin(` or `bibliography(`,
- the value of a `project:` argument, which the engine reads from the root **whatever it starts with** (`read("/" + path)`, lib/bibliography.typ), or of a `file:` argument.

A package import, `@preview/…` or `@local/…`, is a path to nothing on disk and is skipped. A path built at compile time (`image("../Images/" + name)`) is found by its first piece and marked `partial`: if that piece names a folder it is followed like any other, and if it names nothing it is reported as unresolved, which is the truth about it.

**Rewriting them** (`rewrite`). Given where the file, the root and the targets were and where they are going — `moved` maps an old absolute path, a file or a folder, to its new one, and the longest moved ancestor of a target decides where it goes — a literal is written again only when it would stop reaching its target: the string as it stands is resolved from the file's new place against the new root, and left exactly as it is where that is still the target. So `#include "Sections/001-einleitung.typ"` in an entry file that moved together with its `Sections/` is untouched, `project: "references.bib"` stays as it is when `references.bib` moves to the top of the new root, and `image("../Images/x.png")` becomes `image("/Images/x.png")`. A literal that has to change is written root-absolute, `"/" + the target's path from the new root`, valid at any depth and equal to what the editor sees (the plan's framing decision 3); a `project:` value is written without the slash, the engine adding it. Every byte outside a rewritten literal is kept, line endings included — a file is read and written as bytes (`read_text`, `write_text`).

A literal whose target exists nowhere — neither where it was nor where it is going, so the migration may rewrite before or after moving — is left untouched and reported, and so is one whose target would lie outside the new root, which Typst cannot reach. A string that is only «/» is the root itself, `read("/" + path)` as the engine writes it, and is never touched.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path

# The functions whose first string argument is a path. `bibliography` is not in the plan's list and is here because Typst's own one takes a path the same way.
PATH_FUNCTIONS = frozenset({"image", "read", "json", "csv", "yaml", "toml", "xml", "cbor", "plugin", "bibliography"})

# A named argument holding a path, and whether it is read from the root (`project:`, which the engine prefixes with «/») or from the file like every other.
NAMED_PATHS = {"project": True, "file": False}

# What opens a statement that runs to the end of the line when it is embedded in markup (`#let x = 1`, `#set page(…)`). Checked against Typst 0.15: `;` or a newline ends it, and what follows is markup again.
STATEMENT_KEYWORDS = frozenset({"let", "set", "show", "import", "include", "if", "for", "while", "return", "break", "continue", "context"})

KINDS_OF_IMPORT = ("import", "include")


@dataclass(frozen=True)
class Literal:
    """One path written in a Typst file: where its content lies (`start` and `end`, the text between the quotes), what it is for and what it says."""
    start: int
    end: int
    kind: str              # import, include, one of PATH_FUNCTIONS, project or file
    value: str             # the string as Typst reads it: its escapes resolved
    partial: bool = False  # a path continued at compile time with `+`

    @property
    def root_relative(self):
        """True for a `project:` value, which the engine reads from the root even without a leading slash."""
        return NAMED_PATHS.get(self.kind, False)

    def raw(self, text):
        """The literal as written in `text`, between its quotes."""
        return text[self.start:self.end]


@dataclass(frozen=True)
class Change:
    """A literal rewritten: where it was, what it now says, and the target it names before and after."""
    literal: Literal
    new: str
    old_target: Path
    new_target: Path

    @property
    def old(self):
        return self.literal.value


@dataclass(frozen=True)
class Unresolved:
    """A literal left as it was, and why."""
    literal: Literal
    reason: str


# --- reading a file ----------------------------------------------------------------------

def read_text(path):
    """A Typst file as text with its line endings kept: `Path.read_text` turns CRLF into LF, and a file rewritten from that would change on every line."""
    return Path(path).read_bytes().decode("utf-8")


def write_text(path, text):
    """`text` written as it is, line endings included, beside the file and moved into place so that a failure leaves the old one."""
    path = Path(path)
    part = path.with_name(path.name + ".part")
    part.write_bytes(text.encode("utf-8"))
    os.replace(part, path)


# --- the lexer ---------------------------------------------------------------------------

_IDENT = re.compile(r"[^\W\d][\w-]*")
_STRING_BODY = re.compile(r'(?:[^"\\]|\\.)*', re.S)
_HASH_NUMBER = re.compile(r"\d+(?:\.\d+)?\w*%?")
_BLOCK_EDGE = re.compile(r"/\*|\*/")

# What markup reacts to, found by searching: everything between two of them is plain text. `h` is not among them, `http(s)://` is, as in Typst's own lexer, which starts a link at any `h` followed by `ttp://`.
_MARKUP_SPECIAL = re.compile(r"\\|/[/*]|[#$`\[\]]|https?://")
_MATH_SPECIAL = re.compile(r'\\|/[/*]|["#$`]')

# One token of code, matched in this order. Anything else is a single character of punctuation.
_CODE_TOKEN = re.compile(r"""
    (?P<ws>\s+)
  | (?P<comment>//|/\*)
  | (?P<string>")
  | (?P<raw>`)
  | (?P<math>\$)
  | (?P<ident>[^\W\d][\w-]*)
  | (?P<number>\d\w*(?:\.\d\w*)?)
  | (?P<open>[(\[{])
  | (?P<close>[)\]}])
  | (?P<other>.)
""", re.X | re.S)

# What a link may hold in markup, after Typst's own `link_prefix`: brackets have to balance, and trailing punctuation belongs to the sentence.
_LINK_CHARS = frozenset("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%&*+,-./:;=?@_~'")
_LINK_TRAILING = "!,.:;?'"

_SIMPLE_ESCAPES = {"n": "\n", "r": "\r", "t": "\t"}
_ESCAPE = re.compile(r"\\(?:u\{([0-9a-fA-F]+)\}|(.))", re.S)


def _unescape(raw):
    """A string's content as Typst reads it."""
    if "\\" not in raw:
        return raw

    def one(match):
        if match.group(1):
            return chr(int(match.group(1), 16))
        return _SIMPLE_ESCAPES.get(match.group(2), match.group(2))

    return _ESCAPE.sub(one, raw)


def _escape(value):
    """A value written back between quotes: only what would end or bend the string."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


class _Lexer:
    """Walks a file in the modes Typst does, keeping a stack of them, and collects the path literals it passes.

    The stack holds `[mode, closer, flag]`: *markup* (closed by `]` where it is a content block, `flag` the depth of brackets it holds itself), *code* (closed by `)` or `}`, or by nothing where it is the statement a `#let` opens, `flag` true then: a newline ends it), *math* (closed by `$`) and *chain* (what may still follow `#name`: `.field`, a call, a content block — Typst takes them only when nothing separates them).
    """

    def __init__(self, text):
        self.text = text
        self.n = len(text)
        self.i = 0
        self.stack = [["markup", None, 0]]
        self.hist = []         # the last few tokens of the code being read: what a string is looked up against
        self.found = []

    def run(self):
        while self.i < self.n:
            frame = self.stack[-1]
            getattr(self, "_" + frame[0])(frame)
        return self.found

    # -- small helpers

    def _push(self, kind, closer=None, flag=0):
        self.stack.append([kind, closer, flag])

    def _note(self, token):
        self.hist.append(token)
        del self.hist[:-4]

    def _line_comment(self, j):
        k = self.text.find("\n", j)
        return self.n if k < 0 else k

    def _block_comment(self, j):
        depth, k = 1, j + 2
        while depth:
            edge = _BLOCK_EDGE.search(self.text, k)
            if edge is None:
                return self.n
            depth += 1 if edge.group() == "/*" else -1
            k = edge.end()
        return k

    def _raw(self, j):
        """Past the raw block that opens at `j`: the next run of as many backticks, and `` `` `` alone is an empty one."""
        text, n = self.text, self.n
        k = j
        while k < n and text[k] == "`":
            k += 1
        count = k - j
        if count == 2:
            return k
        found = 0
        while k < n and found < count:
            found = found + 1 if text[k] == "`" else 0
            k += 1
        return k

    def _link(self, j):
        text, n = self.text, self.n
        k, brackets = j, []
        while k < n:
            c = text[k]
            if c in _LINK_CHARS:
                pass
            elif c in "([":
                brackets.append(c)
            elif c in ")]" and brackets and brackets[-1] == ("(" if c == ")" else "["):
                brackets.pop()
            else:
                break
            k += 1
        while k > j and text[k - 1] in _LINK_TRAILING:
            k -= 1
        return max(k, j + 1)

    def _skip_string(self, j):
        end = _STRING_BODY.match(self.text, j + 1).end()
        return end + 1 if end < self.n else self.n

    # -- markup and math

    def _markup(self, frame):
        match = _MARKUP_SPECIAL.search(self.text, self.i)
        if match is None:
            self.i = self.n
            return
        j, special = match.start(), match.group()
        if special == "\\":
            self.i = j + 2
        elif special == "//":
            self.i = self._line_comment(j)
        elif special == "/*":
            self.i = self._block_comment(j)
        elif special == "#":
            self._hash(j)
        elif special == "$":
            self.i = j + 1
            self.hist.clear()
            self._push("math")
        elif special == "`":
            self.i = self._raw(j)
        elif special == "[":
            frame[2] += 1
            self.i = j + 1
        elif special == "]":
            self.i = j + 1
            if frame[2] > 0:
                frame[2] -= 1
            elif frame[1] == "]":
                self.stack.pop()
                self.hist.clear()
        else:
            self.i = self._link(j)

    def _math(self, frame):
        match = _MATH_SPECIAL.search(self.text, self.i)
        if match is None:
            self.i = self.n
            return
        j, special = match.start(), match.group()
        if special == "\\":
            self.i = j + 2
        elif special == "//":
            self.i = self._line_comment(j)
        elif special == "/*":
            self.i = self._block_comment(j)
        elif special == '"':
            self.i = self._skip_string(j)
        elif special == "#":
            self._hash(j)
        elif special == "`":
            self.i = self._raw(j)
        else:
            self.i = j + 1
            self.stack.pop()
            self.hist.clear()

    def _hash(self, j):
        """`#` in markup or math: code begins. A statement keyword runs to the end of the line, anything else is an expression that goes on only as long as a `.field`, a call or a content block follows it with nothing between."""
        text = self.text
        k = j + 1
        self.i = k
        if k >= self.n:
            return
        c = text[k]
        self.hist.clear()
        if c in "{([":
            self.i = k + 1
            self._push("chain")
            if c == "[":
                self._push("markup", "]")
            else:
                self._note(("p", c))
                self._push("code", "}" if c == "{" else ")")
        elif c == '"':
            self._push("chain")
            self.i = self._skip_string(k)
        else:
            ident = _IDENT.match(text, k)
            if ident is not None:
                name = ident.group()
                self.i = ident.end()
                self._note(("id", name))
                if name in STATEMENT_KEYWORDS:
                    self._push("code", None, 1)
                else:
                    self._push("chain")
            elif c.isdigit():
                self.i = _HASH_NUMBER.match(text, k).end()

    def _chain(self, frame):
        text, j = self.text, self.i
        c = text[j]
        if c == "." and _IDENT.match(text, j + 1):
            ident = _IDENT.match(text, j + 1)
            self._note(("p", "."))
            self._note(("id", ident.group()))
            self.i = ident.end()
        elif c == "(":
            self.i = j + 1
            self._note(("p", "("))
            self._push("code", ")")
        elif c == "[":
            self.i = j + 1
            self.hist.clear()
            self._push("markup", "]")
        else:
            self.stack.pop()

    # -- code

    def _code(self, frame):
        match = _CODE_TOKEN.match(self.text, self.i)
        kind = match.lastgroup
        token = match.group()
        self.i = match.end()
        if kind == "ws":
            if frame[2] and "\n" in token:
                self.stack.pop()
                self.hist.clear()
        elif kind == "comment":
            start = match.start()
            self.i = self._line_comment(start) if token == "//" else self._block_comment(start)
        elif kind == "string":
            self._string(match.start())
        elif kind == "raw":
            self.i = self._raw(match.start())
            self._note(("o", "raw"))
        elif kind == "math":
            self.hist.clear()
            self._push("math")
        elif kind == "ident":
            self._note(("id", token))
        elif kind == "number":
            self._note(("o", "number"))
        elif kind == "open":
            if token == "[":
                self.hist.clear()
                self._push("markup", "]")
            else:
                self._note(("p", token))
                self._push("code", "}" if token == "{" else ")")
        elif kind == "close":
            self._close(token)
        elif token == ";" and frame[2]:
            self.stack.pop()
            self.hist.clear()
        else:
            self._note(("p", token))

    def _close(self, closer):
        """A `)`, `]` or `}` in code: it closes the frame it belongs to, popping what a statement or a chain left open above it."""
        for depth in range(len(self.stack) - 1, 0, -1):
            if self.stack[depth][1] == closer:
                del self.stack[depth:]
                break
        self._note(("p", closer))

    def _string(self, j):
        text = self.text
        end = _STRING_BODY.match(text, j + 1).end()
        kind = self._classify()
        if kind is not None:
            self.found.append(Literal(j + 1, end, kind, _unescape(text[j + 1:end]), self._continued(end + 1)))
        self.i = end + 1 if end < self.n else self.n
        self._note(("s", ""))

    def _continued(self, k):
        """Whether what follows the string that ends before `k` adds to it: `"../Images/" + name`."""
        while k < self.n and self.text[k].isspace():
            k += 1
        return k < self.n and self.text[k] == "+"

    def _classify(self):
        """What the string being read is, from the tokens before it: or None where it is not a path."""
        h = self.hist
        if not h:
            return None
        last = h[-1]
        if last[0] == "id" and last[1] in KINDS_OF_IMPORT and not (len(h) >= 2 and h[-2] == ("p", ".")):
            return last[1]
        if last == ("p", "(") and len(h) >= 2 and h[-2][0] == "id" and h[-2][1] in PATH_FUNCTIONS:
            if len(h) >= 3 and h[-3] == ("p", ".") and not (len(h) >= 4 and h[-4] == ("id", "std")):
                return None     # `data.image(…)`, a method that is not Typst's function
            return h[-2][1]
        if last == ("p", ":") and len(h) >= 2 and h[-2][0] == "id" and h[-2][1] in NAMED_PATHS:
            return h[-2][1]
        return None


def literals(text):
    """The path literals of a Typst file, in the order they are written, outside comments, raw blocks and other strings.

    Each is a `Literal` carrying the span of its content, its kind and its value; `text[lit.start:lit.end]` is what is written and `lit.value` what Typst reads. A package import is not listed, and neither is an empty string.
    """
    return [lit for lit in _Lexer(text).run() if lit.value and not lit.value.startswith("@")]


# --- where things are ---------------------------------------------------------------------

def _norm(path):
    """An absolute, normalised path, without asking the file system: the files may be where they were or already where they are going."""
    return Path(os.path.abspath(os.fspath(path)))


def _key(path):
    """What two paths are compared by: case and separators as Windows counts them."""
    return os.path.normcase(os.fspath(_norm(path)))


def _inside(path, root):
    k, r = _key(path), _key(root)
    return k == r or k.startswith(r + os.sep)


def _locate(path, pairs):
    """Where `path` lies once everything has moved: under its longest moved ancestor, or where it is."""
    best = None
    for old, new in pairs:
        if _inside(path, old) and (best is None or len(_key(old)) > len(_key(best[0]))):
            best = (old, new)
    if best is None:
        return _norm(path)
    old, new = best
    return _norm(new).joinpath(*_norm(path).parts[len(_norm(old).parts):])


def _from_root(path, root):
    """`path` as a `/`-separated path from `root`, or None where it does not lie inside it."""
    if not _inside(path, root):
        return None
    return "/".join(_norm(path).parts[len(_norm(root).parts):])


def _target(literal, value, file_dir, root):
    """What a string reaches: from the root for a `project:` value or one starting with «/», else from the file's folder."""
    if literal.root_relative or value.startswith("/"):
        return _norm(os.path.join(root, value.lstrip("/")))
    return _norm(os.path.join(file_dir, value))


def rewrite(text, file_old, file_new, root_old, root_new, moved):
    """`text` with every path literal that would stop reaching its target written again, and what was done: `(new_text, changes, unresolved)`.

    `file_old` and `file_new` are the file's absolute path before and after it moves (the same where it stays), `root_old` and `root_new` the Typst root before and after, and `moved` maps the old absolute path of each file or folder that moves to its new one. The text is that of the file, read with its line endings (`read_text`); the rewritten text keeps every byte outside the literals it changes.

    A literal is left alone when its string, resolved from `file_new` against `root_new`, is still its target. Otherwise it is written root-absolute, `"/" + the target's path from root_new` — without the slash for a `project:` value, which the engine adds, and with it where the old one had one. A literal whose target exists neither where it was nor where it is going, and one whose target leaves `root_new`, are left untouched and listed in `unresolved` with the reason. A string that is only «/» is the root and is never touched: the engine's own `read("/" + path)` is the pattern, and it stays true wherever the root is.
    """
    pairs = [(_norm(old), _norm(new)) for old, new in dict(moved).items()]
    old_dir, new_dir = _norm(file_old).parent, _norm(file_new).parent
    changes, unresolved, edits = [], [], []
    for lit in literals(text):
        if not lit.value.strip("/"):
            continue    # the root itself, `read("/" + path)`: it is the root in whichever place the root is
        old_target = _target(lit, lit.value, old_dir, root_old)
        new_target = _locate(old_target, pairs)
        if not (old_target.exists() or new_target.exists()):
            more = " (a path continued at compile time: only its first piece is checked)" if lit.partial else ""
            unresolved.append(Unresolved(lit, f"{lit.value!r} names nothing: neither {old_target} nor {new_target} exists{more}"))
            continue
        if _key(_target(lit, lit.value, new_dir, root_new)) == _key(new_target):
            continue    # the string as it stands still reaches it
        rel = _from_root(new_target, root_new)
        if rel is None:
            unresolved.append(Unresolved(lit, f"{lit.value!r} would name {new_target}, which lies outside the new root {_norm(root_new)}"))
            continue
        value = ("/" if lit.value.startswith("/") or not lit.root_relative else "") + rel
        if lit.value.endswith("/") and not value.endswith("/"):
            value += "/"    # a folder a path is continued from: `"../Images/" + name`
        if value == lit.value:
            continue
        changes.append(Change(lit, value, old_target, new_target))
        edits.append((lit.start, lit.end, _escape(value)))
    for start, end, new in reversed(edits):
        text = text[:start] + new + text[end:]
    return text, changes, unresolved


def rewrite_file(path, file_old, root_old, root_new, moved):
    """`rewrite` applied to the file at `path`, which is where it lies now and so `file_new`, written back only if something changed: `(changes, unresolved)`."""
    text = read_text(path)
    new_text, changes, unresolved = rewrite(text, file_old, path, root_old, root_new, moved)
    if new_text != text:
        write_text(path, new_text)
    return changes, unresolved
