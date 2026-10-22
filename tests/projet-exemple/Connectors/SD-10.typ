#import "/000-Typst-Config/commands.typ": *

#domain("SD-10", label: "Stabdübel – SD-10")[
#calc-defaults(presets: "block", scope: "domain") <SD-10-presets>
*SD-10: Stabdübel, Holz-Holz zweischnittig, Ø 10 mm, L = 100 mm, 8/200, vorgebohrt* <SD-10-member>

Stabdübel 4x 10mm Durchmesser <SD-10-description>

#figure(image("/Connectors/Exports/Figures/SD-10-pattern-de.svg", width: 60%)) <SD-10-figure-pattern>

#figure(image("/Connectors/Exports/Figures/SD-10-section.svg", width: 60%)) <SD-10-figure-section>

  #var("d", 10, "mm", domain: ("connector", "SD-10"), label: "Durchmesser", norm: "SIA 265", norm-section: "6.2.1.1", id: "d")
  #var("n_tot", "n_\"tot\"", 4, domain: ("connector", "SD-10"), label: "Anzahl Verbinder", norm: "SIA 265", norm-section: "6.2.1.1", id: "n_tot")
  #var("f_u_k", "f_(u,k)", 510, "N/mm²", domain: ("connector", "SD-10"), label: "char. Zugfestigkeit des Stabdübels", norm: "SIA 265", norm-section: "6.1.4.4", id: "f_u_k")
  #var("rho_k_1", "rho_(k,1)", 350, "kg/m³", domain: ("connector", "SD-10"), label: "Rohdichte", descr: "Bauteil 1: C24, im Verbindungsmittel festgelegt.", norm: "SIA 265", norm-section: "3.3.2.1", id: "rho_k_1")
  #var("alpha_1", 0, "°", domain: ("connector", "SD-10"), label: "Winkel zwischen der Kraft- und Faserrichtung der Holzteile", norm: "SIA 265", norm-section: "6.1.4.2", id: "alpha_1")
  #var("rho_k_2", "rho_(k,2)", 350, "kg/m³", domain: ("connector", "SD-10"), label: "Rohdichte", descr: "Bauteil 2: C24, im Verbindungsmittel festgelegt.", norm: "SIA 265", norm-section: "3.3.2.1", id: "rho_k_2")
  #var("alpha_2", 0, "°", domain: ("connector", "SD-10"), label: "Winkel zwischen der Kraft- und Faserrichtung der Holzteile", norm: "SIA 265", norm-section: "6.1.4.2", id: "alpha_2")
  #var("f_h_0_1", "f_(h,0,1)", 25.83, "N/mm²", domain: ("connector", "SD-10"), label: "Lochleibungsfestigkeit parallel zur Faser", norm: "SIA 265", norm-section: "6.1.4.3", id: "f_h_0_1")
  #var("f_h_90_1", "f_(h,90,1)", 17.22, "N/mm²", domain: ("connector", "SD-10"), label: "Lochleibungsfestigkeit rechtwinklig zur Faser", norm: "SIA 265", norm-section: "6.1.4.3", id: "f_h_90_1")
  #var("f_h_1", "f_(h,1,k)", 25.83, "N/mm²", domain: ("connector", "SD-10"), label: "Lochleibungsfestigkeit", norm: "SIA 265", norm-section: "6.1.4.3", id: "f_h_1")
  #var("f_h_0_2", "f_(h,0,2)", 25.83, "N/mm²", domain: ("connector", "SD-10"), label: "Lochleibungsfestigkeit parallel zur Faser", norm: "SIA 265", norm-section: "6.1.4.3", id: "f_h_0_2")
  #var("f_h_90_2", "f_(h,90,2)", 17.22, "N/mm²", domain: ("connector", "SD-10"), label: "Lochleibungsfestigkeit rechtwinklig zur Faser", norm: "SIA 265", norm-section: "6.1.4.3", id: "f_h_90_2")
  #var("f_h_2", "f_(h,2,k)", 25.83, "N/mm²", domain: ("connector", "SD-10"), label: "Lochleibungsfestigkeit", norm: "SIA 265", norm-section: "6.1.4.3", id: "f_h_2")
  #eq("beta_f", `f_h_2 / f_h_1`, label: "Verhältnis der Lochleibungsfestigkeiten", norm: "SIA 265", norm-section: "A.1.1", id: "beta_f")
  #var("t_1", 50, "mm", domain: ("connector", "SD-10"), label: "Holzdicke", norm: "SIA 265", norm-section: "A.1.2", id: "t_1")
  #var("t_2", 100, "mm", domain: ("connector", "SD-10"), label: "Holzdicke", norm: "SIA 265", norm-section: "A.1.2", id: "t_2")
  #eq("k_beta_max", "k_(beta,\"max\")", `sqrt(4 dot beta_f / (1 + beta_f))`, label: "Grösstwert des Hilfswerts", norm: "SIA 265", norm-section: "A.1.1", id: "k_beta_max")
  #var("t_c_1_1", "t_(1,1)", 21.058927, "mm", domain: ("connector", "SD-10"), label: "Holzdicke für den unteren Eckwert", norm: "SIA 265", norm-section: "A.1.1", id: "t_c_1_1")
  #eq("k_beta_1_1", "k_(beta,1,1)", `0.6 dot k_beta_max`, label: "Hilfswert zum unteren Eckwert", norm: "SIA 265", norm-section: "A.1.1", id: "k_beta_1_1")
  #var("t_c_1_2", "t_(1,2)", 60.305111, "mm", domain: ("connector", "SD-10"), label: "Holzdicke für den oberen Eckwert", norm: "SIA 265", norm-section: "A.1.1", id: "t_c_1_2")
  #eq("k_beta_1_2", "k_(beta,1,2)", `k_beta_max`, label: "Hilfswert zum oberen Eckwert", norm: "SIA 265", norm-section: "A.1.1", id: "k_beta_1_2")
  #eq("k_beta_1", "k_(beta,1)", `k_beta_1_1 + (t_1 - t_c_1_1) / (t_c_1_2 - t_c_1_1) dot (k_beta_1_2 - k_beta_1_1)`, label: "Hilfswert zur Scherfuge", norm: "SIA 265", norm-section: "A.1.1", id: "k_beta_1")
  #var("t_c_2_2", "t_(2,2)", 49.958389, "mm", domain: ("connector", "SD-10"), label: "Holzdicke für den oberen Eckwert", norm: "SIA 265", norm-section: "A.1.1", id: "t_c_2_2")
  #eq("k_beta_2_2", "k_(beta,2,2)", `k_beta_max`, label: "Hilfswert zum oberen Eckwert", norm: "SIA 265", norm-section: "A.1.1", id: "k_beta_2_2")
  #eq("k_beta_2", "k_(beta,2)", `k_beta_2_2`, label: "Hilfswert zur Scherfuge", norm: "SIA 265", norm-section: "A.1.1", id: "k_beta_2")
  #var("n_1", 2, domain: ("connector", "SD-10"), label: "Anzahl der in Faserrichtung des Holzes hintereinander angeordneten Verbindungsmittel", norm: "SIA 265", norm-section: "6.1.4.2", id: "n_1")
  #var("a_1_1", "a_(1,1)", 120, "mm", domain: ("connector", "SD-10"), label: "Abstand der Verbindungsmittel untereinander in Faserrichtung", norm: "SIA 265", norm-section: "6.1.4.2", id: "a_1_1")
  #var("k_red_1", "k_(\"red\",1)", 0.976545, domain: ("connector", "SD-10"), label: "Reduktionsbeiwert", norm: "SIA 265", norm-section: "6.1.4.2", id: "k_red_1")
  #var("n_2", 2, domain: ("connector", "SD-10"), label: "Anzahl der in Faserrichtung des Holzes hintereinander angeordneten Verbindungsmittel", norm: "SIA 265", norm-section: "6.1.4.2", id: "n_2")
  #var("a_1_2", "a_(1,2)", 120, "mm", domain: ("connector", "SD-10"), label: "Abstand der Verbindungsmittel untereinander in Faserrichtung", norm: "SIA 265", norm-section: "6.1.4.2", id: "a_1_2")
  #var("k_red_2", "k_(\"red\",2)", 0.976545, domain: ("connector", "SD-10"), label: "Reduktionsbeiwert", norm: "SIA 265", norm-section: "6.1.4.2", id: "k_red_2")
  #var("M_u_k", "M_(u,k)", 60910.397095, "Nmm", domain: ("connector", "SD-10"), label: "char. Fliessmoment des Stabdübels", norm: "SIA 265", norm-section: "6.1.4.4", id: "M_u_k")
  #var("k_beta", 1.265678, domain: ("connector", "SD-10"), label: "Hilfswert zur Scherfuge", descr: "Massgebend ist der kleinste Hilfswert der beteiligten Holzteile (Tabellen 45 und 46, zwischen den Eckwerten linear interpoliert).", norm: "SIA 265", norm-section: "A.1.1", id: "k_beta")
  #var("p", 2, domain: ("connector", "SD-10"), label: "Anzahl Scherfugen", norm: "SIA 265", norm-section: "6.2.1.1", id: "p")
  #var("p_k_beta", "(p dot k_beta)", 2.531356, domain: ("connector", "SD-10"), label: "Scherfugen mit ihren Hilfswerten", norm: "SIA 265", norm-section: "6.2.1.1", id: "p_k_beta")
  #var("k_red", "k_\"red\"", 0.976545, domain: ("connector", "SD-10"), label: "Massgebender Reduktionsbeiwert", descr: "Bei unterschiedlichen Winkeln ist $k_\"red\"$ für alle Holzteile einzeln zu bestimmen und der kleinste Wert einzusetzen.", norm: "SIA 265", norm-section: "6.1.4.2", id: "k_red")
  #var("n_quer_1", "n_(\"quer\",1)", 2, domain: ("connector", "SD-10"), label: "Anzahl Verbindungsmittel quer zur Faserrichtung", descr: "$n_\"quer\" = n_\"tot\" \\/ n$, aufgerundet.", norm: "SIA 265", norm-section: "6.1.4.2", id: "n_quer_1")
  #var("n_quer_2", "n_(\"quer\",2)", 2, domain: ("connector", "SD-10"), label: "Anzahl Verbindungsmittel quer zur Faserrichtung", norm: "SIA 265", norm-section: "6.1.4.2", id: "n_quer_2")
  #var("k_alpha", 0.73, domain: ("connector", "SD-10"), label: "Beiwert der Tragwiderstandsgleichung", norm: "SIA 265", norm-section: "6.2.1.1", id: "k_alpha")
  #var("eta_w", 0.8, domain: ("connector", "SD-10"), label: "Umrechnungsfaktor Holzfeuchte", descr: "Feuchteklasse 2.", norm: "SIA 265", norm-section: "3.2.1.3", id: "eta_w")
  #var("eta_t", 1, domain: ("connector", "SD-10"), label: "Umrechnungsfaktor Einwirkungsdauer", norm: "SIA 265", norm-section: "2.2.6", id: "eta_t")
  #eq("R_d", `k_alpha dot k_red dot p_k_beta dot sqrt(M_u_k dot f_h_1 dot d) dot eta_w dot eta_t`, unit: "kN", label: "Tragwiderstand pro Verbindungsmittel", norm: "SIA 265", norm-section: "6.2.1.1", id: "R_d")
  #eq("R_d_Verb", "R_(d,\"Verb\")", `n_tot dot R_d`, unit: "kN", label: "Tragwiderstand der Verbindung", norm: "SIA 265", norm-section: "6.2.1.1", id: "R_d_Verb")
  #var("eta_w_ser", "eta_(w,\"Steif\")", 0.9, domain: ("connector", "SD-10"), label: "Umrechnungsfaktor Holzfeuchte für die Steifigkeit", norm: "SIA 265", norm-section: "3.2.1.3", id: "eta_w_ser")
  #var("K_ser_1", "K_(\"ser\",1)", 2531.615735, "N/mm", domain: ("connector", "SD-10"), label: "Verschiebungsmodul", norm: "SIA 265", norm-section: "6.2.1.4", id: "K_ser_1")
  #var("K_ser_2", "K_(\"ser\",2)", 2531.615735, "N/mm", domain: ("connector", "SD-10"), label: "Verschiebungsmodul", norm: "SIA 265", norm-section: "6.2.1.4", id: "K_ser_2")
  #eq("K_ser", "K_\"ser\"", `min(K_ser_1, K_ser_2)`, unit: "N/mm", label: "Massgebender Verschiebungsmodul", norm: "SIA 265", norm-section: "6.2.1.4", id: "K_ser")
  #eq("K_ser_Verb", "K_(\"ser\",\"Verb\")", `n_tot dot p dot K_ser`, unit: "N/mm", label: "Verschiebungsmodul der Verbindung", descr: "Der Schlupf beträgt rund 0.5 mm (6.2.1.3).", norm: "SIA 265", norm-section: "6.2.1.4", id: "K_ser_Verb")

