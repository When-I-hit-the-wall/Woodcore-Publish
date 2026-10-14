#import "/commands.typ": *

// woodcore:object formula-domain domain
#var-domain("poutre-p1", title: "Poutre P1")[
  #var("q_d", 4.5, "kN/m", label: "Charge linéique de calcul")
  #var("l", 5, "m", label: "Portée")
  #eq("M_d", `q_d * l^2 / 8`, unit: "kNm", label: "Moment de flexion de calcul")
  #var("M_Rd", "M_(R,d)", 20, "kNm", label: "Moment résistant de calcul")
  #verify(`M_d <= M_Rd`)
]
// woodcore:/object domain
