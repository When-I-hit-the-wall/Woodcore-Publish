#import "/000-Typst-Config/commands.typ": *

#domain("dreigelenk", label: "Horizontalkraft im Dreigelenkrahmen")[
#calc-defaults(presets: "block", scope: "domain") <dreigelenk-presets>

  #var("H_d", "H_\"d\"", 14.4, "kN", domain: ("script", "dreigelenk"), label: "Horizontalkraft am Fusspunkt", descr: "Dreigelenkrahmen unter Gleichlast, H = q L² / (8 f)", id: "H_d")
  #var("V_d", "V_\"d\"", 19.2, "kN", domain: ("script", "dreigelenk"), label: "Vertikalkraft am Fusspunkt", id: "V_d")
]
