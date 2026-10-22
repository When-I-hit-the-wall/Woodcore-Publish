#import "/000-Typst-Config/commands.typ": *

#domain("SL", label: "Schneelast – SL")[
#calc-defaults(presets: "block", scope: "domain") <SL-presets>

  #var("h_0", 551.767944, "m", domain: ("snow-load", "SL"), label: "Höhe ü. NN", descr: "Höhe des Standorts über Meer.", norm: "SIA 261", norm-section: "5.2.6", id: "h_0")
  #var("korrektur", "Delta h", 0, "m", domain: ("snow-load", "SL"), label: "Korrektur Wert", descr: "Höhenzuschlag auf die Höhe ü. NN nach SIA 261, Anhang D.", norm: "SIA 261", norm-section: "Anhang D", id: "korrektur")
  #eq("h_ref", "h_\"ref\"", `h_0 + korrektur`, unit: "m", label: "Bezugshöhe", norm: "SIA 261", norm-section: "5.2.6", id: "h_ref")
  #var("ce", "C_e", 1, domain: ("snow-load", "SL"), label: "Expositionsbeiwert", norm: "SIA 261", norm-section: "5.2.4", id: "ce")
  #var("ct", "C_T", 1, domain: ("snow-load", "SL"), label: "Thermischer Beiwert", norm: "SIA 261", norm-section: "5.2.5", id: "ct")
  #var("dachform", domain: ("snow-load", "SL"), label: "Dachform / Lastmodell", norm: "SIA 261", norm-section: "Figur 3", id: "dachform")
  #var("L", 17.5, "m", domain: ("snow-load", "SL"), label: "Gebäudelänge", norm: "SIA 261", norm-section: "5.3.5", id: "L")
  #var("B", 4.25, "m", domain: ("snow-load", "SL"), label: "Gebäudebreite", norm: "SIA 261", norm-section: "5.3.5", id: "B")
  #var("abgleiten", domain: ("snow-load", "SL"), label: "Abgleiten des Schnees", descr: "Ist das Abgleiten behindert oder erschwert, wird der Dachformbeiwert mu_1 mit 0.8 angesetzt (SIA 261, Ziffer 5.3.4).", norm: "SIA 261", norm-section: "5.3.4", id: "abgleiten")
  #var("mu_1", 0.8, domain: ("snow-load", "SL"), label: "Dachformbeiwert", norm: "SIA 261", norm-section: "Figur 2", id: "mu_1")
  #var("s_k", 1.394115, "kN/m²", domain: ("snow-load", "SL"), label: "Charakteristischer Wert der Schneelast auf horizontalem Gelände", norm: "SIA 261", norm-section: "5.2.6", id: "s_k")
  #eq("q_k1", "q_k", `mu_1 dot ce dot ct dot s_k`, unit: "kN/m²", label: "Charakteristische Schneelast", norm: "SIA 261", norm-section: "5.2.2", id: "q_k1")
]
