"""`#member` and the `verify-*` commands -- the member checks of SIA 265:2021, chapter 4.2, computed in the report (lib/timber.typ, v0.88).

A check is a run of `#eq` and `#verify` of lib/formula.typ, so what is held here is not the arithmetic of the unit algebra (tests/test_formula.py holds that) but what the checks put into it:

* **one list of norm files**, named in lib/timber.typ, calc/norms/sia265.py, project.ENGINE_FILES and the examples' fixture -- a file one of them forgets is a report that fails on «file not found» in a project and nowhere in the checkout;
* **the answers**, each re-derived here in Python from the norm's own equations and the transcribed tables, and compared with the value the check stored in its `var-domain`: the design values of a member, buckling (29)-(34), lateral torsional buckling (38)-(41) on each branch of (39), the interactions (14), (21), (22), (37), tension and compression at an angle (9), (13), bending at an angle (19), (20), shear, torsion (25), Abscheren (26)/(27) and (28);
* **the refusals**: a compression handed to verify-tension, a tension to verify-compression, a member never written down, a buckling length left out, C16 in tension (Tabelle 8 note 2) -- and since v0.94, where `#member` takes any position, a check on a position it computed not: a steel one, a plate, a CLT panel, one with no section, no moisture class, or exported before its section was read;
* **a round section** (v0.94): its section values, k_h, the shear stress 4/3 V/A, buckling with i = d/4, and no lateral torsional buckling -- re-derived here as the rectangle's are, and the reference template for a round column reproduced (tests/fixtures/timber-oracles.json);
* **the worked examples** of tests/fixtures/timber-oracles.json, where a published example gives one.

⚠️ Skipped where `typst` is not on the path.
"""

import json
import math
import re
import shutil
import subprocess

import conftest
from conftest import ROOT, Skip

import project
from norms import sia265

TYPST_ROOT = conftest.TYPST_ROOT
TIMBER_TYP = ROOT / "lib" / "timber.typ"


def _run(body, tag="out"):
    """Compiles `body` against the report's own commands; returns ("ok", value of `metadata(...) <out>`) or ("error", message)."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.probe_dir("timber")
    probe = d / "probe.typ"
    probe.write_text('#import "/commands.typ": *\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(
        ["typst", "query", "--root", str(TYPST_ROOT), str(probe), f"<{tag}>", "--field", "value", "--one"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode != 0:
        message = conftest.panic_message(out.stderr)
        if message is None:  # not a panic but a compile error of its own -- a file not found, a syntax error
            found = re.search(r"error: (.*?)\n", out.stderr, re.S)
            message = found.group(1) if found else out.stderr.strip()
        return ("error", message)
    return ("ok", json.loads(out.stdout))


def _stored(body, domain, keys):
    """Runs `body` and reads the values of `keys` out of the var-domain `domain`."""
    read = ", ".join(f'"{k}": var-registry.get().domains.at("{domain}").at("{k}").value' for k in keys)
    kind, got = _run(body + f"\n#context [#metadata(({read},)) <out>]")
    assert kind == "ok", f"expected values, got an error:\n  {got}"
    return got


def _error(body):
    kind, got = _run(body + "\n#metadata(none) <out>")
    assert kind == "error", f"expected a refusal, got {got!r}"
    return got


def close(a, b, rel=1e-9):
    return abs(a - b) <= rel * max(1.0, abs(b))


# --- the norm as the tests read it: from calc/norms/, by Python's own reader -----------

def grade(name):
    for table in (sia265.table_8(), sia265.table_9()):
        for g in table["grades"]:
            if g["id"] == name:
                return g
    raise KeyError(name)


def char(name):
    return sia265.characteristic(name)


def eta_w(moisture, kind="resistance"):
    return sia265.eta_w(moisture, kind)


# --- one list of files -----------------------------------------------------------

def test_one_list_of_files_in_four_places():
    """lib/timber.typ, sia265.py, project.ENGINE_FILES and the examples' fixture name the same norm files."""
    typst = set(re.findall(r'"(sia265-2021-[a-z0-9.-]+)"', TIMBER_TYP.read_text(encoding="utf-8")))
    assert typst, "lib/timber.typ names no norm file"
    for name in typst:
        assert (ROOT / "calc" / "norms" / (name + ".json")).is_file(), f"lib/timber.typ names {name}, which calc/norms/ does not carry"
        assert name in sia265.FILES or name in sia265.MEMBER_FILES, f"calc/norms/sia265.py never checks {name}"
    engine = {n[len("calc/norms/"):-len(".json")] for n in project.ENGINE_FILES if n.startswith("calc/norms/")}
    assert typst <= engine, "project.ENGINE_FILES lacks %s" % sorted(typst - engine)
    assert "lib/timber.typ" in project.ENGINE_FILES
    fixture = ROOT / "examples" / "calc" / "norms"
    missing = sorted(n for n in typst if not (fixture / (n + ".json")).is_file())
    assert not missing, "examples/calc/norms/ lacks %s -- run calc/tools/build_examples.py --freeze" % missing


def test_the_public_commands_reach_the_sections_and_the_helpers_do_not():
    """formula.typ imports the commands by name, so commands.typ's wildcard carries them and none of the helpers."""
    formula = (ROOT / "lib" / "formula.typ").read_text(encoding="utf-8")
    line = re.search(r'#import\s+"timber\.typ":\s*(.*)', formula).group(1)
    imported = {n.strip() for n in line.split(",")}
    assert imported == {"member", "verify-tension", "verify-compression", "verify-compression-perp", "verify-bending",
                        "verify-bending-normal", "verify-shear", "verify-shear-off", "verify-shear-perp",
                        "show-check-member", "check-member-ids"}
    assert not any(n.startswith("timber-") for n in imported)


# --- the member -------------------------------------------------------------------

def test_a_member_reads_its_position():
    """S001 of the example project: C24, 100/200 mm, Feuchteklasse 2 -- read, and the design values times eta_w."""
    got = _stored('#member("S001", level: 0)', "S001", ("b", "h", "A", "W_y", "i_z", "eta_w", "f_c_0_d", "f_m_y_d", "E_0_05", "f_c_0_k"))
    g, c = grade("C24"), char("C24")
    assert (got["b"], got["h"]) == (100, 200)
    assert close(got["A"], 20000) and close(got["W_y"], 100 * 200 ** 2 / 6) and close(got["i_z"], 100 / math.sqrt(12))
    assert got["eta_w"] == eta_w(2)
    assert close(got["f_c_0_d"], eta_w(2) * g["f_c_0_d"])
    assert close(got["f_m_y_d"], eta_w(2) * g["f_m_d"])
    # the stiffness takes eta_w for the stiffness (the engineer's rule, v0.88), and E_0,05 is Anhang B's, not 2/3 of E_0,mean
    assert close(got["E_0_05"], eta_w(2, "stiffness") * c["E_0_05"])
    assert got["f_c_0_k"] == c["f_c_0_k"]


