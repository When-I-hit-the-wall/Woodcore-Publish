"""What a report prints out of an RFEM model (`lib/rfem.typ`, `calc/domains/rfem.py`).

The engineer's own three: «(1) affichage de l'effort maximal, et affichage de la combinaison de charge qui a calculé cet effort maximal (e.g. CO33), (2) affichage d'un tableau qui contient tous les efforts ou déformations maximales ainsi que les combinaisons de charge qui les ont calculés», and «les combinaisons de charge: affichage de la formule … 1.35 * CC1 + 1.5 * CC2 ou en remplaçant CC1 et CC2 par leur nom».

⚠️ **The design situation is always stated, and a call that leaves it out is refused.** His own rule — «il faut toujours préciser quelle situation ou combinaison on regarde» — and it is enforced rather than defaulted, because an ELU moment and an ELS moment differ by half and a default would print one under the other's name.

⚠️ **The load case's name may itself be a sum.** This model's CC1 is «EG + AL», so `1.35 · EG + AL + 1.50 · Schnee` reads as three terms and means nothing. The engineer's own answer: parenthesise as soon as the name is not a simple word.

👉 The example project names no RFEM export, so these tests write a small `data/rfem.json` into this process's own copy of it. That is also why the commands' `///` examples are `typ-dry` for now (`tests/test_commands.py`): a real export in the example project is what would let the website show these tables (docs/open-questions.md §14).
"""

import json
import re
import subprocess

import conftest
from conftest import Skip

# One structure, two bars, a support node, two design situations -- the shape `calc/domains/rfem.py` writes.
FIXTURE = {
    "schema_version": "1.0",
    "cases": {
        "CC1": {"name": "EG + AL", "category": "Permanent", "action": "permanent"},
        "CC2": {"name": "Schnee", "category": "Neige/glace", "action": "variable"},
    },
    "combinations": {
        "CO1": {"name": "1.35 * CC1", "situation": "SP1 - ELU Type 2 - Fondamental",
                "terms": [[1.35, "CC1"]]},
        "CO3": {"name": "1.35 * CC1 + 1.50 * CC2", "situation": "SP1 - ELU Type 2 - Fondamental",
                "terms": [[1.35, "CC1"], [1.5, "CC2"]]},
        "CO36": {"name": "1.00 * CC1 + 1.00 * CC2", "situation": "SP2 - ELS - Rare",
                 "terms": [[1.0, "CC1"], [1.0, "CC2"]]},
    },
    "structures": {
        "VU-Probe": {
            "label": "Velo Unterstand — Probe",
            "description": "",
            "export": "probe.xlsx",
            "engine": "rfem",
            "bars": [
                {"id": "T001_1", "position": "T001", "index": 1, "member": 2,
                 "length": 4.23, "section": "R_M1 500/200", "material": "C24"},
                {"id": "S001_1", "position": "S001", "index": 1, "member": 1,
                 "length": 2.95, "section": "R_M1 500/200", "material": "C24"},
            ],
            "support_nodes": [1],
            "situations": {"SP1": "SP1 - ELU Type 2 - Fondamental", "SP2": "SP2 - ELS - Rare"},
            "zero": {"T001_1": ["Mz", "Vy"]},
            "vars": {},
            "steps": [], "checks": [], "results": [],
            "calculated": True, "reason": "",
        },
        "VU-Leer": {
            "label": "eine Struktur ohne Ergebnis", "description": "", "export": "probe.xlsx",
            "engine": "rfem", "bars": [], "support_nodes": [], "situations": {}, "zero": {},
            "vars": {}, "steps": [], "checks": [], "results": [],
            "calculated": False,
            "reason": "this export carries no result combination -- calculate the model in RFEM",
        },
    },
}


def _var(bar, quantity, kind, value, unit, loading, situation, at=None, symbol=None):
    return {
        "value": value, "unit": unit, "symbol": symbol or f'{quantity}_("{kind}")',
        "label": ("Grösster" if kind == "max" else "Kleinster") + f" Wert von {quantity}, Stab {bar}",
        "level": 2, "source": f"rfem:probe.xlsx!{situation}!{loading}", "norm": "", "norm_ref": "",
        "loading": loading, "at": at, "situation": situation, "bar": bar,
        "quantity": quantity, "kind": kind,
    }


