#import "/000-Typst-Config/commands.typ": *

#domain("ZT-02", label: "Zug unter einem Winkel zur Faserrichtung – ZT-02")[
#calc-defaults(presets: "block", scope: "domain") <ZT-02-presets>
*ZT-02*: GL24h, 120/240 mm, Feuchteklasse 1 <ZT-02-member>

  #var("b", 120, "mm", domain: ("check", "ZT-02"), level: 0, id: "b")
  #var("h", 240, "mm", domain: ("check", "ZT-02"), level: 0, id: "h")
  #eq("A", `b dot h`, unit: "mm²", id: "A")
  #var("eta_w", 1, domain: ("check", "ZT-02"), id: "eta_w")
  #var("eta_t", 1, domain: ("check", "ZT-02"), id: "eta_t")
  #var("f_t_0_d_tab", "f_(t,0,d,\"Tab\")", 12.8, "N/mm²", domain: ("check", "ZT-02"), id: "f_t_0_d_tab")
  #eq("f_t_0_d", "f_(t,0,d)", `eta_w dot eta_t dot f_t_0_d_tab`, unit: "N/mm²", norm: "SIA 265", norm-section: "Tabelle 9", id: "f_t_0_d")
  #var("f_t_90_d_tab", "f_(t,90,d,\"Tab\")", 0.15, "N/mm²", domain: ("check", "ZT-02"), id: "f_t_90_d_tab")
  #eq("f_t_90_d", "f_(t,90,d)", `eta_w dot eta_t dot f_t_90_d_tab`, unit: "N/mm²", norm: "SIA 265", norm-section: "Tabelle 9", id: "f_t_90_d")

_Tragsicherheit_ <ZT-02-part>

  #var("N_t_d", "N_(t,d)", 20, "kN", domain: ("check", "ZT-02"), id: "N_t_d")
  #var("alpha", 10, "°", domain: ("check", "ZT-02"), id: "alpha")
  #eq("f_t_alpha_d", "f_(t,alpha,d)", `f_t_90_d dot f_t_0_d / (f_t_0_d dot sin(alpha)^2 + f_t_90_d dot cos(alpha)^2)`, unit: "N/mm²", norm: "SIA 265", norm-section: "4.2.1.3 (9)", id: "f_t_alpha_d")
  #eq("sigma_t_alpha_d", "sigma_(t,alpha,d)", `N_t_d / A`, unit: "N/mm²", norm: "SIA 265", norm-section: "4.2.1.3", id: "sigma_t_alpha_d")
  #verify(`sigma_t_alpha_d <= f_t_alpha_d`, id: "v-8-9")
  #eq("eta", `sigma_t_alpha_d / f_t_alpha_d`, unit: "%", id: "eta")
]