def test_what_the_call_states_wins_over_the_position():
    got = _stored('#member("S001", b: 120, h: 280, grade: "GL24h", moisture-class: 1, level: 0)', "S001", ("b", "h", "f_c_0_d", "eta_w"))
    assert (got["b"], got["h"], got["eta_w"]) == (120, 280, 1)
    assert close(got["f_c_0_d"], grade("GL24h")["f_c_0_d"])


def test_k_h_is_glulam_s_and_a_side_under_600_mm():
    """3.4.2.3: k_h = (600/h)^0.1 <= 1.1 for glulam, 1 for solid timber, 1 when switched off."""
    kh = sia265.k_h()
    got = _stored('#member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: 0)', "P", ("k_h_y", "k_h_z", "f_m_y_d"))
    assert close(got["k_h_y"], (kh["reference_height"] / 400) ** kh["exponent"])
    assert close(got["k_h_z"], kh["maximum"])          # (600/100)^0.1 = 1.196, capped
    assert close(got["f_m_y_d"], got["k_h_y"] * grade("GL24h")["f_m_d"])
    off = _stored('#member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, k-h: false, level: 0)', "P", ("k_h_y",))
    assert off["k_h_y"] == 1
    solid = _stored('#member("P", b: 100, h: 400, grade: "C24", moisture-class: 1, level: 0)', "P", ("k_h_y",))
    assert solid["k_h_y"] == 1


def test_a_member_is_refused_what_it_cannot_be():
    assert "no position" in _error('#member("X", position: "Z999")')
    assert "stated in the call" in _error('#member("X", b: 100, h: 200)')  # no position, no grade
    assert "not both" in _error('#member("X", b: 100, d: 200, grade: "C24", moisture-class: 1)')
    assert "no strength class" in _error('#member("S001", grade: "S355")'), "a grade the call states is refused where Tabellen 8 and 9 do not give it"


# --- any position (v0.94) ------------------------------------------------------------

# A check on a member, with the actions it cannot do without -- build_reference's own, so the copied calls and these refusals name the same.
def _checks():
    from tools import build_reference
    return {name: ", ".join(f"{k}: {v}" for k, v in args.items()) for name, args in build_reference.MEMBER_CHECKS.items()}


def test_any_position_is_a_member_and_one_no_check_can_use_says_why():
    """S002 of the example project is a steel column, ROR 101.6×10 of S355: `#member` prints its line -- which is what Sections/003 loops over every position for -- computes nothing, and every check on it is refused naming why, in the words the engineer gave: «S002 is steel (ROR 101.6×10, S355): #member computes timber of SIA 265 Tabelle 8/9 only»."""
    kind, _ = _run('#member("S002")\n#member("S002", level: 3, description: true, axes: "Achse 1")\n#metadata(none) <out>')
    assert kind == "ok"
    for name, args in _checks().items():
        message = _error(f'#member("S002", level: 0)\n#{name}("S002", {args})')
        assert "S002 is steel (ROR 101.6×10, S355)" in message and "Tabelle 8/9 only" in message, (name, message)


