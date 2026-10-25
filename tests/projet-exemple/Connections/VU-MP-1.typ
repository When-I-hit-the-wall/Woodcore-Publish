#import "/000-Typst-Config/commands.typ": *

#domain("VU-MP-1", label: "Anschluss VU-MP-1: Velo Unterstand: Stabdübel 4x 10mm Durchmesser")[
#calc-defaults(presets: "block", scope: "domain") <VU-MP-1-presets>
*E1 (T001), E2 (S001)* <VU-MP-1-member>

  #var("x_c", 0, "mm", domain: ("connection", "VU-MP-1"), label: "Drehpunkt, x", norm: "bauforumstahl, Arbeitshilfe: Tragwerksplanung im Stahlbau – Gelenkige Anschlüsse", id: "x_c")
  #var("z_c", 0, "mm", domain: ("connection", "VU-MP-1"), label: "Drehpunkt, z", norm: "bauforumstahl, Arbeitshilfe: Tragwerksplanung im Stahlbau – Gelenkige Anschlüsse", id: "z_c")
  #var("theta_2", "theta_(1,2)", 90, "°", domain: ("connection", "VU-MP-1"), label: "Winkel von Element 1 zu Element 2", norm: "bauforumstahl, Arbeitshilfe: Tragwerksplanung im Stahlbau – Gelenkige Anschlüsse", id: "theta_2")
  #var("alpha_N", 0, "°", domain: ("connection", "VU-MP-1"), label: "Richtung der Normalkraft", norm: "bauforumstahl, Arbeitshilfe: Tragwerksplanung im Stahlbau – Gelenkige Anschlüsse", id: "alpha_N")
  #var("alpha_V", 90, "°", domain: ("connection", "VU-MP-1"), label: "Richtung der Querkraft", norm: "bauforumstahl, Arbeitshilfe: Tragwerksplanung im Stahlbau – Gelenkige Anschlüsse", id: "alpha_V")
  #var("n", 4, domain: ("connection", "VU-MP-1"), label: "Anzahl Verbindungsmittel", norm: "bauforumstahl, Arbeitshilfe: Tragwerksplanung im Stahlbau – Gelenkige Anschlüsse", id: "n")
  #var("I_px", "I_(p,x)", 14400, "mm²", domain: ("connection", "VU-MP-1"), label: "Polares Flächenträgheitsmoment, Anteil x", norm: "bauforumstahl, Arbeitshilfe: Tragwerksplanung im Stahlbau – Gelenkige Anschlüsse", id: "I_px")
  #var("I_pz", "I_(p,z)", 14400, "mm²", domain: ("connection", "VU-MP-1"), label: "Polares Flächenträgheitsmoment, Anteil z", norm: "bauforumstahl, Arbeitshilfe: Tragwerksplanung im Stahlbau – Gelenkige Anschlüsse", id: "I_pz")
  #eq("I_p", `I_px + I_pz`, unit: "mm²", label: "Polares Flächenträgheitsmoment", norm: "bauforumstahl, Arbeitshilfe: Tragwerksplanung im Stahlbau – Gelenkige Anschlüsse", id: "I_p")

_Lage der Verbindungsmittel_ <VU-MP-1-table-1-title>
#table(columns: 7, table.header([*Nr.*], [*x [mm]*], [*z [mm]*], [*Δx [mm]*], [*Δz [mm]*], [*Δx² [mm²]*], [*Δz² [mm²]*]), [1], [−60], [−60], [−60], [−60], [3600], [3600], [2], [60], [−60], [60], [−60], [3600], [3600], [3], [60], [60], [60], [60], [3600], [3600], [4], [−60], [60], [−60], [60], [3600], [3600], [*Σ*], [], [], [], [], [*14400*], [*14400*]) <VU-MP-1-table-1>
x, z: Koordinaten im Rahmen des Schemas, x nach rechts, z nach unten; Δx, Δz: Abstände zum Drehpunkt. <VU-MP-1-table-1-note>

