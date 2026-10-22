#import "/000-Typst-Config/commands.typ": *

#domain("FE-01", label: "Biegung – FE-01")[
#calc-defaults(presets: "block", scope: "domain") <FE-01-presets>
*FE-01*: C24, 140/200 mm, Feuchteklasse 1 <FE-01-member>

  #var("b_0", 140, "mm", domain: ("check", "FE-01"), level: 0, id: "b_0")
  #var("h_0", 200, "mm", domain: ("check", "FE-01"), level: 0, id: "h_0")
  #var("t_fi", "t", 60, "min", domain: ("check", "FE-01"), id: "t_fi")
  #var("beta_n", 0.8, "mm/min", domain: ("check", "FE-01"), id: "beta_n")
  #eq("d_char_n", "d_(char,n)", `beta_n dot t_fi`, unit: "mm", norm: "SIA 265", norm-section: "4.5.2.2", id: "d_char_n")
  #var("d_red", "d_(red)", 7, "mm", domain: ("check", "FE-01"), id: "d_red")
  #eq("d_ef", "d_(ef)", `d_char_n + d_red`, unit: "mm", norm: "SIA 265", norm-section: "4.5.2.2", id: "d_ef")
  #eq("b", "b_(fi)", `b_0 - 2 dot d_ef`, unit: "mm", norm: "SIA 265", norm-section: "4.5.2.2", id: "b")
  #eq("h", "h_(fi)", `h_0 - d_ef`, unit: "mm", norm: "SIA 265", norm-section: "4.5.2.2", id: "h")
  #var("k_fi", "k_(fi)", 1.8, domain: ("check", "FE-01"), id: "k_fi")
  #eq("W_y", `b dot h^2 / 6`, unit: "mm³", id: "W_y")
  #var("eta_w", 1, domain: ("check", "FE-01"), id: "eta_w")
  #var("eta_t", 1, domain: ("check", "FE-01"), id: "eta_t")
  #var("f_m_y_d", "f_(m,y,d)", 25.38, "N/mm²", domain: ("check", "FE-01"), id: "f_m_y_d")

_Tragsicherheit_ <FE-01-part>

  #var("M_y_d", "M_(y,d)", 2, "kNm", domain: ("check", "FE-01"), id: "M_y_d")
  #eq("sigma_m_y_d", "sigma_(m,y,d)", `M_y_d / W_y`, unit: "N/mm²", id: "sigma_m_y_d")
  #eq("eta_s", `sigma_m_y_d / f_m_y_d`, id: "eta_s")
  #verify(`sigma_m_y_d / f_m_y_d <= 1`, id: "v-14")
  #eq("eta", `sigma_m_y_d / f_m_y_d`, unit: "%", id: "eta")
]