def _planted(name, records, index=None):
    """A Typst root of this test's own -- the example project's report folder and generated folder -- with `records` planted as positions, and the positions index replaced by `index` where one is given."""
    root = conftest.tmpdir(name)
    for f in ("commands.typ", "config.typ"):
        shutil.copyfile(TYPST_ROOT / f, root / f)
    generated = conftest.PROJECT.generated_dir
    relative = generated.relative_to(TYPST_ROOT)
    shutil.copytree(generated, root / relative, copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("out", "docs"))
    data = root / relative / "data"
    base = json.loads((data / "positions" / "S001.json").read_text(encoding="utf-8"))
    ids = json.loads((data / "positions-index.json").read_text(encoding="utf-8"))["positions"]
    for pid, fields in records.items():
        record = dict(base, position=pid, **fields)
        for key in [k for k, v in fields.items() if v is ...]:
            record.pop(key)
        (data / "positions" / f"{pid}.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        ids.append(pid)
    (data / "positions-index.json").write_text(json.dumps({"schema_version": "1.0", "positions": ids if index is None else index}), encoding="utf-8")
    return root


def _run_in(root, body):
    """Compiles `body` in the planted project `root`; returns None where it compiled, else the message it was refused with.

    A refusal here is a **panic** and not something printed on the page: `#member` writes a position it cannot compute down as `calculable: false` with its reason, and every `verify-*` then refuses it with that reason (docs/domain/member-checks.md §3.3undecies), the way every other refusal of this engine refuses -- an unknown id, a level outside the five. So a caller reads the panic's message, which is what this returns.
    """
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    probe = root / "probe.typ"
    probe.write_text('#import "/commands.typ": *\n' + body + "\n#metadata(none) <out>\n", encoding="utf-8")
    out = subprocess.run(["typst", "query", "--root", str(root), str(probe), "<out>", "--field", "value", "--one"],
                         capture_output=True, text=True, encoding="utf-8")
    if out.returncode == 0:
        return None
    message = conftest.panic_message(out.stderr)
    return message if message is not None else out.stderr.strip()


def test_a_position_no_check_can_use_is_printed_and_refused_by_its_reason():
    """A plate, a CLT panel, a position with no section, one exported before its section was read, and one with no moisture class: each is a member whose line prints, and on which a check is refused saying why and what to do."""
    from domains import section
    root = _planted("timber_positions", {
        "D901": {"type": "Decke", "section_type": "pla", "dimension": "22", "section": section.parse("pla", "22", "mm")},
        "D902": {"type": "Decke", "section_type": "clt", "dimension": "20/30/20", "section": section.parse("clt", "20/30/20", "mm")},
        "D903": {"type": "Decke", "section_type": "", "dimension": "180", "section": None},
        "T903": {"section": ..., "section_type": ...},
        "T904": {"moisture_class": None},
    })
    for pid, words in (("D901", "is a plate (22 mm)"), ("D902", "is a CLT panel (20/30/20 mm (70 mm))"), ("D903", "has no section -- its dimension"),
                       ("T903", "was exported before"), ("T904", "states no moisture class")):
        assert _run_in(root, f'#member("{pid}", level: 3)') is None, pid
        message = _run_in(root, f'#member("{pid}", level: 0)\n#verify-shear("{pid}", V: 12)')
        assert message is not None and message.startswith(f"verify-shear: {pid} ") and words in message, (pid, message)
    # what the call states is still computed on any of them
    assert _run_in(root, '#member("D901", b: 100, h: 200, grade: "C24", level: 0)\n#verify-shear("D901", V: 12)') is None


def test_a_position_named_in_a_project_with_no_positions_is_refused_by_name():
    """`#member("X", position: "Z999")` in a project with no position joined an empty list into its message, which gives none and not a string, and failed on that instead (v0.94)."""
    root = _planted("timber_no_positions", {}, index=[])
    message = _run_in(root, '#member("X", position: "Z999", level: 0)')
    assert message is not None and "none in Woodcore's Positions tab yet" in message, message
    assert "none in Woodcore's Positions tab yet" in _run_in(root, '#calc-block("Z999")[Body]')


# --- a round section (v0.94) -----------------------------------------------------------

def test_a_round_member_s_section_values_are_the_circle_s():
    """d = 200 mm: A = π·d²/4, W = π·d³/32, I = π·d⁴/64, i = d/4 about either axis, W_t = π·d³/16 -- mechanics, exact -- and k_h of a glulam round section read at its diameter."""
    d = 200
    got = _stored('#member("R", d: 200, grade: "GL24h", moisture-class: 1, level: 0)', "R",
                  ("A", "W_y", "W_z", "I_y", "I_z", "i_y", "i_z", "W_t", "b", "h", "k_h_y", "k_h_z", "f_m_y_d", "f_m_z_d"))
    assert close(got["A"], math.pi * d ** 2 / 4) and close(got["W_y"], math.pi * d ** 3 / 32) and close(got["W_z"], got["W_y"])
    assert close(got["I_y"], math.pi * d ** 4 / 64) and close(got["I_z"], got["I_y"])
    assert close(got["i_y"], d / 4) and close(got["i_z"], d / 4)
    assert close(got["W_t"], math.pi * d ** 3 / 16)
    assert (got["b"], got["h"]) == (d, d), "d stands for b and h where a check reads a side"
    kh = sia265.k_h()
    assert close(got["k_h_y"], min((kh["reference_height"] / d) ** kh["exponent"], kh["maximum"])) and got["k_h_z"] == got["k_h_y"]
    assert close(got["f_m_y_d"], got["k_h_y"] * grade("GL24h")["f_m_d"]) and close(got["f_m_z_d"], got["f_m_y_d"])


def test_a_round_member_s_shear_is_four_thirds_and_its_buckling_reads_d_over_4():
    body = '#member("R", d: 160, grade: "C24", moisture-class: 1, level: 0)\n'
    shear = _stored(body + '#verify-shear("R", V: 15, T: 0.5, level: 0)', "R-verify-shear", ("tau_d", "tau_tor_d", "eta"))
    fv = grade("C24")["f_v_d"]
    assert close(shear["tau_d"], 4 / 3 * 15e3 / (math.pi * 160 ** 2 / 4))
    assert close(shear["tau_tor_d"], 0.5e6 / (math.pi * 160 ** 3 / 16))
    assert close(shear["eta"], shear["tau_tor_d"] / fv + (shear["tau_d"] / fv) ** 2)
    perp = _stored(body + '#verify-shear-perp("R", V: 15, sigma-90: -1.2, level: 0)', "R-verify-shear-perp", ("tau_d",))
    assert close(perp["tau_d"], shear["tau_d"])
    buckling = _stored(body + '#verify-compression("R", N: -60, l-k-y: 3000, l-k-z: 2000, level: 0)', "R-verify-compression", ("lambda_y", "lambda_z", "k_c_y", "k_c_z", "eta"))
    c = char("C24")
    for axis, lk in (("y", 3000), ("z", 2000)):
        lam = lk / (160 / 4)
        assert close(buckling["lambda_" + axis], lam)
        assert close(buckling["k_c_" + axis], kc(lam / math.pi * math.sqrt(c["f_c_0_k"] / c["E_0_05"]), 0.2)), axis


def test_a_round_member_does_not_tip():
    """Lateral torsional buckling does not apply to a round section, being as stiff about either axis: with `a:` the check computes no k_m and says so on the page; in (37) k_m is 1 (v0.94, the engineer's rule)."""
    body = '#member("R", d: 200, grade: "C24", moisture-class: 1, level: 0)\n'
    for check, domain, extra in (("verify-bending", "R-verify-bending", ""), ("verify-bending-normal", "R-verify-bending-normal", ", N: -40, l-k-y: 3000, l-k-z: 3000")):
        kind, keys = _run(body + f'#{check}("R", M-y: 5, a: 3000{extra}, level: 0)\n#context [#metadata(var-registry.get().domains.at("{domain}").keys()) <out>]')
        assert kind == "ok" and "lambda_rel_m" not in keys and "sigma_m_crit" not in keys, (check, keys)
    got = _stored(body + '#verify-bending("R", M-y: 5, a: 3000, level: 0)', "R-verify-bending", ("eta", "eta_s"))
    assert got["eta"] == got["eta_s"]
    normal = _stored(body + '#verify-bending-normal("R", N: -40, M-y: 5, l-k-y: 3000, l-k-z: 3000, a: 3000, level: 0)', "R-verify-bending-normal", ("k_m",))
    assert normal["k_m"] == 1
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.probe_dir("timber_round_note")
    probe = d / "probe.typ"
    probe.write_text('#import "/commands.typ": *\n' + body + '#verify-bending("R", M-y: 5, a: 3000, level: 1)\n', encoding="utf-8")
    run = subprocess.run(["typst", "compile", "--root", str(TYPST_ROOT), str(probe), str(d / "probe.pdf")], capture_output=True, text=True, encoding="utf-8")
    assert run.returncode == 0, run.stderr
    from pypdf import PdfReader
    text = " ".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages)
    assert "Kreisquerschnitt kippt nicht" in text, text


# --- buckling, 4.2.8 --------------------------------------------------------------

def kc(lam_rel, beta_c):
    if lam_rel <= 0.3:
        return 1.0
    k = 0.5 * (1 + beta_c * (lam_rel - 0.3) + lam_rel ** 2)
    return 1 / (k + math.sqrt(k ** 2 - lam_rel ** 2))


def test_buckling_is_the_norm_s_own_formulas():
    """C24 100/200, Feuchteklasse 2, N = 40 kN, l_k = 3 m about both axes: (29) with (30), (31), (34)."""
    body = '#member("S001", level: 0)\n#verify-compression("S001", N: -40, l-k-y: 3000, l-k-z: 3000, level: 0)'
    got = _stored(body, "S001-verify-compression", ("sigma_c_0_d", "lambda_rel_y", "lambda_rel_z", "k_c_y", "k_c_z", "eta_y", "eta_z", "eta"))
    c = char("C24")
    f_c = eta_w(2) * grade("C24")["f_c_0_d"]
    e = eta_w(2, "stiffness") * c["E_0_05"]
    for axis, i in (("y", 200 / math.sqrt(12)), ("z", 100 / math.sqrt(12))):
        lam_rel = 3000 / i / math.pi * math.sqrt(c["f_c_0_k"] / e)
        assert close(got["lambda_rel_" + axis], lam_rel)
        assert close(got["k_c_" + axis], kc(lam_rel, 0.2))
        assert close(got["eta_" + axis], 2.0 / (kc(lam_rel, 0.2) * f_c))
    assert close(got["eta"], max(got["eta_y"], got["eta_z"], 2.0 / f_c))


def test_a_short_member_takes_k_c_of_one_and_beta_times_l():
    """lambda_rel <= 0.3 takes k_c = 1 (Figur 10); l with beta gives l_k = beta · l."""
    body = '#member("S001", level: 0)\n#verify-compression("S001", N: -40, l: 400, beta-y: 0.5, beta-z: 1, level: 0)'
    got = _stored(body, "S001-verify-compression", ("l_k_y", "l_k_z", "k_c_y", "k_c_z"))
    assert close(got["l_k_y"], 200) and close(got["l_k_z"], 400)
    assert got["k_c_y"] == 1                                     # lambda_rel,y well under 0.3
    assert got["k_c_z"] < 1 or close(got["k_c_z"], 1)


