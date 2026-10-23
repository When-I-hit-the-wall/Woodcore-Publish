#import "/000-Typst-Config/commands.typ": *

#domain("BI-02", label: "Biegung – BI-02")[
#calc-defaults(presets: "block", scope: "domain") <BI-02-presets>
*S001*: Stütze, Fichte C24, 100/200 mm, Feuchteklasse 2 <BI-02-member>

  #var("b", 100, "mm", domain: ("check", "BI-02"), level: 0, id: "b")
  #var("h", 200, "mm", domain: ("check", "BI-02"), level: 0, id: "h")
  #eq("A", `b dot h`, unit: "mm²", id: "A")
  #eq("W_y", `b dot h^2 / 6`, unit: "mm³", id: "W_y")
  #var("eta_w", 0.8, domain: ("check", "BI-02"), id: "eta_w")
  #var("eta_t", 1, domain: ("check", "BI-02"), id: "eta_t")
  #var("f_m_y_d", "f_(m,y,d)", 11.28, "N/mm²", domain: ("check", "BI-02"), id: "f_m_y_d")
  #var("f_c_0_d_tab", "f_(c,0,d,\"Tab\")", 12.4, "N/mm²", domain: ("check", "BI-02"), id: "f_c_0_d_tab")
  #eq("f_c_0_d", "f_(c,0,d)", `eta_w dot eta_t dot f_c_0_d_tab`, unit: "N/mm²", norm: "SIA 265", norm-section: "Tabelle 8", id: "f_c_0_d")

_Tragsicherheit_ <BI-02-part>

  #var("M_y_d", "M_(y,d)", 3, "kNm", domain: ("check", "BI-02"), id: "M_y_d")
  #var("N_c_d", "N_(c,d)", 40, "kN", domain: ("check", "BI-02"), id: "N_c_d")
  #eq("sigma_c_0_d", "sigma_(c,0,d)", `N_c_d / A`, unit: "N/mm²", id: "sigma_c_0_d")
  #eq("sigma_m_y_d", "sigma_(m,y,d)", `M_y_d / W_y`, unit: "N/mm²", id: "sigma_m_y_d")
  #verify(`(sigma_c_0_d / f_c_0_d)^2 + sigma_m_y_d / f_m_y_d <= 1`, id: "v-22")
  #eq("eta", `(sigma_c_0_d / f_c_0_d)^2 + sigma_m_y_d / f_m_y_d`, unit: "%", id: "eta")
]
