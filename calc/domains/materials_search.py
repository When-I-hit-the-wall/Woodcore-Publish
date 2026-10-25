"""Finding a material by what the engineer types (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, REQ-011; issue #110).

Every word typed must be found (AND), without regard to case or accents, in the material's names in the three languages, its category -- its three names and its words (`materials_contract.CATEGORY_TERMS`) -- or its type («panneau», «Platte», «panel»). The filters are its origin -- all, Woodcore's, the engineer's -- and its type. Shared by the «Matériaux» tab and the permanent loads' choice of a material. No Qt here.
"""

import unicodedata

from domains import materials_contract as contract

ORIGINS = ("all", "woodcore", "user")


def fold(text):
    """`text` lower case and without accents: «Étanchéité» is «etancheite»."""
    decomposed = unicodedata.normalize("NFKD", str(text or "").casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def haystack(m):
    names = m.get("names") or {}
    parts = [names.get(lang, "") for lang in contract.LANGS]
    parts.append(contract.CATEGORY_TERMS.get(m.get("category"), ""))
    parts.append(contract.TYPE_TERMS.get(m.get("type"), ""))
    return fold(" ".join(parts))


def matches(m, query):
    hay = haystack(m)
    return all(word in hay for word in fold(query).split())


def search(materials, query="", origin="all", kind=None):
    """The materials of `materials` that every word of `query` finds, of `origin` (all, woodcore, user) and of type `kind` (None for any), in their order."""
    out = []
    for m in materials:
        shipped = bool(m.get("origin"))
        if origin == "woodcore" and not shipped or origin == "user" and shipped:
            continue
        if kind and m.get("type") != kind:
            continue
        if matches(m, query):
            out.append(m)
    return out


def ranked(materials, query=""):
    """`search`'s materials with the category the words name first (spec 2026-10-24-poids-propre-repense, T48): «isolation», «étanchéité», «béton», «acier», «bois» list their whole category, at the head, then what the words find by name; each part in the order of `materials`."""
    found = search(materials, query)
    words = fold(query).split()
    if not words:
        return found
    head = [m for m in found if all(w in fold(contract.CATEGORY_TERMS.get(m.get("category"), "")) for w in words)]
    return head + [m for m in found if m not in head]


def by_category(materials):
    """{category: [materials]} in the order of `materials_contract.CATEGORIES`, an empty category left out."""
    out = {}
    for c in contract.CATEGORIES:
        found = [m for m in materials if m.get("category") == c]
        if found:
            out[c] = found
    return out
