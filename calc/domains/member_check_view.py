"""The four tabs of the member checks as their type «Calcul» reads them -- Traction, Compression, Flexion, Cisaillement --, described and never copied (spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md, UI-001 to UI-012, ARCH-001, ARCH-004; issue #112; docs/ui/calc-tab.md).

A tab of calculation is built from its domain's declaration (calc/tools/calc_tab.py). The member checks share one domain (`member_check`) and one folder (`Woodcore-Datei/checks/`) between four tabs, each listing its own kinds: `CheckDomain(tab)` is what one tab's services read -- its sections and fields, the rows it shows, what it says of a draft (`messages`), what it computes (`build_instance`, `results`), its drawings (`figure_svg`, `tile_svg`) and its chart --, every number of it `member_check.compute`'s and every rule `member_check`'s or `member_check_material`'s. No Qt here.

**The stability is the last accordion of the compression and of the bending** (REQ-011, Q-001 A): the box «vérifier la stabilité» is the draft's `stability`, which `stamp_version` turns into the kind -- compression ⇄ buckling, bending ⇄ lateral torsional buckling (`member_check.change_kind`) --, and which the file never holds (`to_file`); the save moves the check's file to the folder of its new kind (`save_case`).

**The words** are the tab's, prefixed `vc_` (calc/tools/member_check_tab_words.py): `vc_s_<section>`, `vc_f_<field>`, `vc_msg_<code>`, a tile's `vc_t_<id>`.
"""

import copy
import dataclasses
import json
import math

import project
import validation
from domains import links, member_check as mc, member_check_material as mm
from domains.contracts import Choice, Declaration, Field, Message
from norms import sia265
from number_text import exact as _fmt

PREFIX = "vc_"
NORM_FILE = "sia265-2021-checks-excerpts"   # the clauses and figures of SIA 265 the checks cite (UI-012)
# The tabs, their kinds -- the first the one a new check is --, and the prefix of a new id
TABS = {
    "tension": (("tension",), "Z_"),
    "compression": (("compression", "buckling"), "DR-"),
    "bending": (("bending", "lateral-torsional"), "BI-"),
    "shear": (("shear",), "SC-"),
}
STABILITY = {"compression": "buckling", "bending": "lateral-torsional"}
STABLE = {v: k for k, v in STABILITY.items()}
# A check's kind as the glossary names it, in a message (T39: «… de cette vérification (compression)»)
KIND_WORDS = {"tension": "Zug", "compression": "Druck", "bending": "Biegung", "shear": "Schub", "buckling": "Knicken", "lateral-torsional": "Kippen"}
# The draft's box «vérifier la stabilité», never written into the file
STABILITY_KEY = "stability"
# The draft's five cards of f_c,90,d (UI-008): a case of 4.2.2.2 and the bracketed value or not -- the file's `case` and `larger`, which the card is written as (`_apply_support`) and never held itself
SUPPORT_KEY = "support"
LARGER_SUFFIX = "-larger"
SUPPORTS = ("generell", "mit_vorholz", "mit_vorholz" + LARGER_SUFFIX, "endauflagerung", "endauflagerung" + LARGER_SUFFIX)


def support_of(src):
    """The card a source's `case` and `larger` stand for: «generell» where it says none."""
    case = src.get("case") or "generell"
    return case + (LARGER_SUFFIX if src.get("larger") and case != "generell" else "")


def _apply_support(src):
    """The card of the draft written as its `case` and `larger` -- only where it says otherwise than they do, so that a file which held none keeps holding none -- and taken out of `src`."""
    support = src.pop(SUPPORT_KEY, None)
    if support in SUPPORTS and support != support_of(src):
        case, larger = (support[:-len(LARGER_SUFFIX)], True) if support.endswith(LARGER_SUFFIX) else (support, False)
        src["case"], src["larger"] = case, larger
    return src

