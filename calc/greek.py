"""The Greek names Typst's math knows, and the letter each is set as -- one list for the window and the domain modules (spec 2026-10-08-onglet-formule-domaines, revue ARCH-RISK-107).

It is lib/formula.typ's `greek-names`, which decides how a registry key is printed (`key-symbol`: a multi-letter subscript that is not a Greek name is quoted), and `tests/test_units.py` holds the two equal. Until 0.117 the window kept a shorter list of its own in calc/tools/richtext.py, a module that imports Qt and that calc/domains/ therefore cannot read: zeta, iota, kappa, upsilon and Gamma, Theta, Lambda, Xi, Pi, Upsilon, Psi were set as words in the window and as letters on the page. richtext reads this one now. No Qt here.
"""

# name -> letter, in formula.typ's own order: the small letters, then the capitals Typst's math names
LETTERS = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "iota": "ι",
    "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ",
    "phi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ", "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}
NAMES = tuple(LETTERS)
# a letter typed as itself -> the name a key is written with (σ → sigma); the final sigma and the other forms of a letter are read as it
BY_LETTER = {letter: name for name, letter in LETTERS.items()}
BY_LETTER.update({"ς": "sigma", "ϕ": "phi", "ϑ": "theta", "ϵ": "epsilon", "µ": "mu"})
