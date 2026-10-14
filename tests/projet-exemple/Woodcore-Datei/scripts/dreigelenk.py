# @name Dreigelenkrahmen
# @label Horizontalkraft im Dreigelenkrahmen
# @group Halle
"""What this script works out: the horizontal reaction of a three-hinged frame under a uniform roof load.

What it is given, and nothing else:
    result(name, value, unit="", symbol=None, label=None, descr=None, norm=None, norm_ref="")
        declares a value the report reads with #val(name, domain: ("script", "dreigelenk"))
    value(domain, instance, name)
        a number out of the export: value("snow-load", "SL", "q_k11")
    PROJECT, DATA
        the project's folder and its export, as pathlib.Path -- to read, not to write

Written in the standard library alone, so it runs wherever the suite does; numpy is pinned and
available for a system of equations that wants it (docs/domain/scripts.md §3.3sexdecies).
"""

q = 3.2      # kN/m, the roof load on the frame
span = 12.0  # m
height = 4.0  # m to the hinge

# a three-hinged frame, uniform load on both rafters: H = q L^2 / (8 f)
H = q * span ** 2 / (8 * height)
V = q * span / 2

result("H_d", H, "kN", symbol='H_"d"', label="Horizontalkraft am Fusspunkt",
       descr="Dreigelenkrahmen unter Gleichlast, H = q L² / (8 f)")
result("V_d", V, "kN", symbol='V_"d"', label="Vertikalkraft am Fusspunkt")
