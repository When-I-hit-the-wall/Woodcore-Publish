#import "/000-Typst-Config/commands.typ": *

#domain("BI-03", label: "Biegung – BI-03")[
#calc-defaults(presets: "block", scope: "domain") <BI-03-presets>
*BI-03*: GL24h, 120/280 mm, Feuchteklasse 1 <BI-03-member>

  #var("b", 120, "mm", domain: ("check", "BI-03"), level: 0, id: "b")
  #var("h", 280, "mm", domain: ("check", "BI-03"), level: 0, id: "h")
  #eq("A", `b dot h`, unit: "mm²", id: "A")
  #eq("W_y", `b dot h^2 / 6`, unit: "mm³", id: "W_y")
  #var("eta_w", 1, domain: ("check", "BI-03"), id: "eta_w")
  #var("eta_t", 1, domain: ("check", "BI-03"), id: "eta_t")
  #var("k_h_y", "k_(h,y)", 1.079194, domain: ("check", "BI-03"), id: "k_h_y")
  #var("f_m_y_d", "f_(m,y,d)", 17.267096, "N/mm²", domain: ("check", "BI-03"), id: "f_m_y_d")
  #var("f_t_0_d_tab", "f_(t,0,d,\"Tab\")", 12.8, "N/mm²", domain: ("check", "BI-03"), id: "f_t_0_d_tab")
  #eq("f_t_0_d", "f_(t,0,d)", `eta_w dot eta_t dot f_t_0_d_tab`, unit: "N/mm²", norm: "SIA 265", norm-section: "Tabelle 9", id: "f_t_0_d")
  #var("f_t_90_d_tab", "f_(t,90,d,\"Tab\")", 0.15, "N/mm²", domain: ("check", "BI-03"), id: "f_t_90_d_tab")
  #eq("f_t_90_d", "f_(t,90,d)", `eta_w dot eta_t dot f_t_90_d_tab`, unit: "N/mm²", norm: "SIA 265", norm-section: "Tabelle 9", id: "f_t_90_d")
  #var("f_c_90_d_tab", "f_(c,90,d,\"Tab\")", 1.9, "N/mm²", domain: ("check", "BI-03"), id: "f_c_90_d_tab")
  #eq("f_c_90_d", "f_(c,90,d)", `eta_w dot eta_t dot f_c_90_d_tab`, unit: "N/mm²", norm: "SIA 265", norm-section: "Tabelle 9", id: "f_c_90_d")

_Tragsicherheit_ <BI-03-part>

  #var("M_y_d", "M_(y,d)", 3, "kNm", domain: ("check", "BI-03"), id: "M_y_d")
  #var("alpha", 10, "°", domain: ("check", "BI-03"), id: "alpha")
  #var("N_t_d", "N_(t,d)", 25, "kN", domain: ("check", "BI-03"), id: "N_t_d")
  #eq("f_t_alpha_d", "f_(t,alpha,d)", `f_t_90_d dot f_t_0_d / (f_t_0_d dot sin(alpha)^2 + f_t_90_d dot cos(alpha)^2)`, unit: "N/mm²", id: "f_t_alpha_d")
  #eq("sigma_t_alpha_d", "sigma_(t,alpha,d)", `N_t_d / A`, unit: "N/mm²", id: "sigma_t_alpha_d")
  #eq("k_mc_alpha", "k_(mc,alpha)", `f_c_90_d / (f_m_y_d dot sin(alpha)^2 + f_c_90_d dot cos(alpha)^2)`, id: "k_mc_alpha")
  #eq("k_mt_alpha", "k_(mt,alpha)", `f_t_90_d / (f_m_y_d dot sin(alpha)^2 + f_t_90_d dot cos(alpha)^2)`, id: "k_mt_alpha")
  #eq("sigma_m_alpha_d", "sigma_(m,alpha,d)", `M_y_d / W_y`, unit: "N/mm²", id: "sigma_m_alpha_d")
  #eq("eta_m_t", "eta_(m,t)", `sigma_t_alpha_d / f_t_alpha_d + sigma_m_alpha_d / (k_mt_alpha dot f_m_y_d)`, id: "eta_m_t")
  #eq("eta_m_c", "eta_(m,c)", `sigma_m_alpha_d / (k_mc_alpha dot f_m_y_d)`, id: "eta_m_c")
  #verify(`sigma_t_alpha_d / f_t_alpha_d + sigma_m_alpha_d / (k_mt_alpha dot f_m_y_d) <= 1`, id: "v-21-9-19-20")
  #eq("eta", `max(eta_m_t, eta_m_c)`, unit: "%", id: "eta")
]
