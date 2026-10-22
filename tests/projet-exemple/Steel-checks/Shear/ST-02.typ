#import "/000-Typst-Config/commands.typ": *

#domain("ST-02", label: "Stahl: Querkraft – ST-02")[
#calc-defaults(presets: "block", scope: "domain") <ST-02-presets>
*IPE 360, S355* <ST-02-member>

  #var("f_y", 355, "N/mm²", domain: ("steel", "ST-02"), label: "Streckgrenze", descr: "S355, t ≤ 40 mm", norm: "SIA 263", norm-section: "Tabelle 1", id: "f_y")
  #var("gamma_M1", "gamma_(M 1)", 1.05, domain: ("steel", "ST-02"), label: "Widerstandsbeiwert", norm: "SIA 263", norm-section: "4.1.3", id: "gamma_M1")
  #var("V_z_Ed", "V_(z,E d)", 500, "kN", domain: ("steel", "ST-02"), label: "Querkraft", norm: "SIA 263", norm-section: "5.1.4, 5.1.5", id: "V_z_Ed")
  #var("M_y_Ed", "M_(y,E d)", 150, "kNm", domain: ("steel", "ST-02"), label: "Biegemoment", norm: "SIA 263", norm-section: "5.1.4, 5.1.5", id: "M_y_Ed")
  #var("QK", "\"QK\"", 1, domain: ("steel", "ST-02"), label: "Querschnittsklasse", descr: "Flansch oben links: c/t = 5.0 (Klasse 1: 7.3, 2: 8.1, 3: 11.4)", norm: "SIA 263", norm-section: "Tabelle 5a, 5b", id: "QK")
  #var("E", 210000, "N/mm²", domain: ("steel", "ST-02"), label: "Elastizitätsmodul", norm: "SIA 263", norm-section: "3.2.2.3", id: "E")
  #var("web_slenderness", "(h - t_f) / t_w", 43.4125, domain: ("steel", "ST-02"), label: "Stegschlankheit", norm: "SIA 263", norm-section: "5.1.4.2 (42)", id: "web_slenderness")
  #eq("web_limit", "sqrt(4 E / f_y)", `sqrt(4 dot E / f_y)`, label: "Grenzschlankheit", norm: "SIA 263", norm-section: "5.1.4.2 (42)", id: "web_limit")
  #var("tau_y", 205, "N/mm²", domain: ("steel", "ST-02"), label: "Fliessschubspannung", norm: "SIA 263", norm-section: "Tabelle 1", id: "tau_y")
  #var("A_v_z", "A_v", 3514, "mm²", domain: ("steel", "ST-02"), label: "wirksame Schubfläche", descr: "IPE 360", norm: "SZS C5:2018", norm-section: "pp. 30-31", id: "A_v_z")
  #eq("V_z_Rd", "V_(z,R d)", `tau_y dot A_v_z / gamma_M1`, unit: "kN", label: "Querkraftwiderstand", norm: "SIA 263", norm-section: "5.1.4 (41)", id: "V_z_Rd")
  #eq("eta_V", `V_z_Ed / V_z_Rd`, label: "Ausnutzung Querkraft", norm: "SIA 263", norm-section: "5.1.4", id: "eta_V")
  #var("W_pl_y", "W_(p l,y)", 1020000, "mm³", domain: ("steel", "ST-02"), label: "plastisches Widerstandsmoment", descr: "IPE 360", norm: "SZS C5:2018", norm-section: "pp. 30-31", id: "W_pl_y")
  #eq("M_y_Rd", "M_(y,R d)", `f_y dot W_pl_y / gamma_M1`, unit: "kNm", label: "Biegewiderstand", norm: "SIA 263", norm-section: "5.1.3 (40)", id: "M_y_Rd")
  #var("b", 170, "mm", domain: ("steel", "ST-02"), label: "Breite", norm: "SZS C5:2018", id: "b")
  #var("h", 360, "mm", domain: ("steel", "ST-02"), label: "Höhe", norm: "SZS C5:2018", id: "h")
  #var("t_1", 12.7, "mm", domain: ("steel", "ST-02"), label: "Flanschdicke", norm: "SZS C5:2018", norm-section: "5.1.5.2", id: "t_1")
  #var("t_2", 8, "mm", domain: ("steel", "ST-02"), label: "Stegdicke", norm: "SZS C5:2018", norm-section: "5.1.5.2", id: "t_2")
  #var("h_w", 334.6, "mm", domain: ("steel", "ST-02"), label: "Steghöhe", norm: "SZS C5:2018", norm-section: "5.1.5.2", id: "h_w")
  #eq("M_V_Rd", "M_(V,R d)", `b dot t_1 dot f_y dot (h - t_1) / gamma_M1 + h_w^2 dot t_2 dot f_y / (4 dot gamma_M1) dot (1 - (V_z_Ed / V_z_Rd)^2)`, unit: "kNm", label: "reduzierter Biegewiderstand", norm: "SIA 263", norm-section: "5.1.5.2 (43)", id: "M_V_Rd")
  #eq("eta_M", `M_y_Ed / M_V_Rd`, label: "Ausnutzung Biegung", norm: "SIA 263", norm-section: "5.1.5", id: "eta_M")

  #verify(`max(eta_V, eta_M) <= 1`, id: "v-steel-shear")
  #eq("eta", `max(eta_V, eta_M)`, unit: "%", id: "eta")
]