def test_glulam_buckles_with_its_own_beta_c():
    body = '#member("G", b: 140, h: 140, grade: "GL24h", moisture-class: 1, level: 0)\n#verify-compression("G", N: -60, l-k-y: 3200, l-k-z: 3200, level: 0)'
    got = _stored(body, "G-verify-compression", ("beta_c", "k_c_z", "lambda_rel_z"))
    assert got["beta_c"] == sia265.buckling()["beta_c"]["Brettschichtholz"]
    assert close(got["k_c_z"], kc(got["lambda_rel_z"], got["beta_c"]))


# --- lateral torsional buckling, 4.2.9 ---------------------------------------------

def km(lam):
    if lam <= 0.75:
        return 1.0
    if lam <= 1.4:
        return 1.56 - 0.75 * lam
    return 1 / lam ** 2


def test_lateral_buckling_takes_each_branch_of_39():
    """GL24h 100/400, Feuchteklasse 1: a = 6 m gives the middle branch, 1.5 m the first, 30 m the last."""
    c = char("GL24h")
    for a in (1500, 6000, 30000):
        body = f'#member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: 0)\n#verify-bending("P", M-y: 10, a: {a}, level: 0)'
        got = _stored(body, "P-verify-bending", ("sigma_m_crit", "lambda_rel_m", "k_m", "eta_m"))
        crit = 0.75 * c["E_0_05"] * 100 ** 2 / (a * 400)
        assert close(got["sigma_m_crit"], crit)
        assert close(got["lambda_rel_m"], math.sqrt(grade("GL24h")["f_m_k"] / crit))
        assert close(got["k_m"], km(got["lambda_rel_m"])), f"a = {a}: k_m {got['k_m']}"


def test_a_critical_stress_given_replaces_41():
    body = '#member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: 0)\n#verify-bending("P", M-y: 10, sigma-m-crit: 40, level: 0)'
    got = _stored(body, "P-verify-bending", ("sigma_m_crit", "lambda_rel_m"))
    assert close(got["sigma_m_crit"], 40) and close(got["lambda_rel_m"], math.sqrt(24 / 40))


def test_without_a_the_stability_is_said_not_checked():
    """No distance between lateral supports: the report says so, and eta is the section's alone."""
    body = '#member("S001", level: 0)\n#verify-bending("S001", M-y: 3, level: 1)'
    kind, _ = _run(body + "\n#metadata(none) <out>")
    assert kind == "ok"
    got = _stored('#member("S001", level: 0)\n#verify-bending("S001", M-y: 3, level: 0)', "S001-verify-bending", ("eta", "eta_s"))
    assert got["eta"] == got["eta_s"]


# --- interactions ------------------------------------------------------------------

def test_biaxial_bending_is_14():
    body = '#member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: 0)\n#verify-bending("P", M-y: 30, M-z: 1.2, level: 0)'
    got = _stored(body, "P-verify-bending", ("eta_s", "f_m_y_d", "f_m_z_d"))
    s_y = 30e6 / (100 * 400 ** 2 / 6)
    s_z = 1.2e6 / (400 * 100 ** 2 / 6)
    assert close(got["eta_s"], s_y / got["f_m_y_d"] + s_z / got["f_m_z_d"])


def test_bending_with_compression_is_22_and_37():
    body = '#member("S001", level: 0)\n#verify-bending-normal("S001", N: -40, M-y: 5, l-k-y: 3000, l-k-z: 3000, a: 3000, level: 0)'
    got = _stored(body, "S001-verify-bending-normal", ("eta_s", "eta_y", "eta_z", "k_c_y", "k_c_z", "k_m"))
    f_c = eta_w(2) * grade("C24")["f_c_0_d"]
    f_m = eta_w(2) * grade("C24")["f_m_d"]
    s_c, s_m = 40e3 / 20000, 5e6 / (100 * 200 ** 2 / 6)
    assert close(got["eta_s"], (s_c / f_c) ** 2 + s_m / f_m)
    assert close(got["eta_y"], s_c / (got["k_c_y"] * f_c) + s_m / (got["k_m"] * f_m))
    assert close(got["eta_z"], s_c / (got["k_c_z"] * f_c))       # no M_z: the bending term of (37) about z is left out


def test_bending_with_tension_is_21():
    body = '#member("Z", b: 120, h: 240, grade: "C24", moisture-class: 1, level: 0)\n#verify-bending-normal("Z", N: 35, M-y: 6, level: 0)'
    got = _stored(body, "Z-verify-bending-normal", ("eta_s",))
    g = grade("C24")
    assert close(got["eta_s"], 35e3 / (120 * 240) / g["f_t_0_d"] + 6e6 / (120 * 240 ** 2 / 6) / g["f_m_d"])


# --- at an angle to the grain --------------------------------------------------------

def test_tension_at_an_angle_is_9():
    body = '#member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: 0)\n#verify-tension("P", N: 40, alpha: 30, level: 0)'
    got = _stored(body, "P-verify-tension", ("f_t_alpha_d", "eta"))
    g = grade("GL24h")
    s, c2 = math.sin(math.radians(30)) ** 2, math.cos(math.radians(30)) ** 2
    f = g["f_t_90_d"] * g["f_t_0_d"] / (g["f_t_0_d"] * s + g["f_t_90_d"] * c2)
    assert close(got["f_t_alpha_d"], f) and close(got["eta"], 40e3 / 40000 / f)


def test_compression_across_the_grain_is_11_and_13():
    got = _stored('#member("S001", level: 0)\n#verify-compression-perp("S001", F: 18, l: 120, level: 0)', "S001-verify-compression-perp", ("eta", "f_c_90_d"))
    f90 = eta_w(2) * grade("C24")["f_c_90_d"]["generell"]
    assert close(got["f_c_90_d"], f90) and close(got["eta"], 18e3 / (120 * 100) / f90)
    body = '#member("P", b: 160, h: 400, grade: "GL24h", moisture-class: 1, level: 0)\n#verify-compression-perp("P", F: 45, l: 150, case: "endauflagerung", larger: true, alpha: 60, level: 0)'
    got = _stored(body, "P-verify-compression-perp", ("f_c_90_d", "f_c_alpha_d"))
    g = grade("GL24h")
    f90 = g["f_c_90_d"]["endauflagerung"]["groessere_eindrueckungen"]
    s, c2 = math.sin(math.radians(60)) ** 2, math.cos(math.radians(60)) ** 2
    assert close(got["f_c_90_d"], f90)
    assert close(got["f_c_alpha_d"], f90 * g["f_c_0_d"] / (g["f_c_0_d"] * s + f90 * c2))


def test_bending_at_an_angle_is_19_and_20():
    body = '#member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: 0)\n#verify-bending("P", M-y: 20, alpha: 10, level: 0)'
    got = _stored(body, "P-verify-bending", ("k_mc_alpha", "k_mt_alpha", "f_m_y_d"))
    g = grade("GL24h")
    s, c2 = math.sin(math.radians(10)) ** 2, math.cos(math.radians(10)) ** 2
    f_m = got["f_m_y_d"]
    assert close(got["k_mc_alpha"], g["f_c_90_d"]["generell"] / (f_m * s + g["f_c_90_d"]["generell"] * c2))
    assert close(got["k_mt_alpha"], g["f_t_90_d"] / (f_m * s + g["f_t_90_d"] * c2))


