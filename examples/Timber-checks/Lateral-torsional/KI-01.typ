#import "/000-Typst-Config/commands.typ": *

#domain("KI-01", label: "Kippen – KI-01")[
#calc-defaults(presets: "block", scope: "domain") <KI-01-presets>
*T001*: Träger, Fichte C24, 100/200 mm, Feuchteklasse 2 <KI-01-member>

  #var("b", 100, "mm", domain: ("check", "KI-01"), level: 0, id: "b")
  #var("h", 200, "mm", domain: ("check", "KI-01"), level: 0, id: "h")
  #eq("W_y", `b dot h^2 / 6`, unit: "mm³", id: "W_y")
  #var("eta_w", 0.8, domain: ("check", "KI-01"), id: "eta_w")
  #var("eta_t", 1, domain: ("check", "KI-01"), id: "eta_t")
  #var("f_m_y_d", "f_(m,y,d)", 11.28, "N/mm²", domain: ("check", "KI-01"), id: "f_m_y_d")
  #var("i_y", 57.735027, "mm", domain: ("check", "KI-01"), id: "i_y")
  #var("i_z", 28.867513, "mm", domain: ("check", "KI-01"), id: "i_z")
  #var("eta_w_E", "eta_(w,E)", 0.9, domain: ("check", "KI-01"), id: "eta_w_E")
  #var("f_c_0_k", "f_(c,0,k)", 21, "N/mm²", domain: ("check", "KI-01"), id: "f_c_0_k")
  #var("E_0_05", "E_(0,05)", 6660, "N/mm²", domain: ("check", "KI-01"), id: "E_0_05")

_Tragsicherheit_ <KI-01-part>

  #var("M_y_d", "M_(y,d)", 4.5, "kNm", domain: ("check", "KI-01"), id: "M_y_d")
  #eq("sigma_m_y_d", "sigma_(m,y,d)", `M_y_d / W_y`, unit: "N/mm²", id: "sigma_m_y_d")
  #eq("eta_s", `sigma_m_y_d / f_m_y_d`, id: "eta_s")
  #var("a", 3000, "mm", domain: ("check", "KI-01"), id: "a")
  #eq("sigma_m_crit", "sigma_(m,crit)", `0.75 dot E_0_05 dot b^2 / (a dot h)`, unit: "N/mm²", id: "sigma_m_crit")
  #var("f_m_k", "f_(m,k)", 24, "N/mm²", domain: ("check", "KI-01"), id: "f_m_k")
  #eq("lambda_rel_m", "lambda_(rel,m)", `sqrt(f_m_k / sigma_m_crit)`, id: "lambda_rel_m")
  #var("k_m", 1, domain: ("check", "KI-01"), id: "k_m")
  #eq("eta_m", `sigma_m_y_d / (k_m dot f_m_y_d)`, id: "eta_m")
  #verify(`sigma_m_y_d <= k_m dot f_m_y_d`, id: "v-38")
  #eq("eta", `max(eta_s, eta_m)`, unit: "%", id: "eta")
]
