#import "/000-Typst-Config/commands.typ": *

#domain("DR-01", label: "Druck rechtwinklig zur Faserrichtung – DR-01")[
#calc-defaults(presets: "block", scope: "domain") <DR-01-presets>
*T001*: Träger, Fichte C24, 100/200 mm, Feuchteklasse 2 <DR-01-member>

  #var("b", 100, "mm", domain: ("check", "DR-01"), level: 0, id: "b")
  #var("h", 200, "mm", domain: ("check", "DR-01"), level: 0, id: "h")
  #var("eta_w", 0.8, domain: ("check", "DR-01"), id: "eta_w")
  #var("eta_t", 1, domain: ("check", "DR-01"), id: "eta_t")
  #var("f_c_90_d_tab", "f_(c,90,d,\"Tab\")", 1.8, "N/mm²", domain: ("check", "DR-01"), id: "f_c_90_d_tab")
  #eq("f_c_90_d", "f_(c,90,d)", `eta_w dot eta_t dot f_c_90_d_tab`, unit: "N/mm²", norm: "SIA 265", norm-section: "Tabelle 8", id: "f_c_90_d")

_Tragsicherheit_ <DR-01-part>

  #var("l_c", "l", 120, "mm", domain: ("check", "DR-01"), id: "l_c")
  #var("w_c", "w", 100, "mm", domain: ("check", "DR-01"), id: "w_c")
  #eq("A_c", `l_c dot w_c`, unit: "mm²", id: "A_c")
  #var("F_c_d", "F_(c,90,d)", 16, "kN", domain: ("check", "DR-01"), id: "F_c_d")
  #eq("sigma_c_90_d", "sigma_(c,90,d)", `F_c_d / A_c`, unit: "N/mm²", id: "sigma_c_90_d")
  #verify(`sigma_c_90_d <= f_c_90_d`, id: "v-11")
  #eq("eta", `sigma_c_90_d / f_c_90_d`, unit: "%", id: "eta")
]