_N = dict(kind="number", unit="kN", linkable=True, block=True, decimals=2, step=1.0)
FIELDS = {
    "N": Field("N", minimum=0.0, maximum=1e6, var="N", **_N),
    "N_signed": Field("N", minimum=-1e6, maximum=1e6, var="N", **_N),
    "alpha": Field("alpha", "number", "°", minimum=0.0, maximum=90.0, decimals=1, step=5.0, linkable=True, var="alpha"),
    "M_y": Field("M_y", "number", "kNm", minimum=0.0, maximum=1e6, decimals=2, step=0.5, linkable=True, block=True, zero_none=True, var="M_y_d"),
    "M_z": Field("M_z", "number", "kNm", minimum=0.0, maximum=1e6, decimals=2, step=0.5, linkable=True, block=True, zero_none=True, var="M_z_d"),
    "support": Field("support", "buttons", choices=tuple(Choice(s, PREFIX + "c_" + s.replace("-", "_")) for s in SUPPORTS)),
    "l": Field("l", "number", "mm", minimum=0.0, maximum=1e5, decimals=0, step=10.0, linkable=True, zero_none=True, var="l_c"),
    "w": Field("w", "number", "mm", minimum=1.0, maximum=1e5, decimals=0, step=10.0, linkable=True, special_word="w_b", var="w_c"),
    "stability": Field("stability", "checkbox"),
    "l_y": Field("l_y", "number", "mm", minimum=0.0, maximum=1e6, decimals=0, step=100.0, linkable=True, var="l_k_y"),
    "l_z": Field("l_z", "number", "mm", minimum=0.0, maximum=1e6, decimals=0, step=100.0, linkable=True, var="l_k_z"),
    "beta_y": Field("beta_y", "number", "", minimum=0.0, maximum=10.0, decimals=2, step=0.1, linkable=True),
    "beta_z": Field("beta_z", "number", "", minimum=0.0, maximum=10.0, decimals=2, step=0.1, linkable=True),
    "a": Field("a", "number", "mm", minimum=1.0, maximum=1e6, decimals=0, step=100.0, linkable=True, special_word="crit_given", var="a"),
    "sigma_m_crit": Field("sigma_m_crit", "number", "N/mm²", minimum=0.01, maximum=1e5, decimals=2, step=1.0, linkable=True, var="sigma_m_crit"),
    "variant": Field("variant", "tiles", choices=tuple(Choice(v, PREFIX + "t_" + v.replace("-", "_"), excerpts=x) for v, x in zip(mc.SHEAR_VARIANTS, (("4.2.5.1",), ("4.2.6",), ("4.2.7.1", "fig8"))))),
    "V_z": Field("V_z", "number", "kN", minimum=0.0, maximum=1e6, decimals=2, step=1.0, linkable=True, block=True, zero_none=True, var="V_z_d"),
    "V_y": Field("V_y", "number", "kN", minimum=0.0, maximum=1e6, decimals=2, step=1.0, linkable=True, block=True, zero_none=True, var="V_y_d"),
    "pith": Field("pith", "checkbox"),
    "F": Field("F", "number", "kN", minimum=0.0, maximum=1e6, decimals=2, step=1.0, block=True, zero_none=True, var="F_a_d"),
    "l_a": Field("l", "number", "mm", minimum=0.0, maximum=1e5, decimals=0, step=10.0, zero_none=True, var="l_a"),
    "w_a": Field("w", "number", "mm", minimum=1.0, maximum=1e5, decimals=0, step=10.0, special_word="w_b", var="w_a"),
    "sigma_90": Field("sigma_90", "number", "N/mm²", minimum=-1000.0, maximum=1000.0, decimals=3, step=0.1, var="sigma_90_d"),
}

SECTIONS = {
    "tension": (("forces", ("N", "alpha")),),
    "compression": (("forces", ("N", "alpha")), ("support", ("support", ("l", "w"))), ("stability", ("stability", ("l_y", "l_z"), ("beta_y", "beta_z")))),
    "bending": (("forces", (("N_signed", "M_y", "M_z"), "alpha")), ("stability", ("stability", "a", "sigma_m_crit", ("l_y", "l_z"), ("beta_y", "beta_z")))),
    "shear": (("figures", ("variant",)), ("forces", (("V_z", "V_y"), "pith", "F", ("l_a", "w_a"), "sigma_90"))),
}
# The excerpts a field's ⓘ shows -- the clauses `NORM_FILE` holds
# The clauses and figures a field's ⓘ shows, by tab -- calc/norms/sia265-2021-checks-excerpts.json, read off the editions (UI-012); a click pins them in the right pane
EXCERPTS = {
    "tension": {"N": ("4.2.1.1",), "alpha": ("4.2.1.3",)},
    "compression": {"N": ("4.2.2.1",), "alpha": ("4.2.2.3",), "support": ("4.2.2.2", "fig9", "fig46"), "stability": ("4.2.8", "fig10")},
    "bending": {"N_signed": ("4.2.4.1", "4.2.4.2"), "alpha": ("4.2.3.3", "fig7"), "stability": ("4.2.9", "fig11")},
    "shear": {"V_z": ("4.2.5.1",), "F": ("4.2.6",), "sigma_90": ("4.2.7.1", "fig8")},
}

_POSITIONS = {}


# --- the positions the export holds, read again only once it has moved --------------------------------------

def positions(here=None):
    """{id: position record} of the last export (connector.known_positions), read again only once the index has moved -- every keystroke resolves the draft."""
    from domains import connector
    try:
        here = here or project.current()
    except project.ProjectError:
        return {}
    data_dir = here.data_dir
    index = data_dir / "positions-index.json"
    try:
        key = (str(data_dir), index.stat().st_mtime_ns)
    except OSError:
        key = (str(data_dir), None)
    if _POSITIONS.get("key") != key:
        _POSITIONS["key"], _POSITIONS["value"] = key, connector.known_positions(data_dir)
    return _POSITIONS["value"]