def _page_text(body, name):
    """The text of the page `body` prints, through a PDF -- what a check says in words."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/commands.typ": *\n' + body + "\n", encoding="utf-8")
    run = subprocess.run(["typst", "compile", "--root", str(TYPST_ROOT), str(probe), str(d / "probe.pdf")], capture_output=True, text=True, encoding="utf-8")
    assert run.returncode == 0, run.stderr
    from pypdf import PdfReader
    return " ".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages)


def test_stability_false_checks_the_section_alone():
    """`stability: false` (v0.117, the module «Flexion»): verify-bending and verify-bending-normal check the section alone -- no k_m, no buckling length read, no «Stabilität» part nor the note that lateral torsional buckling is not checked; eta is the section's. A non-bool and an input of lateral torsional buckling beside it are refused."""
    body = '#member("S001", level: 0)\n'
    got = _stored(body + '#verify-bending("S001", M-y: 3, stability: false, level: 0)', "S001-verify-bending", ("eta", "eta_s"))
    assert got["eta"] == got["eta_s"]
    kind, keys = _run(body + '#verify-bending-normal("S001", N: -40, M-y: 5, stability: false, level: 0)\n#context [#metadata(var-registry.get().domains.at("S001-verify-bending-normal").keys()) <out>]')
    assert kind == "ok" and "k_c_y" not in keys and "k_m" not in keys, keys
    got = _stored(body + '#verify-bending-normal("S001", N: -40, M-y: 5, stability: false, level: 0)', "S001-verify-bending-normal", ("eta", "eta_s"))
    f_c = eta_w(2) * grade("C24")["f_c_0_d"]
    f_m = eta_w(2) * grade("C24")["f_m_d"]
    assert close(got["eta_s"], (40e3 / 20000 / f_c) ** 2 + 5e6 / (100 * 200 ** 2 / 6) / f_m) and got["eta"] == got["eta_s"]
    for check in ('verify-bending("S001", M-y: 3', 'verify-bending-normal("S001", N: 20, M-y: 3'):
        assert "stability is true or false" in _error(body + "#" + check + ', stability: "no", level: 0)')
        assert "a: is an input of lateral torsional buckling" in _error(body + "#" + check + ", a: 3000, stability: false, level: 0)")
        assert "sigma-m-crit: is an input" in _error(body + "#" + check + ", sigma-m-crit: 40, stability: false, level: 0)")
    text = _page_text(body + '#verify-bending("S001", M-y: 3, stability: false, level: 2)\n#verify-bending-normal("S001", N: -40, M-y: 5, stability: false, level: 2)', "timber_stability_false")
    assert "Stabilität" not in text and "Kippen" not in text, text


def test_bending_with_a_normal_force_at_an_angle():
    """(21) and (22) at an angle to the grain (the engineer's reading, 08.10.2026): f_t,α,d of (9) or f_c,α,d of (13) with f_c,90,d generell, k_mt,α or k_mc,α of (19), (20) on the side where N adds, the other side by (17) or (18) alone; eta the larger. The page says the norm does not write it. M-z, the stability and an angle outside 0..90 are refused."""
    body = '#member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: 0)\n'
    g = grade("GL24h")
    s, c2 = math.sin(math.radians(30)) ** 2, math.cos(math.radians(30)) ** 2
    W = 100 * 400 ** 2 / 6
    A = 100 * 400
    for N in (40, -40):
        got = _stored(body + f'#verify-bending-normal("P", N: {N}, M-y: 20, alpha: 30, stability: false, level: 0)', "P-verify-bending-normal",
                      ("eta", "eta_m_t", "eta_m_c", "k_mt_alpha", "k_mc_alpha", "f_m_y_d"))
        f_m = got["f_m_y_d"]
        f90c = g["f_c_90_d"]["generell"]
        k_mc = f90c / (f_m * s + f90c * c2)
        k_mt = g["f_t_90_d"] / (f_m * s + g["f_t_90_d"] * c2)
        assert close(got["k_mc_alpha"], k_mc) and close(got["k_mt_alpha"], k_mt)
        s_m, s_n = 20e6 / W, 40e3 / A
        if N > 0:
            f_t = g["f_t_90_d"] * g["f_t_0_d"] / (g["f_t_0_d"] * s + g["f_t_90_d"] * c2)
            assert close(got["eta_m_t"], s_n / f_t + s_m / (k_mt * f_m))
            assert close(got["eta_m_c"], s_m / (k_mc * f_m))
        else:
            f_c = f90c * g["f_c_0_d"] / (g["f_c_0_d"] * s + f90c * c2)
            assert close(got["eta_m_c"], (s_n / f_c) ** 2 + s_m / (k_mc * f_m))
            assert close(got["eta_m_t"], s_m / (k_mt * f_m))
        assert close(got["eta"], max(got["eta_m_t"], got["eta_m_c"]))
    assert "reads M-y alone" in _error(body + '#verify-bending-normal("P", N: 40, M-y: 20, M-z: 1, alpha: 30, stability: false, level: 0)')
    assert "give stability: false" in _error(body + '#verify-bending-normal("P", N: 40, M-y: 20, alpha: 30, level: 0)')
    assert "0 to 90" in _error(body + '#verify-bending-normal("P", N: 40, M-y: 20, alpha: 95, stability: false, level: 0)')
    text = _page_text(body + '#verify-bending-normal("P", N: -40, M-y: 20, alpha: 30, stability: false, level: 2)', "timber_bending_normal_angle")
    assert "nur in Faserrichtung" in text, text


# --- shear ---------------------------------------------------------------------------

def torsion_k(r):
    """Saint-Venant's k with tau_max = T / (k · a · c²), from its series -- written again here, independently of lib/timber.typ."""
    s1 = sum(math.tanh(n * math.pi * r / 2) / n ** 5 for n in range(1, 60, 2))
    s2 = sum(1 / (n * n * math.cosh(n * math.pi * r / 2)) for n in range(1, 60, 2) if n * math.pi * r / 2 < 700)
    k1 = (1 - 192 / (math.pi ** 5 * r) * s1) / 3
    return k1 / (1 - 8 / math.pi ** 2 * s2)


def test_saint_venant_s_classic_values():
    """0.208 for a square, 0.246 at 2, 0.267 at 3, 0.291 at 5 (Timoshenko & Goodier's table), and what the book prints at 2.75."""
    for ratio, want in ((1, 0.208), (2, 0.246), (3, 0.267), (5, 0.291)):
        assert abs(torsion_k(ratio) - want) < 0.0015, (ratio, torsion_k(ratio))
    got = _stored('#member("X", b: 160, h: 440, grade: "GL24h", moisture-class: 1, level: 0)', "X", ("k_tor", "W_t"))
    assert close(got["k_tor"], torsion_k(440 / 160), rel=1e-9)
    assert abs(got["W_t"] - 2.95e6) < 0.006 * 2.95e6      # Bemessungsbeispiele zur SIA 265, p. 114