_Hilfswert $k_beta$_ <SD-10-table-1-title>
#figure(image("/Connectors/Exports/Figures/SD-10-kbeta-1.svg", width: 45%), caption: [Bauteil 1 – Seitenholz]) <SD-10-table-1-figure-1>
#figure(image("/Connectors/Exports/Figures/SD-10-kbeta-2.svg", width: 45%), caption: [Bauteil 2 – Mittelholz]) <SD-10-table-1-figure-2>
Zwischenwerte werden linear interpoliert (Figur 45). Massgebend ist der kleinere Wert; $beta_f = f_(h,2,k) \/ f_(h,1,k)$. <SD-10-table-1-note>

_Minimale Abstände_ <SD-10-table-2-title>
#table(columns: 5, table.header([*$d$ = 10 mm*], table.cell(colspan: 2, [*in Faserrichtung*]), table.cell(colspan: 2, [*senkrecht zur Faserrichtung*]), [*Abstand*], [*[mm]*], [], [*[mm]*], []), [von Stabdübel zu Stabdübel], [70], [$7 d$], [30], [$3 d$], [vom beanspruchten Rand], [80], [$7 d$ (min. 80 mm)], [40], [$4 d$], [vom unbeanspruchten Rand], [50], [$5 d$], [30], [$3 d$], [*min. Länge der Verbindung*], [*200*], [], [*100*], []) <SD-10-table-2>
Tabelle 24. Gleichung (88) gilt nur bei Einhaltung dieser Abstände (6.2.1.1). Die Mindestlänge folgt aus der Anzahl Verbindungsmittel in und quer zur Faserrichtung. <SD-10-table-2-note>
]
