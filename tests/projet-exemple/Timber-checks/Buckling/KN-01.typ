#import "/000-Typst-Config/commands.typ": *

#domain("KN-01", label: "Stabilität – KN-01")[
#calc-defaults(presets: "block", scope: "domain") <KN-01-presets>
*S001*: Stütze, Fichte C24, 100/200 mm, Feuchteklasse 2 <KN-01-member>

  #var("b", 100, "mm", domain: ("check", "KN-01"), level: 0, id: "b")
  #var("h", 200, "mm", domain: ("check", "KN-01"), level: 0, id: "h")
  #eq("A", `b dot h`, unit: "mm²", id: "A")
  #var("i_y", 57.735027, "mm", domain: ("check", "KN-01"), id: "i_y")
  #var("i_z", 28.867513, "mm", domain: ("check", "KN-01"), id: "i_z")
  #var("eta_w_E", "eta_(w,E)", 0.9, domain: ("check", "KN-01"), id: "eta_w_E")
  #var("f_c_0_k", "f_(c,0,k)", 21, "N/mm²", domain: ("check", "KN-01"), id: "f_c_0_k")
  #var("E_0_05", "E_(0,05)", 6660, "N/mm²", domain: ("check", "KN-01"), id: "E_0_05")
  #var("eta_w", 0.8, domain: ("check", "KN-01"), id: "eta_w")
  #var("eta_t", 1, domain: ("check", "KN-01"), id: "eta_t")
  #var("f_c_0_d_tab", "f_(c,0,d,\"Tab\")", 12.4, "N/mm²", domain: ("check", "KN-01"), id: "f_c_0_d_tab")
  #eq("f_c_0_d", "f_(c,0,d)", `eta_w dot eta_t dot f_c_0_d_tab`, unit: "N/mm²", norm: "SIA 265", norm-section: "Tabelle 8", id: "f_c_0_d")

_Tragsicherheit_ <KN-01-part>

  #var("N_c_d", "N_(c,d)", 40, "kN", domain: ("check", "KN-01"), id: "N_c_d")
  #eq("sigma_c_0_d", "sigma_(c,0,d)", `N_c_d / A`, unit: "N/mm²", id: "sigma_c_0_d")
  #eq("eta_s", `sigma_c_0_d / f_c_0_d`, id: "eta_s")
  #var("beta_c", 0.2, domain: ("check", "KN-01"), id: "beta_c")
  #var("l_k_y", "l_(k,y)", 3000, "mm", domain: ("check", "KN-01"), id: "l_k_y")
  #eq("lambda_y", `l_k_y / i_y`, id: "lambda_y")
  #eq("lambda_rel_y", "lambda_(rel,y)", `lambda_y / pi dot sqrt(f_c_0_k / E_0_05)`, id: "lambda_rel_y")
  #eq("k_y", `0.5 dot (1 + beta_c dot (lambda_rel_y - 0.3) + lambda_rel_y^2)`, id: "k_y")
  #eq("k_c_y", "k_(c,y)", `1 / (k_y + sqrt(k_y^2 - lambda_rel_y^2))`, id: "k_c_y")
  #eq("eta_y", "eta_(c,y)", `sigma_c_0_d / (k_c_y dot f_c_0_d)`, id: "eta_y")
  #var("l_k_z", "l_(k,z)", 3000, "mm", domain: ("check", "KN-01"), id: "l_k_z")
  #eq("lambda_z", `l_k_z / i_z`, id: "lambda_z")
  #eq("lambda_rel_z", "lambda_(rel,z)", `lambda_z / pi dot sqrt(f_c_0_k / E_0_05)`, id: "lambda_rel_z")
  #eq("k_z", `0.5 dot (1 + beta_c dot (lambda_rel_z - 0.3) + lambda_rel_z^2)`, id: "k_z")
  #eq("k_c_z", "k_(c,z)", `1 / (k_z + sqrt(k_z^2 - lambda_rel_z^2))`, id: "k_c_z")
  #eq("eta_z", "eta_(c,z)", `sigma_c_0_d / (k_c_z dot f_c_0_d)`, id: "eta_z")
  #verify(`sigma_c_0_d <= k_c_z dot f_c_0_d`, id: "v-10-29")
  #eq("eta", `max(eta_s, eta_y, eta_z)`, unit: "%", id: "eta")
]
