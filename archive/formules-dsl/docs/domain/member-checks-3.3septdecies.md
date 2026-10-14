# §3.3septdecies of docs/domain/member-checks.md, as it stood when the «Formules» tab was retired (0.117)

### 3.3septdecies A member's checks written in keyword lines (v0.100)

The engineer asked for «un onglet où le user peut écrire des formules de manières simples, non formatées en typst», and wrote his own example:

    Position: S001
    Fais la vérification à: la compression
    Fais la vérification à la stabilité: compression
    Fais la vérification à la flexion avec compression

He was offered an AI for it and refused it («n'implémente pas l'IA»), and agreed that **a deterministic parser suffices**. So `calc/dsl.py` is a grammar of a dozen words, and what that buys is the whole argument for it: the same lines always give the same Typst, a line outside the grammar is **refused naming the line and listing what is understood**, there is no network, no key and no cost, and it **cannot invent a command that does not exist**. What it gives up is tolerance — «vérifie le flambement de S001» written a new way each day is a refusal until the grammar learns the word (§13).

**The shape is `mot-clé: valeur`, one per line.** A blank line and a `#` or `//` comment are skipped; a `position:` line opens a block and everything under it belongs to that member until the next one. Every keyword carries its French, German and English word, matched **folded** — without accents or case — so «Humidité», «humidite» and «Feuchteklasse» are one keyword. The keywords are the identity (`position`, `grade`, `moisture`, `b`, `h`, `d`), the actions (`N`, `V`, `V_y`, `M_y`, `M_z`, `T`, `F`, `tau`, `sigma_90`), the lengths (`l`, `w`, `l_k`, `l_k_y`, `l_k_z`, `a`), `alpha`, `level`, and `verify`; the checks are the eight of §3.3undecies, each with its own words in the three languages, «stabilité: compression» reaching the same check as «compression» because the command prints Tragsicherheit and Stabilität as two parts of one page.

**It emits Typst and runs nothing**: `#member` and the `verify-*` commands, ⚠️ **each with the arguments that command takes and no other** — the grammar knows `verify-shear` takes no buckling length, so a `l_k` written in a block that also shears is handed to the compression check and not to the shear check, which would refuse it. A `l_k` stated once goes to both axes, which is what an engineer means by writing it once. A bare number is passed as a number and anything else as a string, since an action may be a value with its unit or the name of a variable declared above the line (§3.3undecies).

**What is missing is said and never refused** (`dsl.missing`): a check whose action the block does not state, and a compression check with no buckling length — the engineer may mean to write the value in the report by hand, and the commands themselves say what they cannot compute.

**The tab** is «Formules» (§10quater), three panes: what he writes, the Typst it becomes, and **the page that Typst compiles to** — his own requirement, «il doit être possible de voir la compilation typst et pas uniquement le code typst» — compiled from standard input against the project's own report folder as the Typst root, so `#member("T001")` reads the project's real positions and nothing is written into the project to render a preview. *Insérer dans une section…* names the section, shows what will be appended, and writes only on a yes (his answer E14).