$N$, $V$, $M$ <VU-MP-1-forces>
  #eq("N", `N_Ed`, unit: "kN", id: "N")
  #eq("V", `V_Ed`, unit: "kN", id: "V")
  #eq("M", `M_Ed`, unit: "kNm", id: "M")

#figure(image-polar-moment("VU-MP-1", N: "N", V: "V", M: "M", width: 60%), kind: image, caption: [Anschluss VU-MP-1: Velo Unterstand: Stabdübel 4x 10mm Durchmesser – Verbindungsmittel und Kräfte je Verbindungsmittel]) <VU-MP-1-polar-figure>

  #eq("N_x", `N dot cos(alpha_N)`, unit: "kN", id: "N_x")
  #eq("N_z", `N dot sin(alpha_N)`, unit: "kN", id: "N_z")
  #eq("V_x", `V dot cos(alpha_V)`, unit: "kN", id: "V_x")
  #eq("V_z", `V dot sin(alpha_V)`, unit: "kN", id: "V_z")
  #var("Delta_x_1", "Delta x_1", -60, "mm", level: 0, id: "Delta_x_1")
  #var("Delta_z_1", "Delta z_1", -60, "mm", level: 0, id: "Delta_z_1")
  #eq("F_x_1", "F_(x,1)", `(N_x + V_x) / n + M dot Delta_z_1 / I_p`, unit: "kN", id: "F_x_1")
  #eq("F_z_1", "F_(z,1)", `(N_z + V_z) / n - M dot Delta_x_1 / I_p`, unit: "kN", id: "F_z_1")
  #eq("F_1", `sqrt(F_x_1^2 + F_z_1^2)`, unit: "kN", id: "F_1")
  #var("Delta_x_2", "Delta x_2", 60, "mm", level: 0, id: "Delta_x_2")
  #var("Delta_z_2", "Delta z_2", -60, "mm", level: 0, id: "Delta_z_2")
  #eq("F_x_2", "F_(x,2)", `(N_x + V_x) / n + M dot Delta_z_2 / I_p`, unit: "kN", id: "F_x_2")
  #eq("F_z_2", "F_(z,2)", `(N_z + V_z) / n - M dot Delta_x_2 / I_p`, unit: "kN", id: "F_z_2")
  #eq("F_2", `sqrt(F_x_2^2 + F_z_2^2)`, unit: "kN", id: "F_2")
  #var("Delta_x_3", "Delta x_3", 60, "mm", level: 0, id: "Delta_x_3")
  #var("Delta_z_3", "Delta z_3", 60, "mm", level: 0, id: "Delta_z_3")
  #eq("F_x_3", "F_(x,3)", `(N_x + V_x) / n + M dot Delta_z_3 / I_p`, unit: "kN", id: "F_x_3")
  #eq("F_z_3", "F_(z,3)", `(N_z + V_z) / n - M dot Delta_x_3 / I_p`, unit: "kN", id: "F_z_3")
  #eq("F_3", `sqrt(F_x_3^2 + F_z_3^2)`, unit: "kN", id: "F_3")
  #var("Delta_x_4", "Delta x_4", -60, "mm", level: 0, id: "Delta_x_4")
  #var("Delta_z_4", "Delta z_4", 60, "mm", level: 0, id: "Delta_z_4")
  #eq("F_x_4", "F_(x,4)", `(N_x + V_x) / n + M dot Delta_z_4 / I_p`, unit: "kN", id: "F_x_4")
  #eq("F_z_4", "F_(z,4)", `(N_z + V_z) / n - M dot Delta_x_4 / I_p`, unit: "kN", id: "F_z_4")
  #eq("F_4", `sqrt(F_x_4^2 + F_z_4^2)`, unit: "kN", id: "F_4")
  #eq("F_max", `max(F_1, F_2, F_3, F_4)`, unit: "kN", id: "F_max")
]
