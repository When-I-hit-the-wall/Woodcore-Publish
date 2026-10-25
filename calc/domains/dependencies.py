"""What a calculation tab lights up together (spec 2026-10-23-neige-correctifs-issues-96-99, UI-004, ARCH-001): the values a result is computed from, and the results a value goes into -- a pure function of an instance, without Qt, so that the tab draws it and computes nothing.

An instance's `steps` say it already (`uses` -> `result`, engine.Calculation); a domain adds what no step records -- the snow's μ, read off Figur 2 by a slope and the sliding -- with `extra_dependencies(instance)`, {result: [names]}, never new steps, which would change the export and the form of every case's file. The link from a field of the form to the variable it fills is the declaration's (`contracts.Field.var`).
"""


def graph(instance, extra=None):
    """{name: set of the names it is computed from} -- the steps' `uses`, then `extra`'s."""
    out = {}
    for step in (instance or {}).get("steps") or ():
        result = step.get("result")
        if result:
            out.setdefault(result, set()).update(step.get("uses") or ())
    for result, uses in (extra or {}).items():
        out.setdefault(result, set()).update(uses)
    return out


def upstream(name, edges):
    """Every name `name` is computed from, near or far -- not `name` itself."""
    seen, todo = set(), [name]
    while todo:
        for used in edges.get(todo.pop(), ()):
            if used not in seen and used != name:
                seen.add(used)
                todo.append(used)
    return seen


def downstream(name, edges):
    """Every name computed from `name`, near or far -- not `name` itself."""
    users = {}
    for result, uses in edges.items():
        for used in uses:
            users.setdefault(used, set()).add(result)
    return upstream(name, users)
