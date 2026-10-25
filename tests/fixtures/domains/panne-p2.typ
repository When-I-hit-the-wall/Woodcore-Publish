#import "/000-Typst-Config/commands.typ": *

#domain("panne-p2", label: "Panne de toiture P2")[
#calc-defaults(presets: "block", scope: "domain")
Panne en bois massif C24, 100/240 mm, classe d'humidité 2, sur deux appuis. Charges du toit sans eau et neige du toit SL.

  #var("gk_ak_gew", domain: ("dead-load", "EL+AL-Dach_ohne_Wasser"))
  #var("q_k1", domain: ("snow-load", "SL"))
  #var("e", 1, "m", label: "Entraxe des pannes")
  #var("l", 4.25, "m", label: "Portée")
  #var("gamma_G", 1.35, label: "Facteur de charge, actions permanentes", norm: "SIA 260", norm-section: "Tableau 1")
  #var("gamma_Q", 1.5, label: "Facteur de charge, actions variables", norm: "SIA 260", norm-section: "Tableau 1")
  #eq("q_d", `(gamma_G dot gk_ak_gew + gamma_Q dot q_k1) dot e`, unit: "kN/m", label: "Charge linéique de calcul", norm: "SIA 260", norm-section: "4.4.3.4")
  #eq("M_d", `q_d dot l^2 / 8`, unit: "kNm", label: "Moment de flexion de calcul")

_Résistance_

  #var("b", 100, "mm", label: "Largeur")
  #var("h", 240, "mm", label: "Hauteur")
  #eq("W_y", `b dot h^2 / 6`, unit: "mm³", label: "Module de flexion")
  #eq("sigma_m_d", "sigma_(m,d)", `M_d / W_y`, unit: "N/mm²", label: "Contrainte de flexion")
  #var("eta_w", 0.8, label: "Coefficient d'humidité, classe 2", norm: "SIA 265", norm-section: "Tableau 4")
  #var("f_m_d_tab", "f_(m,d,\"Tab\")", 14.1, "N/mm²", label: "Résistance à la flexion, C24", norm: "SIA 265", norm-section: "Tableau 8")
  #eq("f_m_d", "f_(m,d)", `eta_w dot f_m_d_tab`, unit: "N/mm²", label: "Résistance à la flexion de calcul", norm: "SIA 265", norm-section: "3.3.2.1")
  #verify(`sigma_m_d <= f_m_d`, norm: "SIA 265", norm-section: "4.2.3.1")
  #eq("eta", `sigma_m_d / f_m_d`, unit: "%", label: "Taux d'utilisation", role: "result")
]
