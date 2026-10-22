#import "/000-Typst-Config/commands.typ": *

#domain("ST-01", label: "Stahl: Biegung – ST-01")[
#calc-defaults(presets: "block", scope: "domain") <ST-01-presets>
*IPE 360, S355* <ST-01-member>

  #var("f_y", 355, "N/mm²", domain: ("steel", "ST-01"), label: "Streckgrenze", descr: "S355, t ≤ 40 mm", norm: "SIA 263", norm-section: "Tabelle 1", id: "f_y")
  #var("gamma_M1", "gamma_(M 1)", 1.05, domain: ("steel", "ST-01"), label: "Widerstandsbeiwert", norm: "SIA 263", norm-section: "4.1.3", id: "gamma_M1")
  #var("N_Ed", "N_(E d)", -300, "kN", domain: ("steel", "ST-01"), label: "Normalkraft", norm: "SIA 263", norm-section: "5.1.6.4 (48)", id: "N_Ed")
  #var("M_y_Ed", "M_(y,E d)", 150, "kNm", domain: ("steel", "ST-01"), label: "Biegemoment", norm: "SIA 263", norm-section: "5.1.6.4 (48)", id: "M_y_Ed")
  #var("M_z_Ed", "M_(z,E d)", 10, "kNm", domain: ("steel", "ST-01"), label: "Biegemoment", norm: "SIA 263", norm-section: "5.1.6.4 (48)", id: "M_z_Ed")
  #var("QK", "\"QK\"", 1, domain: ("steel", "ST-01"), label: "Querschnittsklasse", descr: "Steg: c/t = 37.2 (Klasse 1: 40.7, 2: 46.8, 3: 69.4)", norm: "SIA 263", norm-section: "Tabelle 5a, 5b", id: "QK")
  #var("W_pl_y", "W_(p l,y)", 1020000, "mm³", domain: ("steel", "ST-01"), label: "plastisches Widerstandsmoment", descr: "IPE 360", norm: "SZS C5:2018", norm-section: "pp. 30-31", id: "W_pl_y")
  #eq("M_y_Rd", "M_(y,R d)", `f_y dot W_pl_y / gamma_M1`, unit: "kNm", label: "Biegewiderstand", norm: "SIA 263", norm-section: "5.1.3 (40)", id: "M_y_Rd")
  #var("W_pl_z", "W_(p l,z)", 191000, "mm³", domain: ("steel", "ST-01"), label: "plastisches Widerstandsmoment", descr: "IPE 360", norm: "SZS C5:2018", norm-section: "pp. 30-31", id: "W_pl_z")
  #eq("M_z_Rd", "M_(z,R d)", `f_y dot W_pl_z / gamma_M1`, unit: "kNm", label: "Biegewiderstand", norm: "SIA 263", norm-section: "5.1.3 (40)", id: "M_z_Rd")
  #var("A", 7270, "mm²", domain: ("steel", "ST-01"), label: "Querschnittsfläche", descr: "IPE 360", norm: "SZS C5:2018", norm-section: "pp. 30-31", id: "A")
  #eq("N_Rd", "N_(R d)", `f_y dot A / gamma_M1`, unit: "kN", label: "Normalkraftwiderstand", norm: "SIA 263", norm-section: "5.1.2 (38)", id: "N_Rd")
  #eq("n", `abs(N_Ed) / N_Rd`, label: "bezogene Normalkraft", norm: "SIA 263", norm-section: "5.1.6.2", id: "n")
  #var("b", 170, "mm", domain: ("steel", "ST-01"), label: "Breite", norm: "SZS C5:2018", norm-section: "pp. 30-31", id: "b")
  #var("t_f", 12.7, "mm", domain: ("steel", "ST-01"), label: "Flanschdicke", norm: "SZS C5:2018", norm-section: "pp. 30-31", id: "t_f")
  #eq("a", `min((A - 2 dot b dot t_f) / A, 0.5)`, label: "Hilfswert", norm: "SIA 263", norm-section: "5.1.6.2", id: "a")
  #eq("xi", `1 / (1 - 0.5 dot a)`, label: "Hilfswert", norm: "SIA 263", norm-section: "5.1.6.2", id: "xi")
  #eq("M_y_N_Rd", "M_(y,N,R d)", `min(M_y_Rd dot xi dot (1 - n), M_y_Rd)`, unit: "kNm", label: "reduzierter Biegewiderstand", norm: "SIA 263", norm-section: "5.1.6.2 (45)", id: "M_y_N_Rd")
  #eq("M_z_N_Rd", "M_(z,N,R d)", `M_z_Rd`, unit: "kNm", label: "reduzierter Biegewiderstand", norm: "SIA 263", norm-section: "5.1.6.2 (47)", id: "M_z_N_Rd")
  #var("alpha_N", "alpha", 2, domain: ("steel", "ST-01"), label: "Exponent", norm: "SIA 263", norm-section: "5.1.6.4", id: "alpha_N")
  #eq("beta_N", "beta", `max(5 dot n, 1.1)`, label: "Exponent", norm: "SIA 263", norm-section: "5.1.6.4", id: "beta_N")

  #verify(`(M_y_Ed / M_y_N_Rd)^2 + (M_z_Ed / M_z_N_Rd)^1.1 <= 1`, id: "v-steel-bending")
  #eq("eta", `(M_y_Ed / M_y_N_Rd)^2 + (M_z_Ed / M_z_N_Rd)^1.1`, unit: "%", id: "eta")
]
