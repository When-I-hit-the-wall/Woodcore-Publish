#import "/000-Typst-Config/commands.typ": *

#domain("ZT-01", label: "Zug parallel zur Faserrichtung – ZT-01")[
#calc-defaults(presets: "block", scope: "domain") <ZT-01-presets>
*T001*: Träger, Fichte C24, 100/200 mm, Feuchteklasse 2 <ZT-01-member>

  #var("b", 100, "mm", domain: ("check", "ZT-01"), level: 0, id: "b")
  #var("h", 200, "mm", domain: ("check", "ZT-01"), level: 0, id: "h")
  #eq("A", `b dot h`, unit: "mm²", id: "A")
  #var("eta_w", 0.8, domain: ("check", "ZT-01"), id: "eta_w")
  #var("eta_t", 1, domain: ("check", "ZT-01"), id: "eta_t")
  #var("f_t_0_d_tab", "f_(t,0,d,\"Tab\")", 8.5, "N/mm²", domain: ("check", "ZT-01"), id: "f_t_0_d_tab")
  #eq("f_t_0_d", "f_(t,0,d)", `eta_w dot eta_t dot f_t_0_d_tab`, unit: "N/mm²", norm: "SIA 265", norm-section: "Tabelle 8", id: "f_t_0_d")

_Tragsicherheit_ <ZT-01-part>

  #var("N_t_d", "N_(t,d)", 25, "kN", domain: ("check", "ZT-01"), id: "N_t_d")
  #eq("sigma_t_0_d", "sigma_(t,0,d)", `N_t_d / A`, unit: "N/mm²", norm: "SIA 265", norm-section: "4.2.1.1", id: "sigma_t_0_d")
  #verify(`sigma_t_0_d <= f_t_0_d`, id: "v-6")
  #eq("eta", `sigma_t_0_d / f_t_0_d`, unit: "%", id: "eta")
]
