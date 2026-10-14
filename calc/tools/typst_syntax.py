"""How a Typst call is cut into what gets a colour -- one tokeniser for the website and Woodcore's window (docs/ui/window.md §10quater, docs/conventions/build-and-release.md §12, v0.92).

The website set its code with a pattern of its own (website/build.py, v0.89) and the window took a copy of it in v0.92; the copy is what found that the keyword `#show` was read inside `#show-calc`, `\\b` falling between «w» and «-» -- so every `show-*` call of the site's reference had its first word coloured as a keyword and the rest as a function. The pattern is written here once, Qt-free because the site's build runs where no PySide6 is installed, and both import it.

`KINDS` names what each group is; `SITE_CLASS` is the class the site's stylesheet colours it by (site.css: .c .s .r .m .k .f .n .d), and `THEME_TOKEN` the colour of theme.json the window reads for it -- the same colour, the site's classes being defined from those tokens.
"""

import re

# A keyword stops where a name would go on: `#show-calc` is a call, `#show:` and `#show heading` are the keyword.
TYPST_TOKEN = re.compile(r"""
    (?P<comment>//[^\n]*|/\*.*?\*/)
  | (?P<string>"(?:\\.|[^"\\\n])*")
  | (?P<raw>`[^`\n]*`)
  | (?P<math>\$[^$\n]*\$)
  | (?P<keyword>\#(?:let|set|show|import|include|if|else|for|while|context|return)(?![\w-]))
  | (?P<call>\#[A-Za-z_][\w-]*(?:\.[A-Za-z_][\w-]*)*)
  | (?P<named>\b[A-Za-z_][\w-]*(?=\s*:(?!:)))
  | (?P<number>(?<![\w-])-?\d+(?:\.\d+)?(?:mm|cm|pt|em|fr|deg|%)?)
  | (?P<func>\b[A-Za-z_][\w-]*(?=\())
""", re.VERBOSE | re.DOTALL)

KINDS = ("comment", "string", "raw", "math", "keyword", "call", "named", "number", "func")

SITE_CLASS = {"comment": "c", "string": "s", "raw": "r", "math": "m", "keyword": "k", "call": "f",
              "named": "n", "number": "d", "func": "f"}

THEME_TOKEN = {"comment": "syn-comment", "string": "syn-string", "raw": "syn-raw", "math": "syn-math", "keyword": "syn-keyword",
               "call": "syn-call", "named": "syn-named", "number": "syn-number", "func": "syn-call"}


def tokens(code):
    """(start, end, kind) for every piece of `code` that takes a colour, in order; what lies between them takes none."""
    for m in TYPST_TOKEN.finditer(code):
        yield m.start(), m.end(), m.lastgroup
