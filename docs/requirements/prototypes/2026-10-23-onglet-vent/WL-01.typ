#import "/commands.typ": *

#domain("WL-01", label: "Charge de vent – WL-01")[
#calc-defaults(presets: "block", scope: "domain") <WL-01-presets>

#figure(image("/Variable-loads/Wind/WL-01-building.png", width: 50%), caption: [Bâtiment du tableau 36 : surfaces A à H, m, n, o, forces Q₁ à Q₃ et direction φ (SIA 261:2020, annexe C, tableau 36)]) <WL-01-figure-1>

  #var("qp0", "q_(p 0)", 1.1, "kN/m²", domain: ("wind-load", "WL-01"), label: "Valeur de référence de la pression dynamique", descr: "Valeur de référence de la pression dynamique au lieu considéré selon SIA 261.", norm: "SIA 261", norm-section: "Anhang E", id: "qp0")
  #var("b", 24, "m", domain: ("wind-load", "WL-01"), label: "Longueur du bâtiment", norm: "SIA 261", norm-section: "6.3", id: "b")
  #var("d", 12, "m", domain: ("wind-load", "WL-01"), label: "Largeur du bâtiment", norm: "SIA 261", norm-section: "6.3", id: "d")
  #var("h", 6, "m", domain: ("wind-load", "WL-01"), label: "Hauteur du bâtiment", norm: "SIA 261", norm-section: "6.3", id: "h")
  #var("gelaendekategorie", domain: ("wind-load", "WL-01"), label: "Catégorie de terrain", descr: "La catégorie de terrain détermine la hauteur du gradient et l’exposant de la rugosité du sol du profil du vent.", norm: "SIA 261", norm-section: "Tableau 4", id: "gelaendekategorie")
  #var("zg", "z_g", 450, "m", domain: ("wind-load", "WL-01"), label: "Hauteur du gradient", norm: "SIA 261", norm-section: "Tableau 4", id: "zg")
  #var("alpha_r", 0.23, domain: ("wind-load", "WL-01"), label: "Exposant de la rugosité du sol", norm: "SIA 261", norm-section: "Tableau 4", id: "alpha_r")
  #var("z", 6, "m", domain: ("wind-load", "WL-01"), label: "Hauteur au-dessus du sol", descr: "Hauteur au-dessus du sol pour laquelle la pression dynamique est déterminée ; la norme la fixe au minimum à 5 m (10 m en catégorie de terrain IV).", norm: "SIA 261", norm-section: "6.2.1.2", id: "z")
  #var("ch", "c_h", 0.889126, domain: ("wind-load", "WL-01"), label: "Coefficient pour le profil de répartition du vent", norm: "SIA 261", norm-section: "6.2.1.2", id: "ch")
  #var("cred_bh", "c_(\"red\", \"b/h\")", 0.825473, domain: ("wind-load", "WL-01"), label: "Facteur de réduction b", descr: "Facteur de réduction pour la surface de référence b·h, d’après le rapport de la longueur (b) à la hauteur (h).", norm: "SIA 261", norm-section: "Figur 9", id: "cred_bh")
  #var("cred_dh", "c_(\"red\", \"d/h\")", 0.8754, domain: ("wind-load", "WL-01"), label: "Facteur de réduction d", descr: "Facteur de réduction pour la surface de référence d·h, d’après le rapport de la largeur (d) à la hauteur (h).", norm: "SIA 261", norm-section: "Figur 9", id: "cred_dh")
  #var("cred_max", "c_(\"red\", \"max\")", 0.8754, domain: ("wind-load", "WL-01"), label: "Facteur de réduction en direction oblique du vent", descr: "Pour une direction du vent qui s’écarte de 15° ou plus des directions de référence, le plus défavorable (le plus grand) des deux facteurs de réduction s’applique.", norm: "SIA 261", norm-section: "6.3.3", id: "cred_max")
  #var("cd", "c_d", 1, domain: ("wind-load", "WL-01"), label: "Facteur dynamique", norm: "SIA 261", norm-section: "6.3.5", id: "cd")
  #eq("qp", "q_p", `ch dot qp0`, unit: "kN/m²", label: "Pression dynamique", norm: "SIA 261", norm-section: "6.2 (11)", id: "qp")
  #var("tabelle", domain: ("wind-load", "WL-01"), label: "Tableau des coefficients de pression", descr: "SIA 261, annexe C, tableau 36, h : b : d = 0,5 : 2 : 1.", norm: "SIA 261", norm-section: "Anhang C", id: "tabelle")
  #var("qk_max_cf1", "q_(k,\"max\",\"b·h\")", 0.718536, "kN/m²", domain: ("wind-load", "WL-01"), label: "Force globale du vent maximale, surface de référence b·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_max_cf1")
  #var("qk_min_cf1", "q_(k,\"min\",\"b·h\")", 0, "kN/m²", domain: ("wind-load", "WL-01"), label: "Force globale du vent minimale, surface de référence b·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_min_cf1")
  #var("qk_max_cf2", "q_(k,\"max\",\"0.71·d·h\")", 0.770557, "kN/m²", domain: ("wind-load", "WL-01"), label: "Force globale du vent maximale, surface de référence 0.71·d·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_max_cf2")
  #var("qk_min_cf2", "q_(k,\"min\",\"0.71·d·h\")", 0, "kN/m²", domain: ("wind-load", "WL-01"), label: "Force globale du vent minimale, surface de référence 0.71·d·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_min_cf2")
  #var("qk_max_cf3", "q_(k,\"max\",\"d·b\")", -0.127145, "kN/m²", domain: ("wind-load", "WL-01"), label: "Force globale du vent maximale, surface de référence d·b", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_max_cf3")
  #var("qk_min_cf3", "q_(k,\"min\",\"d·b\")", -0.420557, "kN/m²", domain: ("wind-load", "WL-01"), label: "Force globale du vent minimale, surface de référence d·b", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_min_cf3")

