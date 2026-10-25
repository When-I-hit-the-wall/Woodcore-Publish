"""What a calculation tab lights up together (calc/domains/dependencies.py; spec 2026-10-23-neige-correctifs-issues-96-99, UI-004, ARCH-001): the values a result is computed from and the results a value goes into, read off an instance's steps and the dependencies its domain adds -- the snow's μ, which no step records.

Held here: the graph of steps and extras, both directions, near and far; the snow's case of a duo-pitch roof and of a flat one, each value going where SIA 261 sends it; every field of the snow's form naming a variable its instance holds.
"""

TIER = "fast"  # tests/run_tests.py --fast

from domains import dependencies, snow_source


def test_upstream_and_downstream_follow_the_steps_near_and_far():
    instance = {"steps": [{"result": "b", "uses": ["a"]}, {"result": "c", "uses": ["b", "x"]}]}
    edges = dependencies.graph(instance, {"x": ["y"]})
    assert dependencies.upstream("c", edges) == {"a", "b", "x", "y"}
    assert dependencies.downstream("a", edges) == {"b", "c"} and dependencies.downstream("y", edges) == {"x", "c"}
    assert dependencies.upstream("a", edges) == set() and dependencies.downstream("c", edges) == set()
    assert dependencies.graph(None) == {} and dependencies.upstream("z", {}) == set()


def _edges(**change):
    src = snow_source.new_source("SN-01")
    src.update(change)
    instance = snow_source.build_instance(src)
    return dependencies.graph(instance, snow_source.extra_dependencies(instance)), instance


def test_the_snow_sends_each_value_where_sia_261_does():
    """UI-004: on a duo-pitch roof q_k,11 is computed from h₀, Δh, C_e, C_T, α₁ and the sliding -- through h_ref, s_k and μ₁₁ --, never from α₂; h₀ goes into h_ref, s_k and every q_k; α₂ into μ₁₂ and its loads alone. A flat roof's μ₁ is read off its plan."""
    edges, _ = _edges()
    assert dependencies.upstream("q_k11", edges) >= {"h_0", "korrektur", "h_ref", "s_k", "ce", "ct", "mu_11", "alpha_1", "abgleiten", "dachform"}
    assert "alpha_2" not in dependencies.upstream("q_k11", edges)
    assert dependencies.downstream("h_0", edges) == {"h_ref", "s_k", "q_k11", "q_k12", "q_k11h", "q_k12h"}
    assert dependencies.downstream("alpha_2", edges) == {"mu_12", "q_k12", "q_k12h"}
    flat, _ = _edges(roof="flat", length=12.0, width=8.0)
    assert {"L", "B"} <= dependencies.upstream("q_k1", flat) and "alpha_1" not in dependencies.upstream("q_k1", flat)


def test_every_field_of_the_snow_names_a_variable_its_instance_holds():
    """ARCH-001: the link from a field to its variable is the declaration's -- each field names one, held by an instance of a roof that shows the field."""
    held = set()
    for roof in snow_source.ROOFS:
        held |= set(_edges(roof=roof, length=12.0, width=8.0, height_step=True)[1]["vars"])
    for field in snow_source.declaration().fields:
        assert field.var and field.var in held, (field.key, field.var)