def test_shear_and_torsion_are_23_and_25():
    body = '#member("R", b: 120, h: 240, grade: "C24", moisture-class: 1, level: 0)\n#verify-shear("R", V: 15, V-y: 3, T: 0.6, level: 0)'
    got = _stored(body, "R-verify-shear", ("tau_d", "tau_tor_d", "eta"))
    fv = grade("C24")["f_v_d"]
    tz, ty = 1.5 * 15e3 / (120 * 240), 1.5 * 3e3 / (120 * 240)
    wt = torsion_k(240 / 120) * 240 * 120 ** 2
    assert close(got["tau_d"], math.hypot(tz, ty)) and close(got["tau_tor_d"], 0.6e6 / wt)
    assert close(got["eta"], got["tau_tor_d"] / fv + (got["tau_d"] / fv) ** 2)


def test_a_pith_member_halves_f_v():
    got = _stored('#member("S001", level: 0)\n#verify-shear("S001", V: 12, pith: true, level: 0)', "S001-verify-shear", ("eta",))
    assert close(got["eta"], 1.5 * 12e3 / 20000 / (eta_w(2) * grade("C24")["f_v_d"] / 2))


def test_abscheren_is_26_or_27_and_needs_150_mm():
    got = _stored('#member("S001", level: 0)\n#verify-shear-off("S001", F: 20, l: 200, level: 0)', "S001-verify-shear-off", ("eta",))
    assert close(got["eta"], 20e3 / (200 * 100) / (0.6 * eta_w(2) * grade("C24")["f_v_d"]))
    glulam = _stored('#member("G", b: 160, h: 320, grade: "GL24h", moisture-class: 1, level: 0)\n#verify-shear-off("G", F: 45, l: 250, w: 120, level: 0)', "G-verify-shear-off", ("eta",))
    assert close(glulam["eta"], 45e3 / (250 * 120) / (0.8 * grade("GL24h")["f_v_d"]))


def test_shear_with_a_stress_across_the_grain_is_28():
    c = sia265.shear_transverse()
    for s90, k in ((-1.2, c["k_t_90"]["querdruck"]), (0.05, c["k_t_90"]["querzug"])):
        body = f'#member("R", b: 120, h: 240, grade: "C24", moisture-class: 1, level: 0)\n#verify-shear-perp("R", tau: "0.9 N/mm²", sigma-90: {s90}, level: 0)'
        got = _stored(body, "R-verify-shear-perp", ("eta", "k_t_90"))
        g = grade("C24")
        fc, ft, fv = g["f_c_90_d"]["generell"], g["f_t_90_d"], g["f_v_d"]
        r = fc / (fc + k * ft)
        want = ((fc + s90) / (fc + k * ft)) ** 2 + (0.9 / fv) ** 2 * (1 - r ** 2)
        assert got["k_t_90"] == k and close(got["eta"], want)


# --- refusals and publication --------------------------------------------------------

def test_the_sign_of_n_chooses_and_refuses():
    assert "compression" in _error('#member("S001", level: 0)\n#verify-tension("S001", N: -5)')
    assert "tension" in _error('#member("S001", level: 0)\n#verify-compression("S001", N: 5, l-k-y: 1000, l-k-z: 1000)')
    assert "buckling lengths" in _error('#member("S001", level: 0)\n#verify-compression("S001", N: -5)')
    assert "no member" in _error('#verify-shear("S001", V: 3)')
    assert "Zugglieder" in _error('#member("X", b: 100, h: 200, grade: "C16", moisture-class: 1, level: 0)\n#verify-tension("X", N: 5)')


def test_a_force_is_a_number_a_value_with_its_unit_a_name_or_a_var():
    base = '#member("S001", level: 0)\n'
    for n in ("-40", '"-40 kN"', '"N_d"', 'var-of("snow-load", "SL", "s_k")'):
        pre = '#var("N_d", -40, "kN", level: 0)\n' if n == '"N_d"' else ""
        if n.startswith("var-of"):
            continue    # a load is no force; the var object form is held by test_a_var_object_is_taken_as_it_is
        got = _stored(pre + base + f'#verify-compression("S001", N: {n}, l-k-y: 3000, l-k-z: 3000, level: 0)', "S001-verify-compression", ("N_c_d",))
        assert close(got["N_c_d"], 40), n
    assert "not declared" in _error(base + '#verify-compression("S001", N: "N_nowhere", l-k-y: 3000, l-k-z: 3000)')


def test_the_results_are_published_under_member_verify_check():
    body = ('#member("S001", level: 0)\n#verify-compression("S001", N: -40, l-k-y: 3000, l-k-z: 3000, level: 0)\n'
            '#verify-compression("S001", N: -20, l-k-y: 3000, l-k-z: 3000, level: 0, name: "S001-light")\n'
            '#var("eta", domain: "S001-verify-compression", level: 0)')
    got = _stored(body, "S001-light", ("eta",))
    heavy = _stored(body, "S001-verify-compression", ("eta",))
    assert close(heavy["eta"], 2 * got["eta"], rel=1e-6)


def test_a_utilisation_in_percent():
    kind, got = _run('#member("S001", level: 0)\n#verify-shear("S001", V: 12, unit: "%", level: 0)\n'
                     '#context [#metadata(var-registry.get().domains.at("S001-verify-shear").at("eta")) <out>]')
    assert kind == "ok" and got["unit"] == "%" and close(got["value"], 75.0)


def test_every_level_compiles():
    body = ('#member("S001", level: {L})\n#member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: {L})\n'
            '#verify-tension("P", N: 40, alpha: 30, level: {L})\n#verify-compression("S001", N: -40, l: 3000, level: {L})\n'
            '#verify-compression-perp("S001", F: 18, l: 120, level: {L})\n#verify-bending("P", M-y: 30, M-z: 1.2, a: 6000, level: {L})\n'
            '#verify-bending("P", M-y: 2, alpha: 90, level: {L})\n#verify-bending-normal("S001", N: -40, M-y: 5, l: 3000, a: 3000, level: {L})\n'
            '#verify-bending-normal("P", N: 35, M-y: 6, a: 4000, unit: "%", level: {L})\n#verify-shear("P", V: 15, T: 0.6, level: {L})\n'
            '#verify-shear-off("S001", F: 20, l: 120, level: {L})\n#verify-shear-perp("S001", V: 12, sigma-90: -1.2, level: {L})')
    for level in (0, 1, 2, 3):
        kind, got = _run(body.replace("{L}", str(level)) + "\n#metadata(none) <out>")
        assert kind == "ok", f"level {level}: {got}"


# --- published worked examples ---------------------------------------------------------

ORACLES = ROOT / "tests" / "fixtures" / "timber-oracles.json"