_Forces globales du vent_ <WL-01-table-1-title>
#table(columns: 5, table.header(table.cell(colspan: 2, []), table.cell(colspan: 3, [*Surface de référence*]), [*Force globale du vent [kN]*], [], [*b·h*], [*0.71·d·h*], [*d·b*]), [force globale du vent maximale], [$Q_k =$], [103.5], [39.4], [−36.6], [force globale du vent minimale], [$Q_k =$], [0], [0], [−121.1]) <WL-01-table-1>
$Q_k = q_k dot A_"ref"$ ; $A_"ref"$ = b·h = 144.0 m², 0,71·d·h = 51.1 m², d·b = 288.0 m² (SIA 261, 6.2.3.2). Les valeurs négatives sont des succions. <WL-01-table-1-note>

_Forces locales du vent_ <WL-01-table-2-title>
#table(columns: (auto,) + (1fr,) * 11, table.header([], table.cell(colspan: 11, [*Ouvertures réparties de façon homogène*]), [*$q_k$ [kN/m²]*], [*A*], [*B*], [*C*], [*D*], [*E*], [*F*], [*G*], [*H*], [*m*], [*n*], [*o*]), [*max*], [0.685], [−0.098], [0.734], [−0.147], [0.44], [0.391], [−0.342], [−0.098], [−0.147], [−0.44], [−0.391], [*min*], [−0.293], [−0.44], [−0.391], [−0.44], [−0.538], [−0.293], [−0.88], [−0.636], [−1.174], [−1.271], [−0.978]) <WL-01-table-2>
Valeur la plus grande (max) et la plus petite (min) de $q_k = q_p dot (c_d dot c_"pe" - c_"pi")$ par surface, sur les directions du vent du tableau 36 ; m, n et o sont des surfaces localisées. Les valeurs négatives sont des succions. <WL-01-table-2-note>
]