def _fixture():
    """The fixture written into this process's own copy of the example project, once."""
    vars = FIXTURE["structures"]["VU-Probe"]["vars"]
    if not vars:
        for name, value in (
            ("SP1_T001_1_M_y_max", _var("T001_1", "My", "max", 0.055, "kNm", "CO1", "SP1", 0.0, 'M_y_("max")')),
            ("SP1_T001_1_M_y_min", _var("T001_1", "My", "min", -15.019, "kNm", "CO3", "SP1", 2.115, 'M_y_("min")')),
            ("SP1_T001_1_V_z_max", _var("T001_1", "Vz", "max", 7.551, "kN", "CO3", "SP1", 2.115, 'V_z_("max")')),
            ("SP1_T001_1_V_z_min", _var("T001_1", "Vz", "min", -7.551, "kN", "CO3", "SP1", 2.115, 'V_z_("min")')),
            ("SP1_S001_1_N_min", _var("S001_1", "N", "min", -26.985, "kN", "CO3", "SP1", 0.0, 'N_("min")')),
            ("SP2_T001_1_u_z_max", _var("T001_1", "uz", "max", 9.147, "mm", "CO36", "SP2", 2.115, 'u_z_("max")')),
            ("SP1_N1_P_z_max", _var("N1", "Pz", "max", 26.985, "kN", "CO3", "SP1", None, 'P_z_("max")')),
        ):
            vars[name] = value
    path = conftest.PROJECT.data_dir / "rfem.json"
    path.write_text(json.dumps(FIXTURE, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def _compile(body, name, lang=None):
    """Compiles `body` in the example project's report, as a section would; `(ok, text or the refusal)`."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    _fixture()
    folder = conftest.probe_dir(name)
    probe = folder / "probe.typ"
    head = '#import "/commands.typ": *\n'
    if lang:
        head += f'#set-report-language("{lang}")\n'
    probe.write_text(head + body + "\n", encoding="utf-8")
    out = subprocess.run(
        ["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(probe), str(folder / "probe.pdf")],
        capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        message = conftest.panic_message(out.stderr)
        return False, message if message is not None else out.stderr
    from pypdf import PdfReader
    raw = "\n".join(page.extract_text() for page in PdfReader(str(folder / "probe.pdf")).pages)
    return True, re.sub(r"\s+", " ", raw)


# --- the domain is addressable ------------------------------------------------

def test_a_structure_is_a_domain_instance_every_command_reads():
    """The whole point of giving it the §3.3 shape: nothing in the report had to be taught about RFEM."""
    ok, text = _compile('#rfem-ids().join(", ")', "ids")
    assert ok, text
    assert "VU-Probe" in text and "VU-Leer" in text


def test_val_reads_an_extreme_by_name():
    """`#val` works on it unchanged, which is what «one instance per structure» bought."""
    ok, text = _compile('#val("SP1_T001_1_M_y_min", domain: ("rfem", "VU-Probe"), level: 1)', "val")
    assert ok, text
    assert "15.019" in text and "kNm" in text
    assert "−" in text, "a negative value is printed with a minus sign and not a hyphen"


def test_a_structure_with_no_result_is_refused_with_its_reason():
    ok, message = _compile('#rfem-max("VU-Leer", "T001_1", "My", situation: "SP1")', "noresult")
    assert not ok
    assert "carries no result" in message and "calculate the model in RFEM" in message


def test_an_unknown_structure_lists_the_ones_there_are():
    ok, message = _compile('#rfem-max("Nirgends", "T001_1", "My", situation: "SP1")', "unknown")
    assert not ok
    assert "VU-Probe" in message


# --- (1) one extreme, with the combination that produced it -------------------

def test_one_extreme_prints_its_value_and_its_combination():
    """The engineer's own (1): the force, and the combination that calculated it."""
    ok, text = _compile('#rfem-max("VU-Probe", "T001_1", "My", situation: "SP1", kind: "min", level: 1)', "max1")
    assert ok, text
    assert "15.019" in text and "kNm" in text
    assert "(CO3)" in text, "the combination RFEM named beside it"


def test_the_combination_can_be_left_off():
    ok, text = _compile('#rfem-max("VU-Probe", "T001_1", "My", situation: "SP1", kind: "min", loading: false, level: 1)', "max2")
    assert ok, text
    assert "15.019" in text and "CO3" not in text


def test_its_levels_add_what_the_value_is_and_where_it_stands():
    ok, one = _compile('#rfem-max("VU-Probe", "T001_1", "My", situation: "SP1", kind: "min", level: 1)', "lvl1")
    ok3, three = _compile('#rfem-max("VU-Probe", "T001_1", "My", situation: "SP1", kind: "min", level: 3)', "lvl3")
    assert ok and ok3, (one, three)
    assert "Stab" not in one, "level 1 is the value and the combination"
    assert "Stab T001_1" in three and "2.115" in three, "level 3 says what it is and where it stands"
    assert "ELU" in three, "and which design situation it came from"
    ok0, zero = _compile('X#rfem-max("VU-Probe", "T001_1", "My", situation: "SP1", level: 0)Y', "lvl0")
    assert ok0 and "XY" in zero, "level 0 prints nothing at all"


def test_a_quantity_the_bar_has_not_got_says_what_it_has():
    ok, message = _compile('#rfem-max("VU-Probe", "T001_1", "MT", situation: "SP1")', "noq")
    assert not ok
    assert "it carries" in message and "My" in message
    assert "identically zero on it" in message and "Mz" in message, (
        "a quantity a plane model has none of is named apart from one the bar simply has not got"
    )


# --- the design situation is always stated ------------------------------------

def test_a_call_that_names_no_situation_is_refused_with_the_ones_there_are():
    """The engineer's own rule, enforced rather than defaulted."""
    ok, message = _compile('#rfem-max("VU-Probe", "T001_1", "My")', "nosit")
    assert not ok
    assert "say which design situation" in message
    assert "SP1" in message and "SP2" in message


def test_a_situation_the_structure_has_not_got_is_refused():
    ok, message = _compile('#rfem-max("VU-Probe", "T001_1", "My", situation: "SP9")', "badsit")
    assert not ok
    assert "SP1, SP2" in message


def test_the_same_bar_reads_differently_in_two_situations():
    """Which is why the situation is in the name: one instance per structure, four maxima per bar."""
    ok, elu = _compile('#rfem-max("VU-Probe", "T001_1", "My", situation: "SP1", kind: "min", level: 1)', "sit1")
    ok2, els = _compile('#rfem-max("VU-Probe", "T001_1", "uz", situation: "SP2", level: 1)', "sit2")
    assert ok and ok2, (elu, els)
    assert "CO3" in elu and "CO36" in els


# --- (2) the table ------------------------------------------------------------

def test_the_table_holds_every_extreme_of_a_bar_with_its_combination():
    """The engineer's own (2)."""
    ok, text = _compile('#show-rfem-forces("VU-Probe", "T001_1", situation: "SP1")', "table")
    assert ok, text
    for wanted in ("15.019", "7.551", "CO3", "CO1", "kNm", "kN"):
        assert wanted in text, f"{wanted} is missing from the table: {text[:400]}"


def test_the_table_reads_a_support_node_the_same_way():
    """A bar is `T001_1` and a support is `N1`; the export gives them one shape, so one command serves both."""
    ok, text = _compile('#show-rfem-forces("VU-Probe", "N1", situation: "SP1")', "reactions")
    assert ok, text
    assert "26.985" in text and "CO3" in text


def test_the_tables_levels_add_the_combination_and_the_abscissa():
    ok1, one = _compile('#show-rfem-forces("VU-Probe", "T001_1", situation: "SP1", level: 1)', "t1")
    ok3, three = _compile('#show-rfem-forces("VU-Probe", "T001_1", situation: "SP1", level: 3)', "t3")
    assert ok1 and ok3, (one, three)
    assert "CO3" in one, "the combination is what the table is for, so it is there at level 1"
    assert "2.115" not in one, "where along the bar it stands is a checker's question"
    assert "CO3" in three and "2.115" in three, "level 3 says where along the bar each extreme stands"


def test_the_table_takes_the_quantities_a_call_names():
    ok, text = _compile('#show-rfem-forces("VU-Probe", "T001_1", situation: "SP1", quantities: ("My",))', "tq")
    assert ok, text
    assert "15.019" in text and "7.551" not in text


def test_the_tables_words_follow_the_reports_language():
    ok, fr = _compile('#show-rfem-forces("VU-Probe", "T001_1", situation: "SP1")', "tfr", lang="fr")
    assert ok, fr
    assert "Combinaison" in fr and "Grandeur" in fr


# --- the combination's formula ------------------------------------------------

def test_a_combination_prints_as_its_factors_and_cases():
    ok, text = _compile('#show-rfem-combination("CO3")', "co")
    assert ok, text
    assert "1.35" in text and "CC1" in text and "1.5" in text and "CC2" in text


def test_a_combination_prints_with_the_cases_own_names():
    ok, text = _compile('#show-rfem-combination("CO3", names: true)', "conames")
    assert ok, text
    assert "Schnee" in text


def test_a_case_whose_name_is_itself_a_sum_is_parenthesised():
    """CC1 is «EG + AL», so `1.35 · EG + AL + 1.50 · Schnee` would read as three terms and mean nothing.

    The engineer's own answer: parenthesise as soon as the name is not a simple word.
    """
    ok, text = _compile('#show-rfem-combination("CO3", names: true)', "coparen")
    assert ok, text
    assert "(EG + AL)" in text, f"the sum must be bracketed: {text[:200]}"
    ok2, simple = _compile('#show-rfem-combination("CO3", names: true)', "coparen2")
    assert ok2 and "(Schnee)" not in simple, "a simple word is not bracketed"


def test_the_combinations_levels_name_it_and_its_situation():
    ok1, one = _compile('#show-rfem-combination("CO3", level: 1)', "co1")
    ok3, three = _compile('#show-rfem-combination("CO3", level: 3)', "co3")
    assert ok1 and ok3, (one, three)
    assert "CO3 =" not in one
    assert "CO3 =" in three and "ELU" in three


def test_an_unknown_combination_lists_what_the_export_carries():
    ok, message = _compile('#show-rfem-combination("CO999")', "conone")
    assert not ok
    assert "CO1" in message and "CO3" in message
