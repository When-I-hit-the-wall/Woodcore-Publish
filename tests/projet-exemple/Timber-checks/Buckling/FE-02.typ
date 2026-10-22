#import "/000-Typst-Config/commands.typ": *

#domain("FE-02", label: "Stabilität – FE-02")[
#calc-defaults(presets: "block", scope: "domain") <FE-02-presets>
*FE-02*: D30, 140/240 mm, Feuchteklasse 1 <FE-02-member>

  #var("b_0", 140, "mm", domain: ("check", "FE-02"), level: 0, id: "b_0")
  #var("h_0", 240, "mm", domain: ("check", "FE-02"), level: 0, id: "h_0")
  #var("t_fi", "t", 30, "min", domain: ("check", "FE-02"), id: "t_fi")
  #var("beta_n", 0.5, "mm/min", domain: ("check", "FE-02"), id: "beta_n")
  #eq("d_char_n", "d_(char,n)", `beta_n dot t_fi`, unit: "mm", norm: "SIA 265", norm-section: "4.5.2.2", id: "d_char_n")
  #var("d_red", "d_(red)", 7, "mm", domain: ("check", "FE-02"), id: "d_red")
  #eq("d_ef", "d_(ef)", `d_char_n + d_red`, unit: "mm", norm: "SIA 265", norm-section: "4.5.2.2", id: "d_ef")
  #eq("b", "b_(fi)", `b_0 - 2 dot d_ef`, unit: "mm", norm: "SIA 265", norm-section: "4.5.2.2", id: "b")
  #eq("h", "h_(fi)", `h_0 - 2 dot d_ef`, unit: "mm", norm: "SIA 265", norm-section: "4.5.2.2", id: "h")
  #var("k_fi", "k_(fi)", 1.8, domain: ("check", "FE-02"), id: "k_fi")
  #eq("A", `b dot h`, unit: "mm²", id: "A")
  #var("i_y", 56.580326, "mm", domain: ("check", "FE-02"), id: "i_y")
  #var("i_z", 27.712813, "mm", domain: ("check", "FE-02"), id: "i_z")
  #var("eta_w_E", "eta_(w,E)", 1, domain: ("check", "FE-02"), id: "eta_w_E")
  #var("f_c_0_k", "f_(c,0,k)", 24, "N/mm²", domain: ("check", "FE-02"), id: "f_c_0_k")
  #var("E_0_05", "E_(0,05)", 9200, "N/mm²", domain: ("check", "FE-02"), id: "E_0_05")
  #var("eta_w", 1, domain: ("check", "FE-02"), id: "eta_w")
  #var("eta_t", 1, domain: ("check", "FE-02"), id: "eta_t")
  #var("f_c_0_d_tab", "f_(c,0,d,\"Tab\")", 14.1, "N/mm²", domain: ("check", "FE-02"), id: "f_c_0_d_tab")
  #eq("f_c_0_d", "f_(c,0,d)", `k_fi dot eta_w dot eta_t dot f_c_0_d_tab`, unit: "N/mm²", norm: "SIA 265", norm-section: "Tabelle 8", id: "f_c_0_d")

_Tragsicherheit_ <FE-02-part>

  #var("N_c_d", "N_(c,d)", 185, "kN", domain: ("check", "FE-02"), id: "N_c_d")
  #eq("sigma_c_0_d", "sigma_(c,0,d)", `N_c_d / A`, unit: "N/mm²", id: "sigma_c_0_d")
  #eq("eta_s", `sigma_c_0_d / f_c_0_d`, id: "eta_s")
  #var("beta_c", 0.2, domain: ("check", "FE-02"), id: "beta_c")
  #var("l_k_y", "l_(k,y)", 2400, "mm", domain: ("check", "FE-02"), id: "l_k_y")
  #eq("lambda_y", `l_k_y / i_y`, id: "lambda_y")
  #eq("lambda_rel_y", "lambda_(rel,y)", `lambda_y / pi dot sqrt(f_c_0_k / E_0_05)`, id: "lambda_rel_y")
  #eq("k_y", `0.5 dot (1 + beta_c dot (lambda_rel_y - 0.3) + lambda_rel_y^2)`, id: "k_y")
  #eq("k_c_y", "k_(c,y)", `1 / (k_y + sqrt(k_y^2 - lambda_rel_y^2))`, id: "k_c_y")
  #eq("eta_y", "eta_(c,y)", `sigma_c_0_d / (k_c_y dot f_c_0_d)`, id: "eta_y")
  #var("l_k_z", "l_(k,z)", 2400, "mm", domain: ("check", "FE-02"), id: "l_k_z")
  #eq("lambda_z", `l_k_z / i_z`, id: "lambda_z")
  #eq("lambda_rel_z", "lambda_(rel,z)", `lambda_z / pi dot sqrt(f_c_0_k / E_0_05)`, id: "lambda_rel_z")
  #eq("k_z", `0.5 dot (1 + beta_c dot (lambda_rel_z - 0.3) + lambda_rel_z^2)`, id: "k_z")
  #eq("k_c_z", "k_(c,z)", `1 / (k_z + sqrt(k_z^2 - lambda_rel_z^2))`, id: "k_c_z")
  #eq("eta_z", "eta_(c,z)", `sigma_c_0_d / (k_c_z dot f_c_0_d)`, id: "eta_z")
  #verify(`sigma_c_0_d <= k_c_z dot f_c_0_d`, id: "v-10-29")
  #eq("eta", `max(eta_s, eta_y, eta_z)`, unit: "%", id: "eta")
]