def test_the_worked_examples():
    """Every case of tests/fixtures/timber-oracles.json that a check can run, to the digits its source prints."""
    if not ORACLES.is_file():
        raise Skip("no tests/fixtures/timber-oracles.json")
    cases = json.loads(ORACLES.read_text(encoding="utf-8")).get("cases", [])
    ran = 0
    failures = []
    for case in cases:
        call = case.get("typst")
        if not call:
            continue
        got = _stored(call["body"], call["domain"], tuple(call["expected"]))
        for key, want in call["expected"].items():
            tol = call.get("tolerance", 0.005)
            if abs(got[key] - want) > tol * max(1.0, abs(want)):
                failures.append(f"{case['id']} {key}: {got[key]} against {want} ({case['source']})")
        ran += 1
    if ran == 0:
        raise Skip("no oracle carries a typst call yet")
    assert not failures, "\n  ".join(failures)


def test_the_buckling_tables_of_the_holzbautabellen():
    """Lignum HBT 1, p. 53 (C24) and p. 58 (GL24h): k_c · f_c,0,d against lambda_rel -- k_c of (30), (31) alone, whatever finds lambda_rel -- each row reached with the length that gives its lambda_rel exactly."""
    if not ORACLES.is_file():
        raise Skip("no tests/fixtures/timber-oracles.json")
    cases = [c for c in json.loads(ORACLES.read_text(encoding="utf-8"))["cases"] if "typst_table" in c]
    assert cases, "no HBT table in the oracles"
    failures = []
    for case in cases:
        t = case["typst_table"]
        for row in t["rows"]:
            body = t["member"] + f'#verify-compression("X", N: -10, l-k-y: {row["l_k_mm"]}, l-k-z: {row["l_k_mm"]}, level: 0)'
            got = _stored(body, "X-verify-compression", ("lambda_rel_z", "k_c_z", "f_c_0_d"))
            value = got["k_c_z"] * got["f_c_0_d"]
            if abs(got["lambda_rel_z"] - row["lambda_rel"]) > 1e-6 or abs(value - row["k_c_f_c_0_d"]) > t["tolerance"] * row["k_c_f_c_0_d"]:
                failures.append(f"{case['id']} lambda_rel {row['lambda_rel']}: {value:.4f} against {row['k_c_f_c_0_d']}")
    assert not failures, "\n  ".join(failures)


# --- the level of detail -1: the variables chosen one by one (issue #20, v0.117) ---------------------------------------

def _shown(keys, level=3):
    return "(" + ", ".join(f"{k}: {level}" for k in keys) + ")" if keys else "(:)"


MINUS_ONE_CALLS = {
    "member": '#member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: -1, shown: {S})',
    "verify-tension": '#verify-tension("P", N: 40, alpha: 30, level: -1, shown: {S})',
    "verify-compression": '#verify-compression("S001", N: -40, l: 3000, level: -1, shown: {S})',
    "verify-compression-perp": '#verify-compression-perp("S001", F: 18, l: 120, alpha: 60, level: -1, shown: {S})',
    "verify-bending": '#verify-bending("P", M-y: 30, M-z: 1.2, a: 6000, level: -1, shown: {S})',
    "verify-bending-normal": '#verify-bending-normal("S001", N: -40, M-y: 5, l: 3000, a: 3000, level: -1, shown: {S})',
    "verify-shear": '#verify-shear("P", V: 15, V-y: 4, pith: true, level: -1, shown: {S})',
}
MINUS_ONE_SETUP = '#member("S001", level: 0)\n#member("P", b: 100, h: 400, grade: "GL24h", moisture-class: 1, level: 0)\n'


def test_level_minus_one_compiles_with_none_and_with_every_key_of_each_command():
    """REQ-003, REQ-005: every key lib/shown-variables.json lets a command name compiles at -1 -- a key the call does not print (alpha = 0, a round section) is accepted and ignored -- and so does an empty choice."""
    import shown_variables
    for command, call in MINUS_ONE_CALLS.items():
        for keys in ((), shown_variables.keys(command)):
            body = MINUS_ONE_SETUP + call.replace("{S}", _shown(keys))
            kind, got = _run(body + "\n#metadata(none) <out>")
            assert kind == "ok", f"{command} with {len(keys)} keys: {got}"


def test_level_minus_one_prints_the_title_and_what_is_chosen_alone():
    """REQ-003, REQ-004 (D-09, D-14), issue #58: `shown: (:)` prints the title and the parts and no verdict -- a verdict is a key like any other; a key chosen is printed with the heading over it, a key not chosen is not; every key at 3, the verdicts' included, prints what level 3 prints."""
    base = '#member("S", b: 140, h: 140, grade: "GL24h", moisture-class: 1, level: 0)\n'
    call = '#verify-compression("S", N: -60, l: 3200, beta-z: 0.7, level: {L})'
    three = _page_text(base + call.replace("{L}", "3"), "minus1_three")
    empty = _page_text(base + call.replace("{L}", "-1, shown: (:)"), "minus1_empty")
    assert "Druck parallel" in empty and "Tragsicherheit" in empty and "✔" not in empty and "✘" not in empty, empty
    assert "Knicken um die" not in empty and "𝜆" not in empty and "𝑁𝑐,𝑑 =" not in empty, empty
    one = _page_text(base + call.replace("{L}", "-1, shown: (lambda_y: 2)"), "minus1_one")
    assert "Knicken um die y-Achse" in one and "Knicken um die z-Achse" not in one, one
    assert "𝜆𝑦" in one and "𝜆rel,𝑦" not in one and "𝛽𝑐 =" not in one, one
    import shown_variables
    every = _page_text(base + call.replace("{L}", "-1, shown: " + _shown(shown_variables.keys("verify-compression"))), "minus1_every")
    lines_three, lines_every = set(three.split("\n")), set(every.split("\n"))
    assert all("⩽" in line for line in lines_every - lines_three), sorted(lines_every - lines_three)
    for word in ("Knicken um die y-Achse", "Knicken um die z-Achse", "𝛽𝑐", "𝑘𝑐,𝑧"):
        assert word in every, word


def test_level_minus_one_is_refused_where_it_names_what_the_command_does_not_print():
    """REQ-003: an unknown key is refused naming the keys the command prints; a level outside 1-3 in `shown:`, and `shown:` without -1, are refused."""
    message = _error(MINUS_ONE_SETUP + '#verify-tension("P", N: 40, level: -1, shown: (W_y: 2))')
    assert "W_y" in message and "sigma_t_0_d" in message, message
    message = _error(MINUS_ONE_SETUP + '#verify-tension("P", N: 40, level: -1, shown: (sigma_t_0_d: 4))')
    assert "1, 2 or 3" in message, message
    message = _error(MINUS_ONE_SETUP + '#verify-tension("P", N: 40, level: 2, shown: (sigma_t_0_d: 2))')
    assert "level: -1" in message, message
    message = _error(MINUS_ONE_SETUP + '#verify-shear("P", V: 15, level: -1, shown: (eta: 0))')
    assert "1, 2 or 3" in message and "left out" in message, message   # a verdict at 0 is left out of shown:, as any key (issue #58)


