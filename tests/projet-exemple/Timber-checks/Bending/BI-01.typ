#import "/000-Typst-Config/commands.typ": *

#domain("BI-01", label: "Biegung – BI-01")[
#calc-defaults(presets: "block", scope: "domain") <BI-01-presets>
*T001*: Träger, Fichte C24, 100/200 mm, Feuchteklasse 2 <BI-01-member>

  #var("b", 100, "mm", domain: ("check", "BI-01"), level: 0, id: "b")
  #var("h", 200, "mm", domain: ("check", "BI-01"), level: 0, id: "h")
  #eq("W_y", `b dot h^2 / 6`, unit: "mm³", id: "W_y")
  #eq("W_z", `h dot b^2 / 6`, unit: "mm³", id: "W_z")
  #var("eta_w", 0.8, domain: ("check", "BI-01"), id: "eta_w")
  #var("eta_t", 1, domain: ("check", "BI-01"), id: "eta_t")
  #var("f_m_y_d", "f_(m,y,d)", 11.28, "N/mm²", domain: ("check", "BI-01"), id: "f_m_y_d")
  #var("f_m_z_d", "f_(m,z,d)", 11.28, "N/mm²", domain: ("check", "BI-01"), id: "f_m_z_d")

_Tragsicherheit_ <BI-01-part>

  #var("M_y_d", "M_(y,d)", 4.5, "kNm", domain: ("check", "BI-01"), id: "M_y_d")
  #var("M_z_d", "M_(z,d)", 0.3, "kNm", domain: ("check", "BI-01"), id: "M_z_d")
  #eq("sigma_m_y_d", "sigma_(m,y,d)", `M_y_d / W_y`, unit: "N/mm²", id: "sigma_m_y_d")
  #eq("sigma_m_z_d", "sigma_(m,z,d)", `M_z_d / W_z`, unit: "N/mm²", id: "sigma_m_z_d")
  #verify(`sigma_m_y_d / f_m_y_d + sigma_m_z_d / f_m_z_d <= 1`, id: "v-14")
  #eq("eta", `sigma_m_y_d / f_m_y_d + sigma_m_z_d / f_m_z_d`, unit: "%", id: "eta")
]
