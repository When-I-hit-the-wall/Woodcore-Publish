#import "/commands.typ": *

#domain("SN-01", label: "Charge de neige – SN-01")[
#calc-defaults(presets: "block", scope: "domain") <SN-01-presets>
#figure(image("/Variable-loads/Snow/SN-01-fig3.svg", width: 80%), caption: [Toit à deux pans, modèles de charge 1 et 2 (SIA 261, figure 3)]) <SN-01-figure-1>

  #var("h_0", 850, "m", domain: ("snow-load", "SN-01"), label: "Altitude", descr: "Altitude du lieu au-dessus du niveau de la mer.", norm: "SIA 261", norm-section: "5.2.6", id: "h_0")
  #var("korrektur", "Delta h", 0, "m", domain: ("snow-load", "SN-01"), label: "Valeur de correction", descr: "Majoration ajoutée à l’altitude du lieu selon SIA 261, annexe D.", norm: "SIA 261", norm-section: "Anhang D", id: "korrektur")
  #eq("h_ref", "h_\"ref\"", `h_0 + korrektur`, unit: "m", label: "Altitude de référence", norm: "SIA 261", norm-section: "5.2.6", id: "h_ref")
  #var("ce", "C_e", 1, domain: ("snow-load", "SN-01"), label: "Coefficient d’exposition", norm: "SIA 261", norm-section: "5.2.4", id: "ce")
  #var("ct", "C_T", 1, domain: ("snow-load", "SN-01"), label: "Coefficient thermique", norm: "SIA 261", norm-section: "5.2.5", id: "ct")
  #var("dachform", domain: ("snow-load", "SN-01"), label: "Forme de la toiture / modèle de charge", norm: "SIA 261", norm-section: "Figur 3", id: "dachform")
  #var("alpha_1", 30, "°", domain: ("snow-load", "SN-01"), label: "Inclinaison de la toiture 1", norm: "SIA 261", norm-section: "Figur 3", id: "alpha_1")
  #var("alpha_2", 30, "°", domain: ("snow-load", "SN-01"), label: "Inclinaison de la toiture 2", norm: "SIA 261", norm-section: "Figur 3", id: "alpha_2")
  #var("abgleiten", domain: ("snow-load", "SN-01"), label: "Glissement de la neige", descr: "Si le glissement est empêché ou rendu difficile, le coefficient de forme de toiture mu_1 est admis à 0.8 (SIA 261, chiffre 5.3.4).", norm: "SIA 261", norm-section: "5.3.4", id: "abgleiten")
  #var("mu_11", 0.8, domain: ("snow-load", "SN-01"), label: "Coefficient de forme de toiture", norm: "SIA 261", norm-section: "Figur 2", id: "mu_11")
  #var("mu_12", 0.8, domain: ("snow-load", "SN-01"), label: "Coefficient de forme de toiture 2", norm: "SIA 261", norm-section: "Figur 2", id: "mu_12")
  #var("s_k", 2.759184, "kN/m²", domain: ("snow-load", "SN-01"), label: "Valeur caractéristique de la charge de neige sur un terrain horizontal", norm: "SIA 261", norm-section: "5.2.6", id: "s_k")
  #eq("q_k11", "q_(k,11)", `mu_11 dot ce dot ct dot s_k`, unit: "kN/m²", label: "Charge de neige caractéristique", norm: "SIA 261", norm-section: "5.2.2", id: "q_k11")
  #eq("q_k12", "q_(k,12)", `mu_12 dot ce dot ct dot s_k`, unit: "kN/m²", label: "Charge de neige caractéristique", norm: "SIA 261", norm-section: "5.2.2", id: "q_k12")
  #eq("q_k11h", "q_(k,11,2)", `mu_11 / 2 dot ce dot ct dot s_k`, unit: "kN/m²", label: "Charge de neige caractéristique, modèle de charge 2", norm: "SIA 261", norm-section: "5.2.2", id: "q_k11h")
  #eq("q_k12h", "q_(k,12,2)", `mu_12 / 2 dot ce dot ct dot s_k`, unit: "kN/m²", label: "Charge de neige caractéristique, modèle de charge 2", norm: "SIA 261", norm-section: "5.2.2", id: "q_k12h")
]