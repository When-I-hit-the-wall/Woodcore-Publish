#import "/000-Typst-Config/commands.typ": *

#domain("SC-01", label: "Schub – SC-01")[
#calc-defaults(presets: "block", scope: "domain") <SC-01-presets>
*T001*: Träger, Fichte C24, 100/200 mm, Feuchteklasse 2 <SC-01-member>

  #var("b", 100, "mm", domain: ("check", "SC-01"), level: 0, id: "b")
  #var("h", 200, "mm", domain: ("check", "SC-01"), level: 0, id: "h")
  #eq("A", `b dot h`, unit: "mm²", id: "A")
  #var("eta_w", 0.8, domain: ("check", "SC-01"), id: "eta_w")
  #var("eta_t", 1, domain: ("check", "SC-01"), id: "eta_t")
  #var("f_v_d_tab", "f_(v,d,\"Tab\")", 1.5, "N/mm²", domain: ("check", "SC-01"), id: "f_v_d_tab")
  #eq("f_v_d", "f_(v,d)", `eta_w dot eta_t dot f_v_d_tab`, unit: "N/mm²", norm: "SIA 265", norm-section: "Tabelle 8", id: "f_v_d")

_Tragsicherheit_ <SC-01-part>

  #var("V_z_d", "V_(z,d)", 12, "kN", domain: ("check", "SC-01"), id: "V_z_d")
  #eq("tau_z_d", "tau_(z,d)", `1.5 dot V_z_d / A`, unit: "N/mm²", id: "tau_z_d")
  #var("V_y_d", "V_(y,d)", 2, "kN", domain: ("check", "SC-01"), id: "V_y_d")
  #eq("tau_y_d", "tau_(y,d)", `1.5 dot V_y_d / A`, unit: "N/mm²", id: "tau_y_d")
  #eq("tau_d", `sqrt(tau_z_d^2 + tau_y_d^2)`, unit: "N/mm²", id: "tau_d")
  #verify(`tau_d <= f_v_d`, id: "v-23")
  #eq("eta", `tau_d / f_v_d`, unit: "%", id: "eta")
]
