#import "/000-Typst-Config/commands.typ": *

#domain("DR-02", label: "Druck parallel zur Faserrichtung – DR-02")[
#calc-defaults(presets: "block", scope: "domain") <DR-02-presets>
*DR-02*: GL24h, 140/140 mm, Feuchteklasse 1 <DR-02-member>

  #var("b", 140, "mm", domain: ("check", "DR-02"), level: 0, id: "b")
  #var("h", 140, "mm", domain: ("check", "DR-02"), level: 0, id: "h")
  #eq("A", `b dot h`, unit: "mm²", id: "A")
  #var("eta_w", 1, domain: ("check", "DR-02"), id: "eta_w")
  #var("eta_t", 1, domain: ("check", "DR-02"), id: "eta_t")
  #var("f_c_0_d_tab", "f_(c,0,d,\"Tab\")", 16, "N/mm²", domain: ("check", "DR-02"), id: "f_c_0_d_tab")
  #eq("f_c_0_d", "f_(c,0,d)", `eta_w dot eta_t dot f_c_0_d_tab`, unit: "N/mm²", norm: "SIA 265", norm-section: "Tabelle 9", id: "f_c_0_d")

_Tragsicherheit_ <DR-02-part>

  #var("N_c_d", "N_(c,d)", 60, "kN", domain: ("check", "DR-02"), id: "N_c_d")
  #eq("sigma_c_0_d", "sigma_(c,0,d)", `N_c_d / A`, unit: "N/mm²", id: "sigma_c_0_d")
  #verify(`sigma_c_0_d <= f_c_0_d`, id: "v-10")
  #eq("eta", `sigma_c_0_d / f_c_0_d`, unit: "%", id: "eta")
]