def test_level_minus_one_stores_what_level_three_stores():
    """ARCH-001: -1 changes what is printed and nothing that is stored -- the registry of a check printed with nothing chosen holds the keys and the values level 3 holds."""
    keys = ("sigma_c_0_d", "lambda_rel_y", "k_c_y", "k_c_z", "eta")
    body = '#member("S001", level: 0)\n#verify-compression("S001", N: -40, l: 3000, level: {L})'
    assert _stored(body.replace("{L}", "3"), "S001-verify-compression", keys) == _stored(body.replace("{L}", "-1, shown: (:)"), "S001-verify-compression", keys)


def test_a_uniform_level_is_forced_over_minus_one_and_a_report_level_is_never_minus_one():
    """REQ-006: like 0, -1 is a level of one call: `--input uniform=N` still wins over it, and `report-level` refuses it."""
    body = MINUS_ONE_SETUP + '#uniform-level.update(3)\n#verify-tension("P", N: 40, alpha: 30, level: -1, shown: (:))'
    text = _page_text(body, "minus1_uniform")
    assert "𝑁𝑡,𝑑" in text, text
    message = _error('#report-level.update(-1)\n#member("S001")')
    assert "report level" in message, message


def test_show_check_member_takes_one_list_for_the_member_and_its_check():
    """D-11: show-check-member at -1 takes the member's keys and its check's in one list, a key both print going to the check, and member-level giving way to it."""
    import shown_variables
    keys = shown_variables.check_member_keys(command="verify-compression-perp")
    assert keys.count("f_c_90_d") == 1 and keys.index("f_c_90_d") > keys.index("A")
    member, check = shown_variables.split_check_member({"A": 2, "f_c_90_d": 3, "A_c": 1}, "verify-compression-perp")
    assert member == {"A": 2} and check == {"f_c_90_d": 3, "A_c": 1}


def test_the_keys_level_minus_one_may_name_are_written_once_and_copied_with_the_engine():
    """ARCH-007 (issue #20): lib/shown-variables.json is read by Typst -- `json("shown-variables.json")` in calc-engine.typ, no key list written there -- and by calc/shown_variables.py, and it travels with the engine (project.ENGINE_FILES) into the project the tests compile, where it is the program's own file."""
    import shown_variables
    source = (ROOT / "lib" / "calc-engine.typ").read_text(encoding="utf-8")
    assert 'json("shown-variables.json")' in source
    assert "lib/shown-variables.json" in project.ENGINE_FILES
    copied = conftest.PROJECT.generated_dir / "lib" / "shown-variables.json"
    assert copied.is_file() and copied.read_bytes() == (ROOT / "lib" / "shown-variables.json").read_bytes()
    assert set(shown_variables.commands()) == {"member", "verify-tension", "verify-compression", "verify-compression-perp", "verify-bending", "verify-bending-normal", "verify-shear", "show-polar-moment"}
    for command in shown_variables.commands():
        keys = shown_variables.keys(command)
        assert len(keys) == len(set(keys)), command
        assert all(set(names) <= set(keys) for names in shown_variables.parts(command).values()), command
        assert "results" not in shown_variables._commands()[command], command   # issue #58 retired them


# the verdicts each check prints, by the key of its utilisation, for MINUS_ONE_CALLS (issue #58)
MINUS_ONE_VERDICTS = {
    "verify-tension": ("eta",),
    "verify-compression": ("eta_s", "eta_y", "eta_z"),
    "verify-compression-perp": ("eta",),
    "verify-bending": ("eta_s", "eta_m"),
    "verify-bending-normal": ("eta_s", "eta_y", "eta_z"),
    "verify-shear": ("eta",),
}


def test_a_verdict_is_a_key_printed_at_its_own_level_and_left_out_where_not_named():
    """REQ-001, REQ-002, REQ-003 (issue #58, D-01, D-02, D-03): at -1 a check's verdict is named by the key of its utilisation; left out of `shown:` it is not printed, at 1 it is the brief verdict, at 2 and 3 the full one; each verify-* command lists its verdicts' keys; a stress is an ordinary key, not printed where it is not named and given 1 to 3 like any other."""
    import shown_variables
    for command, verdicts in MINUS_ONE_VERDICTS.items():
        assert set(verdicts) <= set(shown_variables.keys(command)), command
        call = MINUS_ONE_SETUP + MINUS_ONE_CALLS[command]
        none = _page_text(call.replace("{S}", "(:)"), "minus1_verdict_none_" + command)
        assert "✔" not in none and "✘" not in none, (command, none)
        one = _page_text(call.replace("{S}", _shown(verdicts, 1)), "minus1_verdict_one_" + command)
        assert one.count("✔") + one.count("✘") == len(verdicts), (command, one)
        assert "N/mm²" not in one, (command, one)   # brief: the ratio's symbols and its value, no numbers
        full = _page_text(call.replace("{S}", _shown(verdicts, 3)), "minus1_verdict_full_" + command)
        assert full.count("✔") + full.count("✘") == len(verdicts) and "N/mm²" in full, (command, full)
        assert _page_text(call.replace("{S}", _shown(verdicts, 2)), "minus1_verdict_two_" + command) == full, command
    alone = _page_text(MINUS_ONE_SETUP + MINUS_ONE_CALLS["verify-compression"].replace("{S}", "(eta_y: 1)"), "minus1_verdict_alone")
    assert alone.count("✔") + alone.count("✘") == 1 and "Knicken um die y-Achse" in alone and "Knicken um die z-Achse" not in alone, alone
    message = _error(MINUS_ONE_SETUP + '#verify-tension("P", N: 40, level: -1, shown: (eta_q: 1))')
    assert "eta_q" in message and "eta" in message, message
    empty = _page_text(MINUS_ONE_SETUP + '#verify-tension("P", N: 40, level: -1, shown: (:))', "minus1_stress_none")
    assert "𝜎𝑡,0,𝑑" not in empty, empty
    chosen = _page_text(MINUS_ONE_SETUP + '#verify-tension("P", N: 40, level: -1, shown: (sigma_t_0_d: 2))', "minus1_stress_two")
    assert "𝜎𝑡,0,𝑑" in chosen and "✔" not in chosen and "✘" not in chosen, chosen


def test_the_sides_of_a_bending_at_an_angle_head_their_verdict_from_level_two():
    """REQ-002 (ARCH-RISK-003): at -1 «Biegezugseite» and «Biegedruckseite» stand over their verdict where it is given 2 or 3, as at level 2, and not at 1."""
    call = MINUS_ONE_SETUP + '#verify-bending("P", M-y: 3, alpha: 90, level: -1, shown: {S})'
    one = _page_text(call.replace("{S}", "(eta_m_t: 1, eta_m_c: 1)"), "minus1_sides_one")
    assert "Biegezugseite" not in one and "Biegedruckseite" not in one and one.count("✔") + one.count("✘") == 2, one
    two = _page_text(call.replace("{S}", "(eta_m_t: 2)"), "minus1_sides_two")
    assert "Biegezugseite" in two and "Biegedruckseite" not in two and two.count("✔") + two.count("✘") == 1, two
    level_two = _page_text(MINUS_ONE_SETUP + '#verify-bending("P", M-y: 3, alpha: 90, level: 2)', "level2_sides")
    assert "Biegezugseite" in level_two and "Biegedruckseite" in level_two, level_two