class CheckDomain:
    """One tab of the member checks, as its type reads it -- see the module's docstring."""

    DOMAIN = "check"   # the kind of the checks' files (unfold, `#include domain-file("check", id)`), not the export's domain name
    FOLDER = mc.SOURCES
    ID_PATTERN = mc.ID_PATTERN
    LINKABLE = {links.SELF: mc.LINKABLE}
    SOURCE_SCHEMA_VERSION = mc.SOURCE_SCHEMA_VERSION
    EXPORT_FILE = mc.EXPORT_FILE
    PREFIX = PREFIX

    def __init__(self, tab):
        self.TAB = tab
        self.KINDS, self.ID_PREFIX = TABS[tab]
        self.KIND = self.KINDS[0]
        self.__name__ = "member_check_view[%s]" % tab

    # --- the cases of this tab, in the folder the four share ------------------------------------

    def owns(self, src):
        """Whether this tab lists `src`: a check of one of its kinds at normal temperature -- one in the fire situation is the «Résistance au feu» tab's (issue #46)."""
        return (src.get("kind") or "tension") in self.KINDS and src.get("fire") is None

    def _with_stability(self, src):
        """The draft's own keys, which the file never holds: the box «vérifier la stabilité» (REQ-011) and the card of f_c,90,d of a compression (UI-008)."""
        if self.TAB in STABILITY:
            src[STABILITY_KEY] = src.get("kind") == STABILITY[self.TAB]
        if self.TAB == "compression":
            src[SUPPORT_KEY] = support_of(src)
        return src

    def new_source(self, cid):
        return self._with_stability(mc.new_source(cid, self.KIND))

    def read_source(self, path):
        return self._with_stability(mc.read_source(path))

    @staticmethod
    def to_file(src):
        """The source as its file holds it: the draft without its box «vérifier la stabilité», its card of f_c,90,d written as `case` and `larger`."""
        out = _apply_support(dict(src))
        out.pop(STABILITY_KEY, None)
        return out

    def check_source(self, src, where="checks"):
        mc.check_source(self.to_file(src), where)

    def stamp_version(self, src):
        """The draft's card of f_c,90,d written as `case` and `larger` (UI-008), its kind after its box «vérifier la stabilité» (REQ-011), then the lowest version that holds it (`member_check.stamp_version`). The box and the card stay in the draft."""
        carded = SUPPORT_KEY in src
        _apply_support(src)
        if STABILITY_KEY in src and self.TAB in STABILITY:
            flag = bool(src[STABILITY_KEY])
            changed = mc.change_kind(self.to_file(src), flag)
            src.clear()
            src.update(changed)
            src[STABILITY_KEY] = flag
        held = src.pop(STABILITY_KEY, None) if STABILITY_KEY in src else None
        mc.stamp_version(src)
        if held is not None:
            src[STABILITY_KEY] = held
        if carded:
            src[SUPPORT_KEY] = support_of(src)
        return src

    def save_case(self, here, source, current_id):
        """The case written and exported (source_store.SourceStore.save), its file moved where the box «vérifier la stabilité» changed its kind (REQ-011, ARCH-009): the old kind read from the file before it is written over."""
        folder = here.checks_dir
        old_kind = None
        old_path = folder / ("%s.json" % (current_id or source["id"]))
        if old_path.is_file():
            try:
                old_kind = json.loads(old_path.read_text(encoding="utf-8")).get("kind")
            except (OSError, ValueError):
                old_kind = None
        folder.mkdir(parents=True, exist_ok=True)
        if current_id and current_id != source["id"]:
            old_path.unlink(missing_ok=True)
        import engine
        engine.write_json(folder / ("%s.json" % source["id"]), self.to_file(source))
        moved = mc.save_kind_change(here, source["id"], old_kind, source["kind"]) if old_kind and old_kind != source["kind"] else ()
        try:
            with project.using(here):
                mc.export(here, moved=moved)
        except Exception as exc:  # broad: the exporter's own message is what helps, said in the status bar; the case stays saved
            return str(exc)
        return ""

    @staticmethod
    def graph_id(cid):
        """A check's id in the graph of dependencies, `check:<id>`'s second half (domains/dependency_graph.py)."""
        return cid

    def export_cases(self, here):
        """The export of the checks (source_store.SourceStore.export): data/checks.json and their files."""
        mc.export(here)

    # --- what the list reads (calc/tools/check_list.py, UI-003) -------------------------------------

    def list_rows(self, here, ids):
        """{id: {position, position_label, eta, ok, reason}} of the saved checks `ids`, as the last export holds them (data/checks.json): the position each names -- its id and what it is, «T001 · Poutre», None for none --, its utilisation computed as the tab computes it (`member_check.utilisations`), None with its reason where it cannot be calculated. A check the export does not hold yet has no utilisation and no reason."""
        try:
            data = json.loads((here.data_dir / mc.EXPORT_FILE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        records = data.get("checks") or {}
        rates = mc.utilisations({"checks": {cid: rec for cid, rec in records.items() if cid in ids}})
        known = positions(here)
        out = {}
        for cid in ids:
            rec = records.get(cid) or {}
            pid = rec.get("position")
            held = known.get(pid) or {}
            label = ("%s · %s" % (pid, held.get("type_label") or held.get("strength_class") or "")).rstrip(" ·") if pid else None
            rate = rates.get(cid)
            out[cid] = {"position": pid, "position_label": label, "eta": rate["eta"] if rate else None, "ok": rate["ok"] if rate else None,
                        "reason": "" if rate else (rec.get("reason") or "")}
        return out

    # --- what the head «Élément» reads (calc/tools/check_member.py) ---------------------------------

    def positions(self):
        return positions()

    def position_grade(self, pid):
        """The strength class a position gives -- what «suit T001» says."""
        rec = positions().get(pid) or {}
        return ((rec.get("strength_class") if "strength_class" in rec else rec.get("material")) or "").strip() or None

    def position_moisture(self, pid):
        return (positions().get(pid) or {}).get("moisture_class")

    def message_params(self, params, lang):
        """A message's values in the window's language (tab_host.TabContext.message_text): a material's name, a panel's loading, a check's kind, read off the glossary -- the window's words never composed here."""
        from domains import unfold
        from i18n import strings
        out = dict(params)
        names = out.pop("names", None)
        material = out.get("material")
        if isinstance(material, str) and material.startswith(mm.GRADE_PREFIX):
            out["material"] = material[len(mm.GRADE_PREFIX):]   # a class of SIA 265 by its id, «GL24h»
        elif isinstance(names, dict) and names:
            out["material"] = names.get(lang) or next(iter(names.values()))
        loading = out.get("loading")
        if isinstance(loading, str) and "-" in loading:
            mode, direction = loading.split("-", 1)
            out["loading"] = strings.term(unfold.PANEL_LOADING_WORDS.get(mode, mode), lang) + " " + ("∥" if direction == "par" else "⊥")
        if out.get("kind") in KIND_WORDS:
            out["kind"] = strings.term(KIND_WORDS[out["kind"]], lang)
        if out.get("mode") in unfold.PANEL_LOADING_WORDS:
            out["mode"] = strings.term(unfold.PANEL_LOADING_WORDS[out["mode"]], lang)
        return out

    # --- the record and the calculation of a draft ----------------------------------------------

    def record(self, src):
        """The draft resolved as the export will resolve it (`member_check.resolve`): against the positions of the last export and the project's materials."""
        try:
            here = project.current()
        except project.ProjectError:
            here = None
        return mc.resolve(self.to_file(src), positions(here), library=mc.library_of(here) if here is not None and mm.kind_of_id(src.get("material")) == "user" else None)

    def build_instance(self, src, here=None):
        """The draft's calculation: its record, `member_check.compute`'s result and its lines as an instance of the engine -- {vars, steps, order, record, result} -- which «Résultats» and the graph of dependencies read. A draft that cannot be calculated stops here with its reason (the messages say it first)."""
        record = self.record(src)
        if not record.get("calculable"):
            raise validation.ValidationError(record.get("reason") or "not calculable")
        result, calculation = mc._calculation(record)
        computed = mc.compute(record)
        return {"vars": calculation.vars, "steps": calculation.steps, "order": list(calculation.order), "results": ["eta"],
                "record": record, "result": computed}

    def results(self, instance):
        """The rows in the order of the calculation, η last (REQ-014): what the report prints, never reordered."""
        return list(instance.get("order") or ())

    # --- what the tab says of a draft (UI-007) ----------------------------------------------------

    def messages(self, src):
        """Red what stops the calculation -- the reason of the record, said by its code where the material gives it (REQ-005, REQ-007) --, orange what is only said: a class written over the position's (REQ-013), a panel's side, σ_90,d outside its interval (REQ-008), a position gone, the pith on a glulam. No message of the stability (D-2)."""
        out = []
        try:
            record = self.record(src)
        except (validation.ValidationError, KeyError, TypeError, ValueError) as exc:
            return [Message("invalid", None, "error", {"error": str(exc)})]
        names = (record.get("material") or {}).get("names") or {}
        if not record.get("calculable"):
            code = record.get("reason_code")
            field = "material" if code else _field_of(record.get("reason") or "")
            out.append(Message(code or "not_calculable", field, "error", dict(record.get("reason_params") or {}, reason=record.get("reason") or "", **({"names": names} if names else {}))))
        for note in record.get("notes") or ():
            out.append(Message(note["code"], "material", "info", dict(note["params"], **({"names": names} if names else {}))))
        for warning in record.get("warnings") or ():
            code = getattr(warning, "code", "")
            if code == "check_position_missing":
                out.append(Message("position_gone", "position", "info", {"position": src.get("position") or ""}))
            elif code == "check_pith_glulam":
                out.append(Message("pith_glulam", "pith", "info", {"grade": record.get("grade") or ""}))
        if record.get("calculable"):
            result = mc.compute(record) or {}
            for note in result.get("notes") or ():
                out.append(Message(note["code"], note.get("field"), "info", dict(note["params"])))
        return out

    # --- the form (UI-002) ------------------------------------------------------------------------

    def declaration(self):
        sections = tuple((sid, tuple(tuple(FIELDS[k].key for k in entry) if isinstance(entry, tuple) else FIELDS[entry].key for entry in keys))
                         for sid, keys in SECTIONS[self.TAB])
        used = [k for _sid, keys in SECTIONS[self.TAB] for entry in keys for k in (entry if isinstance(entry, tuple) else (entry,))]
        own = EXCERPTS.get(self.TAB, {})
        fields = tuple(dataclasses.replace(FIELDS[k], excerpts=own[k]) if k in own else FIELDS[k] for k in used)
        return Declaration(PREFIX, NORM_FILE, sections, fields)

    def visible_fields(self, src):
        """The rows a draft shows: the angle but for a panel (D-19: its direction replaces it); the contact at an angle; the stability's lengths while it is ticked, a lateral torsional buckling's with a compression; the fields of the shear's figure chosen."""
        kind = src.get("kind") or self.KIND
        panel = mm.kind_of_id(src.get("material")) == "panel"
        alpha = src.get("alpha") or 0
        out = set()
        if self.TAB == "tension":
            out |= {"N"} | (set() if panel else {"alpha"})
        elif self.TAB == "compression":
            out |= {"N", STABILITY_KEY} | (set() if panel or kind == "buckling" else {"alpha"})
            if alpha > 0 and kind == "compression":
                out |= {SUPPORT_KEY, "l", "w"}
            if kind == "buckling":
                out |= {"l_y", "l_z", "beta_y", "beta_z"}
        elif self.TAB == "bending":
            out |= {"N", "M_y", "M_z", STABILITY_KEY} | (set() if panel or kind == "lateral-torsional" else {"alpha"})
            if kind == "lateral-torsional":
                out |= {"a"} | ({"sigma_m_crit"} if src.get("a") is None else set())
                if ((src.get("N") or {}).get("value") or 0) < 0:
                    out |= {"l_y", "l_z", "beta_y", "beta_z"}
        elif self.TAB == "shear":
            variant = src.get("variant") or "shear"
            out |= {"variant"} | ({"V_z", "V_y", "pith"} if variant == "shear" else {"F", "l", "w"} if variant == "shear-off" else {"V_z", "sigma_90"})
        return sorted(out)

    def choice_values(self, src):
        """What the choices of a field are worth for the draft, beside their words (calc_form.DeclaredForm): a compression's five cards of f_c,90,d (UI-008) -- each the value of SIA 265 Tabelle 8 or 9 for the draft's class, a card the table gives no value for greyed (D30's bracketed values) --; {} where the class is none of the norm's (a panel, a material of the engineer's own, no material)."""
        if self.TAB != "compression":
            return {}
        try:
            grade = self.record(src).get("grade")
        except (validation.ValidationError, KeyError, TypeError, ValueError):
            return {}
        if not grade or grade not in sia265.grades():
            return {}
        out = {}
        for support in SUPPORTS:
            larger = support.endswith(LARGER_SUFFIX)
            value = mc.f_c_90_table(grade, support[:-len(LARGER_SUFFIX)] if larger else support, larger)
            out[support] = {"value": value, "unit": "N/mm²", "enabled": value is not None, "tip": (PREFIX + "c_none", {"grade": grade})}
        return {SUPPORT_KEY: out}

    # --- the drawings (UI-009, UI-010) -------------------------------------------------------------

    def tile_svg(self, choice):
        return TILES.get(choice, TILES["shear"])

    def figure_svg(self, src, lang=None):
        """The drawing of the draft: for a bending the scheme in the style of SIA -- the bar, its moments, the normal force, the grain at α, the section with y, z, b, h, and σ along the height with its values at both edges, read off `compute` (UI-009) --; for the others the member and its action. No colour, no word."""
        try:
            record = self.record(src)
        except (validation.ValidationError, KeyError, TypeError, ValueError):
            return None
        result = mc.compute(record) if record.get("calculable") else None
        if (src.get("kind") or self.KIND) in ("bending", "lateral-torsional"):
            return bending_scheme(record, result)
        return member_sketch(record, result, src.get("kind") or self.KIND)

    def chart(self, src):
        """The figure of SIA 265 the check follows, with its point (UI-012): the buckling's k_c over λ_rel (Figur 10), the lateral torsional buckling's k_m over λ_rel,m (Figur 11), the shear with a stress across the grain over σ_90,d (equation (28), Figur 8); None for the others."""
        try:
            record = self.record(src)
        except (validation.ValidationError, KeyError, TypeError, ValueError):
            return None
        if not record.get("calculable"):
            return None
        result = mc.compute(record)
        rows = {r["key"]: r for r in result["rows"]}
        kind = record["kind"]
        if kind == "buckling" or (kind == "lateral-torsional" and "lambda_rel_y" in rows):
            return buckling_chart(record, rows)
        if kind == "lateral-torsional" and "lambda_rel_m" in rows:
            return lateral_chart(rows)
        if kind == "shear" and (record.get("variant") == "shear-perp"):
            return transverse_chart(record, rows)
        return None


def _field_of(reason):
    """The field a reason of before is about -- what the click on it takes the engineer to."""
    for word, key in (("section", "section"), ("strength class", "material"), ("moisture class", "moisture_class"), ("position", "position"),
                      ("N is", "N"), ("moment", "M_y"), ("shear force", "V_z"), ("sigma_90", "sigma_90"), ("l is", "l"), ("no l", "l"), ("no F", "F"),
                      ("system length", "l_y"), ("neither a", "a")):
        if word in reason:
            return key
    return None


DOMAINS = {tab: CheckDomain(tab) for tab in TABS}


def domain_of_kind(kind):
    """The tab's domain that lists a check of `kind`."""
    return next(d for d in DOMAINS.values() if kind in d.KINDS)


# --- the drawings, in the style of SIA: black and white, thin lines, italic letters -------------------------------------

_STYLE = "<style>line,path,rect,polyline,polygon,circle{stroke:#000;fill:none;stroke-width:1} .f{fill:#000;stroke:none} text{font-family:'Times New Roman',serif;font-style:italic;font-size:13px;fill:#000;stroke:none} .n{font-style:normal;font-size:11px}</style>"


def _svg(width, height, body):
    return "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 %d %d' width='%d' height='%d'>%s%s</svg>" % (width, height, width, height, _STYLE, body)


def _arrow(x1, y1, x2, y2, head=7):
    """A line from (x1, y1) to (x2, y2) with its head at the end."""
    angle = math.atan2(y2 - y1, x2 - x1)
    a = (x2 - head * math.cos(angle - 0.4), y2 - head * math.sin(angle - 0.4))
    b = (x2 - head * math.cos(angle + 0.4), y2 - head * math.sin(angle + 0.4))
    return "<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f'/><polygon class='f' points='%.1f,%.1f %.1f,%.1f %.1f,%.1f'/>" % (x1, y1, x2, y2, x2, y2, a[0], a[1], b[0], b[1])


def _moment(cx, cy, r, clockwise=True):
    """A moment drawn as an arc and its head."""
    sweep = 1 if clockwise else 0
    x1, y1, x2, y2 = cx - r, cy, cx + r * 0.7, cy - r * 0.7 if clockwise else cy + r * 0.7
    return "<path d='M %.1f %.1f A %.1f %.1f 0 0 %d %.1f %.1f'/>" % (x1, y1, r, r, sweep, x2, y2) + _arrow(x2 - 3, y2 - 3 if clockwise else y2 + 3, x2, y2, 6)


def _hatch(x, y, w, h, alpha, step=9):
    """The grain at `alpha` degrees to the bar, hatched inside a rectangle (clipped)."""
    lines = []
    a = math.radians(alpha)
    dx, dy = math.cos(a), -math.sin(a)
    length = w + h
    n = int(length / step) + 2
    for i in range(-n, n):
        ox, oy = x + w / 2 + i * step * -dy, y + h / 2 + i * step * dx
        cut = _clip(ox - dx * length, oy - dy * length, ox + dx * length, oy + dy * length, x, y, w, h)
        if cut:
            lines.append("<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke-width='0.5'/>" % cut)
    return "".join(lines)   # clipped here: Qt's SVG renderer draws no clipPath


def _clip(x1, y1, x2, y2, x, y, w, h):
    """The part of a segment inside a rectangle (Liang-Barsky), or None."""
    t0, t1, dx, dy = 0.0, 1.0, x2 - x1, y2 - y1
    for p, q in ((-dx, x1 - x), (dx, x + w - x1), (-dy, y1 - y), (dy, y + h - y1)):
        if p == 0:
            if q < 0:
                return None
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
        if t0 > t1:
            return None
    return (x1 + t0 * dx, y1 + t0 * dy, x1 + t1 * dx, y1 + t1 * dy)


def edge_stresses(result):
    """(top, bottom) of the stress over the height of a bending, from `compute`'s rows alone (UI-009): σ_m,y,d on each edge, with σ_t,d or σ_c,d added (tension positive) -- None where the check has no σ_m,y,d."""
    if not result:
        return None
    rows = {r["key"]: r["value"] for r in result["rows"]}
    sigma_m = rows.get("sigma_m_y_d", rows.get("sigma_m_alpha_d", rows.get("sigma_m_90_d")))
    if sigma_m is None:
        return None
    normal = rows.get("sigma_t_0_d", rows.get("sigma_t_alpha_d", 0.0)) - rows.get("sigma_c_0_d", rows.get("sigma_c_alpha_d", 0.0))
    return normal - sigma_m, normal + sigma_m


def bending_scheme(record, result):
    """The scheme of a bending (UI-009): the bar with M_y,d at both ends, N_d along it, the grain at α; the section, y, z, b, h, M_z,d as a double arrow; the stress over the height with its two edge values."""
    body = []
    alpha = record.get("alpha") or 0
    # the bar
    body.append("<rect x='40' y='40' width='200' height='40'/>")
    body.append(_hatch(40, 40, 200, 40, alpha))
    body.append(_moment(40, 60, 22, False) + _moment(240, 60, 22, True))
    body.append("<text x='8' y='30'>M<tspan dy='4' font-size='10'>y,d</tspan></text><text x='238' y='30'>M<tspan dy='4' font-size='10'>y,d</tspan></text>")
    normal = ((record.get("N") or {}).get("value") or 0)
    if normal:
        tension = normal > 0
        body.append(_arrow(240, 60, 275, 60) if tension else _arrow(275, 60, 242, 60))
        body.append(_arrow(40, 60, 5, 60) if tension else _arrow(5, 60, 38, 60))
        body.append("<text x='250' y='96'>N<tspan dy='4' font-size='10'>d</tspan></text>")
    if alpha:
        body.append("<text x='120' y='100'>α = %s°</text>" % _fmt(alpha))
    # the section
    section = record.get("section") or {}
    sx, sy = 330, 30
    if section.get("type") == "cir":
        body.append("<circle cx='%d' cy='%d' r='30'/>" % (sx + 30, sy + 30))
        body.append("<text x='%d' y='%d'>d</text>" % (sx + 26, sy + 76))
        hh = 60
    else:
        b, h = section.get("b") or 100, section.get("h") or 200
        scale = 60.0 / max(b, h)
        ww, hh = max(b * scale, 8), max(h * scale, 8)
        body.append("<rect x='%.1f' y='%.1f' width='%.1f' height='%.1f'/>" % (sx + 30 - ww / 2, sy + 30 - hh / 2, ww, hh))
        body.append("<text x='%.1f' y='%.1f'>b</text><text x='%.1f' y='%.1f'>h</text>" % (sx + 26, sy + 30 + hh / 2 + 16, sx + 30 + ww / 2 + 6, sy + 34))
    body.append(_arrow(sx + 30, sy + 30, sx + 75, sy + 30) + "<text x='%d' y='%d'>y</text>" % (sx + 78, sy + 34))
    body.append(_arrow(sx + 30, sy + 30, sx + 30, sy + 80) + "<text x='%d' y='%d'>z</text>" % (sx + 34, sy + 90))
    if record.get("M_z"):
        body.append(_arrow(sx + 30, sy - 10, sx + 30, sy - 26) + _arrow(sx + 30, sy - 4, sx + 30, sy - 20))
        body.append("<text x='%d' y='%d'>M<tspan dy='4' font-size='10'>z,d</tspan></text>" % (sx + 38, sy - 14))
    # the stress over the height, its values at both edges
    edges = edge_stresses(result)
    if edges is not None:
        top, bottom = edges
        ox, oy, height = 470, sy, 60
        span = max(abs(top), abs(bottom), 1e-9)
        k = 45 / span
        body.append("<line x1='%d' y1='%d' x2='%d' y2='%d'/>" % (ox, oy, ox, oy + height))
        body.append("<polyline points='%d,%d %.1f,%d %.1f,%d %d,%d'/>" % (ox, oy, ox + top * k, oy, ox + bottom * k, oy + height, ox, oy + height))
        body.append("<text class='n' x='%.1f' y='%d'>%s</text>" % (ox + top * k + (4 if top >= 0 else -44), oy - 4, _fmt(round(top, 2))))
        body.append("<text class='n' x='%.1f' y='%d'>%s</text>" % (ox + bottom * k + (4 if bottom >= 0 else -44), oy + height + 14, _fmt(round(bottom, 2))))
        body.append("<text x='%d' y='%d'>σ<tspan dy='4' font-size='10'>m,y,d</tspan></text>" % (ox + 8, oy + height / 2 + 4))
    return _svg(560, 130, "".join(body))


def member_sketch(record, result, kind):
    """The member and its action, for a tension, a compression, a buckling or a shear: a bar, its grain at α, the force drawn as the check reads it."""
    alpha = record.get("alpha") or 0
    body = ["<rect x='60' y='40' width='220' height='40'/>", _hatch(60, 40, 220, 40, alpha)]
    if kind == "tension":
        body.append(_arrow(280, 60, 330, 60) + _arrow(60, 60, 10, 60) + "<text x='300' y='50'>N<tspan dy='4' font-size='10'>t,d</tspan></text>")
    elif kind in ("compression", "buckling"):
        if alpha and kind == "compression":
            body.append("<rect x='140' y='80' width='60' height='10'/>" + _arrow(170, 6, 170, 38) + "<text x='178' y='20'>F<tspan dy='4' font-size='10'>c,d</tspan></text>")
        else:
            body.append(_arrow(330, 60, 282, 60) + _arrow(10, 60, 58, 60) + "<text x='300' y='50'>N<tspan dy='4' font-size='10'>c,d</tspan></text>")
    elif kind == "shear":
        variant = record.get("variant") or "shear"
        body.append(_arrow(170, 8, 170, 38) + "<text x='178' y='22'>%s</text>" % ("F<tspan dy='4' font-size='10'>a,d</tspan>" if variant == "shear-off" else "V<tspan dy='4' font-size='10'>z,d</tspan>"))
    if alpha:
        body.append("<text x='150' y='104'>α = %s°</text>" % _fmt(alpha))
    return _svg(340, 112, "".join(body))


# The three figures of the shear (UI-010): the shear of 4.2.5.1, the shear-off of 4.2.6, the shear with a stress across the grain of 4.2.7.1 -- drawn, no word
TILES = {
    "shear": _svg(98, 64, "<rect x='14' y='24' width='70' height='18'/>" + _arrow(49, 4, 49, 22, 5) + _arrow(49, 60, 49, 44, 5)),
    "shear-off": _svg(98, 64, "<path d='M 10 22 H 60 V 34 H 88 V 46 H 10 Z'/>" + _arrow(88, 28, 64, 28, 5) + "<line x1='60' y1='34' x2='10' y2='34' stroke-dasharray='3,2'/>"),
    "shear-perp": _svg(98, 64, "<rect x='14' y='24' width='70' height='18'/>" + _arrow(49, 4, 49, 22, 5) + _arrow(30, 4, 30, 22, 5) + _arrow(68, 4, 68, 22, 5)),
}


# --- the charts of the norm, the check's point on them (UI-012) --------------------------------------------------------

def _kc(lam, beta_c, clause):
    if lam <= clause["lambda_rel_limit"]:
        return 1.0
    k = clause["k_factor"] * (1 + beta_c * (lam - clause["lambda_rel_offset"]) + lam ** 2)
    return 1 / (k + math.sqrt(k ** 2 - lam ** 2))


def buckling_chart(record, rows):
    """k_c over λ_rel, SIA 265 4.2.8 (Figur 10), for the check's β_c -- the points about y and z marked."""
    from norms import sia265
    clause = sia265.buckling()
    beta_c = rows["beta_c"]["value"] if "beta_c" in rows else clause["beta_c"]["Vollholz"]
    points = [(x / 20, _kc(x / 20, beta_c, clause)) for x in range(0, 61)]
    marks = []
    for axis in ("y", "z"):
        lam = rows.get("lambda_rel_" + axis)
        if lam is not None and lam["value"] <= 3:
            marks.append({"x": lam["value"], "y": rows["k_c_" + axis]["value"], "label": "λ rel,%s" % axis, "series": "kc"})
    return {"x": {"label": "λ rel", "unit": "", "min": 0, "max": 3, "step": 0.5}, "y": {"label": "kc", "unit": "", "min": 0, "max": 1.0, "step": 0.2},
            "series": [{"name": "kc", "points": points}], "marks": marks}


def lateral_chart(rows):
    """k_m over λ_rel,m, SIA 265 4.2.9 (Figur 11), the check's point."""
    from norms import sia265
    km = sia265.lateral_buckling()["k_m"]

    def k_m(lam):
        return 1.0 if lam <= km["lower_bound"] else km["intercept"] - km["slope"] * lam if lam <= km["upper_bound"] else 1 / lam ** 2
    points = [(x / 20, k_m(x / 20)) for x in range(0, 61)]
    lam = rows["lambda_rel_m"]["value"]
    marks = [{"x": lam, "y": rows["k_m"]["value"], "label": "λ rel,m", "series": "km"}] if lam <= 3 else []
    return {"x": {"label": "λ rel,m", "unit": "", "min": 0, "max": 3, "step": 0.5}, "y": {"label": "km", "unit": "", "min": 0, "max": 1.0, "step": 0.2},
            "series": [{"name": "km", "points": points}], "marks": marks}


def transverse_chart(record, rows):
    """Equation (28) as SIA 265 Figur 8 draws it: the shear stress the member resists, τ_d / f_v,d at η = 1, over σ_90,d from −f_c,90,d to f_t,90,d -- the check's point."""
    f_c90, f_t90, k = rows["f_c_90_d"]["value"], rows["f_t_90_d"]["value"], rows["k_t_90"]["value"]
    from norms import sia265
    k_q, k_z = sia265.shear_transverse()["k_t_90"]["querdruck"], sia265.shear_transverse()["k_t_90"]["querzug"]

    def allowed(sigma):
        kk = k_z if sigma >= 0 else k_q
        denominator = f_c90 + kk * f_t90
        part = ((f_c90 + sigma) / denominator) ** 2
        resisted = (f_c90 / denominator) ** 2
        rest = (1 - part) / (1 - resisted) if resisted < 1 else 0
        return math.sqrt(max(rest, 0.0))
    sigma_now = rows["sigma_90_d"]["value"]
    lo, hi = min(-f_c90, sigma_now), max(f_t90, sigma_now)
    points = [(lo + (hi - lo) * i / 40, allowed(lo + (hi - lo) * i / 40)) for i in range(41)]
    sigma = rows["sigma_90_d"]["value"]
    ratio = rows["tau_d"]["value"] / rows["f_v_d"]["value"]
    step = round(max((hi - lo) / 4, 0.1), 1)
    return {"x": {"label": "σ90,d", "unit": "N/mm²", "min": round(lo, 2), "max": round(hi, 2), "step": step},
            "y": {"label": "τd/fv,d", "unit": "", "min": 0, "max": max(1.2, math.ceil(max(y for _x, y in points + [(0, ratio)]) * 5) / 5), "step": 0.2},
            "series": [{"name": "η = 1", "points": points}], "marks": [{"x": sigma, "y": ratio, "label": "σ90,d", "series": "τd/fv,d"}]}
