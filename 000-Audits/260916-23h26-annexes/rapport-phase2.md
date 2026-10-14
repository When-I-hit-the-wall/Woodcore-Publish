# Audit 260916-2326 — Phase 2 : les calculs contre les classeurs de référence vérifiés

Agent « p2 ». Bac à sable `AUDIT/projet-phase2/`, scripts et résultats bruts dans `AUDIT/p2/`. Commit audité `997570db`. Travail interrompu à 23 h 52 par la limite de session de l'API et repris le 17.09.2026 : aucune instance EXCEL.EXE lancée par l'agent ne tournait à la reprise (`tasklist` vide), et aucune n'est restée après chaque balayage (chaque script imprime `excel pids after: set()`).

`git -C <projet réel> status --short` : **vide** en début et en fin de phase. Rien n'a été écrit dans l'arbre réel. Les classeurs ont été ouverts uniquement en copie (`projet-phase2/ref/`, copie du dossier `201-excelTools`), avec `Workbooks.Add(copie)`, macros désactivées (`AutomationSecurity = 3`), fermés sans enregistrer. Pour les charges seulement, une copie recalculée a été écrite **dans le bac à sable** par `SaveCopyAs` (`projet-phase2/loads/*.xlsm`), le modèle n'étant jamais enregistré : c'est le seul moyen de faire lire un classeur recalculé par `snow.py`/`dead_load.py`, qui lisent les valeurs en cache avec openpyxl.

## Bilan chiffré

| Niveau | Classeur | Cas | Grandeurs comparées | Conformes | Écarts | dont nouveaux |
|---|---|---|---|---|---|---|
| 2.2 A | Stabdübel (HH + SH) et `Verbindung.xlsm` (HH) via l'export | 3 | 102 | 101 | 1 | 1 (K_ser,Verb, FK 2) |
| 2.2 A | Biegesteifer Anschluss 1.0 via l'export | 1 | 6 | 6 | 0 | 0 |
| 2.2 A | `Belastungsannahmen.xlsm` du projet (EL+AL, SL) | 5 feuilles | 16 | 16 | 0 | 0 |
| 2.3 B | Stabdübel, Excel COM | 62 (59 calculés, 3 refus attendus) | 2008 | 1965 | 43 | 22 (K_ser,Verb) |
| 2.3 B | Biegesteifer Anschluss 1.0, Excel COM | 29 | 1310 | 1261 | 49 | 6 (angle force-fil) |
| 2.3 B | Belastungsannahmen, neige | 20 (16 lus, 4 refus LM2 connus) | 188 (dont 64 formules imprimées réévaluées) | 188 | 0 | 0 |
| 2.3 B | Belastungsannahmen, charges permanentes | 5 feuilles, 56 couches | 127 | 125 | 2 | 2 (ligne sans matériau) |
| 2.4 C | sondes Typst | 17 compilations | 123 valeurs imprimées (+ 2 refus avec leur raison) | 123 | 0 | 0 |
| 2.4.4 | valeurs normatives tirées au sort | 10 | 10 | 10 | 0 | — |

Contrôles menés : 37 (inventaire 1, journaux 4, correspondance 1, niveau A 3 classeurs, niveau B 4 balayages, conversion de repère 1, niveau C 17 compilations, 10 valeurs normatives regroupées en 1 contrôle, vérifications de norme 5). Constats : **A 5**, **B 4**, **C 6**, **NON FAIT 2**.

## 2.1 Inventaire et correspondance

Premier audit : aucune liste précédente, donc aucun « nouveau modèle » ni « version changée » par rapport à un audit antérieur. Inventaire (version tirée du nom de fichier, feuilles lues dans `xl/workbook.xml`) : 27 modèles `.xltx`/`.xltm` et un raccourci `.lnk` (Erdbeben…, pas un modèle), tous suivis par Git. Détail complet dans `p2/inventory.json`.

Journaux lus pour les modèles que le projet reproduit :

- `«dowel connections» template`, feuille `VERSIONEN INDEX` : dernière entrée 1.62 « Korrektur fu für S355 » (27.02.2023). `Verbindung.xlsm` et `Verbindungen.xlsx` portent exactement le même index 1.62. Les formules des feuilles `Stabdübel (Holz-Holz)` et `(Stahl-Holz)` de `Verbindung.xlsm` sont identiques à celles du modèle, cellule par cellule (diff des dumps `tpl_hh.txt`/`vb_hh.txt`, `tpl_sh.txt`/`vb_sh.txt`) ; seules les **entrées** de la feuille Holz-Holz diffèrent (voir AUD-2-7).
- `«rigid connection» template`, `Änderungsjournal` : 1 « go life » (24.02.2022).
- `«R_k to R_d» template` : 1.0 « Erstellt » (05.07.2023).
- `«load workbook» template`, `Änderungsjournal` : **3.2 « Korrektur Wind: Globale Windlast "L70" Formelfehler behoben » (01.09.2026)**. Le classeur du projet `Belastungsannahmen.xlsm` s'arrête à 3.1. Ce changement touche un calcul que le projet reproduit (wind.py lit L70) : voir AUD-2-1.

Correspondance reconstruite à partir du code (`registry.DOMAIN_MODULES`, `connector.MODULES`, `grep gamma_m`) :

| Classeur | Feuilles | Module Python | Commande Typst |
|---|---|---|---|
| Stabdübel et `Verbindung.xlsm` | `Stabdübel (Holz-Holz)`, `(Stahl-Holz)`, `Daten` | `domains/dowel.py` via `connector.MODULES = {"Stabdübel": dowel}` ; `norms/sia265.py` | `show-connector-resistance`, `show-calc("connector", …)` |
| Biegesteifer Anschluss 1.0 | `Biegesteifer Anschluss` | `domains/connection.py` (`analyse`, `fastener_forces`, `grain_angle`) | `show-polar-moment` (calcule en Typst) |
| Belastungsannahmen | `Schnee`, `Wind`, `Flachdach`, `Steildach`, `Innenwand`, `Aussenwand`, `Decke Innen-Innen`, `Material (hier ergänzen)`, `Dropdowns` | `domains/snow.py`, `wind.py`, `dead_load.py` (`registry.DOMAIN_MODULES = (dead_load, snow, wind, live_load)`) | `show-calc("snow-load" / "wind-load" / "dead-load", …)` |
| Rk zu Rd Rechner 1.0 | `Berechnung` | **aucun** (voir AUD-2-9) | — |
| les 23 autres | — | aucun | — |

Non couverts (classe C, AUD-2-13) : Bemessung Wand- und Deckenscheiben 2.0, Brandfall Biegung 1.5, Brandfall Knicken 4J1, Brandwiderstand Stahlprofil 1.2, Ersatzstab Holzrahmenwand 1.0, Anschlüsse mit Querzug 1.1, Auflagerlatte 2.0, Ausklinkung 1.02, Deckenbemessung Einfeld 7.02, Durchbrüche 1.7, Hohlkastenträger 5.34, Klammern 0.0 (TESTVERSION), Brettsperrholz 2.32, Nagelverbindungen 1.02, Rk zu Rd 1.0, Schwalbenschwanz 1.0, Stabilität Rechteck 3.12, Stabilität Rund 1.1, Steifigkeit Tafelbauwand 1.2, Steildach Sparren 2.0, Vorbemessung Unterzüge 1.9, Kategorisierung Erdbeben 1.01, Brandabschnitt Lignum 3.1 1.2, Verteilung Wind/Erdbeben 2.3. Aucun module nouveau (pas de `nail.py`, bouton *Vis* toujours inactif).

## 2.2 Niveau A — l'exemple enregistré

### Stabdübel

Sources écrites dans le bac à sable (`p2/levelA_sources.py`) : `connectors/AUD-HH1.json` (exemple Holz-Holz du modèle : GL24h/GL24h, d = 14, zweischnittig, t = 70/100, n_tot = 8, n = 4, a₁ = 100, FK 1) et `AUD-SH1.json` (exemple Stahl-Holz du modèle : GL24h, d = 12, α = 90°, 2 tôles en fente de 12 mm dans 200 mm, 9 broches, n = 3, a₁ = 60), sur le schéma `VU-Skizze` avec `n_tot.override`, plus la source existante `VU-SD-10`, qui est exactement le cas enregistré aujourd'hui dans `Verbindung.xlsm` (C24/C24, d = 10, FK 2, t = 50/100, 4 broches, n = 2, a₁ = 120). Export complet `calc/export_all.py` du bac à sable (code 0), puis comparaison des valeurs en cache d'Excel (openpyxl `data_only`) avec `data/connectors.json` (`p2/levelA_compare.py`, sortie `p2/levelA.txt`) : f_h,0,k, f_h,90,k, f_h,α,k par pièce, ρ_k, β_f, t_1,1, t_1,2, t_2,2, k_β,1, k_β,2, k_β, p, p·k_β, M_u,k, n_quer, k_red par pièce, η_w, η_t, R_d, R_d,Verb, R_d,Verb,Fachwerk, les six distances de Tabelle 24, les deux longueurs minimales, K_ser par pièce et K_ser,Verb.

Résultat : **101/102 conformes** à 1·10⁻⁶ près. Le seul écart : `VU-SD-10`, K_ser,Verb = 22 503,251 N/mm (`Verbindung.xlsm` C62) contre 20 252,926 N/mm exporté, rapport 0,9 = η_w rigidité de la FK 2 (AUD-2-3).

### Biegesteifer Anschluss — conversion de repère établie d'abord

Le classeur : x vers la droite, **y vers le haut** (broche 1 « unten links », y = 84·(rangée − 1)), F_Ed,x positive vers la droite, **F_Ed,y positive vers le bas** (colonne AB = −F_Ed,y/n dans le repère y-haut), **M_Ed positif horaire** (Y = M/I_p·Δy, AA = −M/I_p·Δx). Le projet (§3.3quinquies) : x à droite, z vers le bas, angles de x vers z, M positif tournant z vers x (antihoraire sur le dessin).

Conversion retenue et vérifiée : **z = −y ; N = F_Ed,x à 0° ; V = F_Ed,y à 90° ; M_projet = −M_Ed ; F_z(projet) = −(AA + AB)** ; fil du bois pour un angle α du classeur (grille avançant selon (sin α, cos α) en y-haut) : axe de la pièce à α − 90° dans le repère du projet.

| Cas élémentaire (groupe 3 × 4, h = 220, a₂,Rand = 48, a₁ = 84) | Grandeurs | Résultat |
|---|---|---|
| F_Ed,x = 10 seul | n, Σ Δx², Σ Δy², x_s, y_s, F_i, F_x,i, F_z,i (12 broches), F_max, α, numéro | 44/44 conformes |
| F_Ed,y = 10 seul | idem | 44/44 |
| M_Ed = 10 seul | idem | 44/44 |
| −F_Ed,x, −F_Ed,y, −M_Ed | idem | 3 × 44/44 |
| contre-épreuve : M sans changement de signe | idem | 24/44 : 20 composantes fausses, normes et F_max égales : le signe de M est bien inversé |

Niveau A avec l'export : `connections/AUD-MP1.json` sur `details/AUD-GRID.json` (les 12 broches de l'exemple aux coordonnées converties) : n = 12, Σ Δx² = 30 752 (W108), Σ Δy² = 105 840 (X108), I_p = 136 592, x_s = 110 (AE8), y_s = 126 = −z_c (AF8) : **6/6 conformes**. Les forces de ce cas (F_max = 12,535 kN, broche n° 12, α = 60,3°) sont comparées au niveau C, `show-polar-moment` calculant en Typst.

### Charges

Le modèle `«load workbook» template` n'enregistre **aucun exemple** (altitude, exposition et modèle de charge vides : H12, H14, H17, I37 valent `#N/A` ; couches sans matériau). Le niveau A a donc été mené sur le classeur du projet, instance du modèle en 3.1 : g_k, a_k et g_k + a_k des quatre feuilles `EL+AL-*` (Python calcule) contre J27/J28/J29 de chaque feuille, et h_ref, s_k, μ₁₁, q_k,11 de `SL` : **16/16 conformes**. « NON FAIT » partiel : exemple du modèle absent (NF-1).

### Écarts connus — sont-ils toujours les seuls ?

- t₂,ᵢ Holz-Holz einschnittig : **confirmé**, et seulement lui dans sa famille. La norme (SIA 265:2021 p. 95, rendu `p2/tab45-095.png`) écrit l'éq. (125) avec (√(1/(1+β_f)) + 1) pour le Seitenholz t₂ ; le classeur (O34/P34) garde √(β_f/(1+β_f)). Sur 5 cas β_f ≠ 1 : écart de 2,7 % à 8,2 % sur t_2,1 et t_2,2, et 2,5 % sur k_β,2 dans un cas ; k_β et R_d restent égaux dans les 5 cas (la pièce 1 gouverne).
- k_red = 1 pour n = 1 (Tabelle 21) : **confirmé**. Avec a₁ vide la feuille Holz-Holz donne k_red = 0 et **R_d = 0** (C33 = (0/(10d))^¼) ; la feuille Stahl-Holz est protégée (C31). Tabelle 21 p. 63 donne 1,0 dans la colonne n = 1.
- Conditions (130)/(131) : **inexact tel que documenté** — le classeur les impose par une validation de données sur C20, voir AUD-2-5.
- η_w de la classe des positions : non observé dans les balayages (même classe des deux côtés) ; les résistances coïncident en FK 2 et 3.
- **Deux écarts nouveaux** : K_ser,Verb sans η_w dans le classeur (AUD-2-3), et l'angle force-fil du classeur Biegesteifer pour α ≠ 0 (AUD-2-4). Chacun tranché contre la norme ou la géométrie : Python est juste dans les deux cas.

## 2.3 Niveau B — balayages recalculés par Excel

Excel 16 par COM (`win32com`, `DispatchEx`, instance dédiée), entrées trouvées par leur libellé en colonne A (ou D pour les charges), `CalculateFull`, sorties lues par libellé ou dans les blocs dont l'en-tête est trouvé par libellé. Python : le `calc/` du bac à sable, source de connecteur construite par cas, `check_source` puis `build_record` (le chemin de l'export). Tolérance relative 1·10⁻⁶.

### Stabdübel (`p2/sweep_dowel.py`, `sweep_dowel.json`, `sweep_dowel_hh2.json`, synthèse `analyse_dowel.txt`)

62 cas : 35 Holz-Holz (C24, C30, GL24c, GL24h, GL28h, GL32h, D30 ; d = 6, 8, 10, 12, 14, 16 ; α = 0, 30, 45, 60, 90 ; prépercé, non prépercé, mixte ; FK 1, 2, 3 ; einschnittig et zweischnittig ; n = 1 à 6 ; a₁ = 5d à 10d ; β_f ≠ 1 par classes, par angles et par prépercage ; épaisseurs sous t_1,1 et au plateau ; séisme ; f_u,k 400 et 600) et 27 Stahl-Holz (1, 2 et 3 tôles en fente, tôles extérieures ; t₁/t₂ = 0,3, 0,35, 0,4, 0,45, 0,5, 0,6, 0,8 ; n = 1 ; broche unique ; feuillu ; séisme). Le premier passage lisait les f_h,0/f_h,90 de la pièce 2 deux lignes trop bas (défaut du harnais, corrigé : lignes trouvées par les libellés « Nadelholz »/« Laubholz » de la colonne J) ; les 35 cas Holz-Holz ont été recalculés.

Résultat : 59 calculés, **2008 grandeurs, 1965 conformes, 43 écarts**, tous classés ; 3 refus attendus (feuillu non prépercé : Python refuse avec « Laubholz must be predrilled -- SIA 265 Tabelle 22 gives no value… », le classeur donne un nombre et affiche seulement « Bei Laubholz muss vorgebohrt werden » en E24/D39 ; la norme, Tabelle 22 p. 64, n'a pas de ligne feuillu non prépercé : Python est conforme).

| Grandeur | Cas | Excel | Python | Écart | Verdict |
|---|---|---|---|---|---|
| K_ser,Verb | 22 cas en FK 2 ou 3 (ex. n° 3 = VU-SD-10) | 22 503,251 | 20 252,926 | −10 % (FK 2), −25 % (FK 3) | **nouveau** : SIA 265 3.2.1.3 et titre de Tab. 25 « für Feuchteklasse 1 » → Python conforme, classeur sans η_w (AUD-2-3) |
| k_red,1, k_red,2, R_d, R_d,Verb, R_d,Fachwerk | n° 14 (HH zweischnittig, n = 1) | 0 ; 0 ; 0 kN | 1 ; 1 ; 4,183 kN | — | connu, Tabelle 21 |
| idem | n° 15 (einschnittig, n = 1) | 0 ; R_d,Verb 0 | 1 ; 12,884 kN | — | connu |
| t_2,1, t_2,2 | n° 20 (C24/D30 einschnittig) | 20,833 ; 59,659 mm | 19,128 ; 54,774 mm | 8,2 % | connu, éq. (125) |
| t_2,1, t_2,2, k_β,2 | n° 17 (prépercé mixte) | 29,079 ; 83,273 ; 1,4964 | 27,027 ; 77,394 ; 1,5334 | 7,1 % ; 2,5 % | connu, éq. (125) |
| t_2,1, t_2,2 | n° 22, 24, 32 | — | — | 2,7 % ; 5,6 % ; 6,0 % | connu, éq. (125) |

Cas hors validation du classeur (Stahl-Holz C20 limité à 0,35…0,5) : n° 42 (0,6), 43 (0,8), 44 (0,3) — notés, comparés quand même : conformes hormis K_ser,Verb du n° 42 (FK 2) ; Python y émet bien les avertissements (130)/(131).

### Biegesteifer Anschluss (`p2/sweep_polar.py`, `sweep_polar.json`, `sweep_polar_extra.json`)

29 cas : 8 élémentaires (dont 2 contre-épreuves), groupes 1 × 4, 4 × 1, 2 × 2, 3 × 4, 4 × 3, 2 × 5, 5 × 2, 1 × 1 (sans et avec moment), 10 × 10, signes mélangés, α = 15, 20, 30, 45, 60, 70, 80, 90. Comparés : n, Σ Δx², Σ Δy², centre, F_i, F_x,i, F_z,i de chaque broche, F_max, numéro du connecteur déterminant, angle force-fil du déterminant.

**1310 grandeurs, 1261 conformes, 49 écarts** : 20 dans la contre-épreuve voulue (n° 7), 23 dans les deux groupes à une seule file (n° 10, 17) où le classeur est en `#DIV/0!` (AUD-2-10 ; Python : F_max 8,757 kN et 5 kN ; 1 × 1 avec moment : Python refuse « I_p = 0 », classeur en erreur), et 6 angles force-fil pour α ≠ 0 (AUD-2-4). Numéro déterminant : conforme dans tous les cas calculables.

| Cas | α | F (y vers le haut) au déterminant | Classeur C50 | Python | Angle correct (grille du classeur) |
|---|---|---|---|---|---|
| n° 20 | 30° | (9,098 ; −10,832) | 10,03° | 70,03° | 70,03° |
| n° 21 | 45° | (−3,657 ; 12,230) | 28,35° | 61,65° | 61,65° |
| n° 22 | 60° | (−5,833 ; 2,882) | 3,71° | 56,30° | 56,30° |
| n° 26 | 15° | (−9,872 ; 16,437) | 15,99° | 45,99° | 45,99° |
| n° 27 | 80° | (−7,314 ; 2,129) | 6,23° | 26,23° | 26,23° |
| n° 29 | 30° | F_Ed,x = 10, F_Ed,y = 10 (bas), M = 0 : (0,833 ; −0,833) | 15,00° | 75,00° | 75,00° |
| n° 28 (témoin) | 30° | F_Ed,x = 10, F_Ed,y = −10, M = 0 : (0,833 ; 0,833) | 15,00° | 15,00° | 15,00° |

### Neige (`p2/sweep_loads.py`, `sweep_loads.json`)

Modèle 3.2, feuille `Schnee` renommée `SL-Schnee`, feuilles de vent et annexes supprimées de la copie avant `SaveCopyAs`. 20 cas : les cinq modèles de `Dropdowns!I44:I48` × altitudes 300 m (plancher 0,9 kN/m² actif) et 1450 m × Abgleiten « möglich » / « behindert oder erschwert ». 16 lus : **188/188 conformes**, dont 64 formules imprimées (h_ref, s_k avec son plancher, q_k,11, q_k,12, q_k,2m) réévaluées avec les valeurs imprimées à côté et égales au résultat. 4 refusés (GiebeldachLM2) : « N37: load model 'GiebeldachLM2' also computes a characteristic load here, which this exporter does not read yet » — point ouvert connu du §14 (AUD-2-11).

### Charges permanentes

Les cinq feuilles de couches du modèle renommées `EL+AL-*`, remplies depuis la bibliothèque du modèle (236 lignes) : 56 couches, matériaux en kg/m² (PV-Anlage, Blech, Ampack, Profilblech, Flammex) et en kg/m³, dont « Gartenplatten » (listé sous deux Ebene à 2200 et 2000 kg/m³, pris sous « Beschichtung »). Poids et charge de chaque couche : conformes ; g_k, a_k : **125/127**. Écart : `EL+AL-Decke` a_k Excel 5,9816 contre Python 5,4816 kN/m² (−0,5), g_k + a_k 6,9716 contre 6,4716 : ligne 20 « Installationen und Innenwände » dont la charge 0,5 est **saisie directement en K20 sans matériau** ; Python saute la ligne (AUD-2-2).

## 2.4 Niveau C — ce que Typst imprime (`p2/levelC.py`, `levelC.json`)

Sondes `projet-phase2/000-TypstRapport/.probe-audit/<pid>/*.typ`, `#import "/commands.typ": *`, compilées avec `--root <bac>/000-TypstRapport`, texte extrait par pypdf puis normalisé NFKC (les résultats sont en chiffres mathématiques gras Unicode : sans NFKC ils paraissent absents, défaut du harnais corrigé), nombres formatés comme `fmt-decimals`.

- `show-connector-resistance(…, level: 3)` et `level: 1` pour AUD-HH1, AUD-SH1, AUD-N1, AUD-130, AUD-SP (sous Tabelle 24, d = 20 sur 120 mm), VU-SD-10 : 6 compilations sans avertissement ; R_d, R_d,Verb, R_d,Fachwerk, k_β, p·k_β, k_red, M_u,k, f_h,1,k, β_f, η_w, K_ser,Verb imprimés et égaux à l'export (ex. AUD-HH1 : 11.627, 93.014, 69.76 kN ; AUD-SH1 : 21.077, 189.697 kN, égaux au modèle) ; l'avertissement (130) et celui de Tabelle 24 sont imprimés.
- `show-calc("connector", "AUD-HH1", level: 3)` : les 36 variables numériques imprimées.
- Cas refusé AUD-REF : `show-connector-resistance` et `show-calc` arrêtent la compilation avec la **raison** (« connector 'AUD-REF' carries no calculation -- f_h,k: Laubholz must be predrilled -- SIA 265 Tabelle 22 gives no value for it without predrilling »), aucun nombre imprimé ; `show-connector` imprime la ligne descriptive.
- `show-polar-moment("AUD-MP1", N: 20, V: 20, M: -10, level: 3)` : F_max imprimé **12.535** = `connection.fastener_forces()` 12,535140666 = Excel C49 12,535140666 ; « Verbindungsmittel 12 » = E49 ; I_p imprimé. Second jeu (N = 15, V = −25, M = −6) : 8.315 = Python = Excel 8,314904614, broche 10. `VU-MP-1` compile.
- `show-calc` niveau 3 : `snow-load/SL` (h_ref 551.768, s_k 1.394, q_k,11 1.115) et trois `dead-load` (g_k, a_k, choisi) : toutes les variables numériques imprimées.

### 2.4.4 Valeurs normatives (graine 20260916, population 437 valeurs numériques dans 23 fichiers, `p2/norm_sample.py`)

| Fichier | Valeur | Page (PDF DE) | Verdict |
|---|---|---|---|
| sia265-2021-tab09 GL28c f_c,90,d mit Vorholz (Klammer) | 4,3 | p. 27 « 2,7 (4,3) » | conforme |
| sia261-2020-tab08 H Q_k | 1 | p. 37 « 0,4 1 1) » | conforme (source sans page, AUD-2-8) |
| sia265-2021-tab09 GL28h f_m,d | 18,7 | p. 27 | conforme |
| sia265-2021-6.1.4.2 k_red n = 1 | 1,0 | p. 63, Tabelle 21 | conforme |
| sia261-2020-tab30 Kiessand gemischt | 20 | p. 78 | conforme |
| sia265-2021-tab09 GL24h G_mean | 650 | p. 27 | conforme |
| sia261-2020-tab28 Natursteine | 30 | p. 77 | conforme |
| sia265-2021-2.2.6 η_t stossartig | 1,4 | p. 19 | conforme |
| sia265-2021-tab08 C30 f_t,90,d | 0,1 | p. 25 | conforme |
| sia261-2020-tab30 Pflanzenöl | 9,5 | p. 78 | conforme |

Vérifications de norme annexes : Tabelle 4 p. 22 (η_w rigidité 0,90/0,75), 6.2.1.4 et Tabelle 25 p. 66 (« für Feuchteklasse 1 »), Tabelle 24 p. 66, Tabelle 45 p. 95 (rendu), A.1.1 p. 94 (la coquille « p_B·k_β1 » est bien dans la norme).

## Constats

**AUD-2-1 | B | `Belastungsannahmen.xlsm` feuilles `WL-Velo`, `WL-Fluchttreppe+Geräte`, `WL-Pavillon`, cellule L70 (et CLAUDE.md §3.3quater)** — Le modèle de référence (01.09.2026) corrige la formule L70 : `=J17*1*MIN(S78:S81)*J60` ; le classeur du projet (3.1) garde `=J19*1*MIN(S79:S81)*J60` et le rapport imprime q_k,min pour d·b = −0.34 / −0.3956 / −0.34 kN/m² au lieu de −0.266 / −0.3059 / −0.266 kN/m² (valeurs recalculées sur les caches J17 = 0,6650, S78:S81, J60 = 1). Preuve : `openpyxl` sur `projet-phase2/Belastungsannahmen.xlsm` et `ref/«load workbook» template` (`Wind!L70`, `K70`, `J70`). Options : (1) l'ingénieur reporte dans Excel la formule 3.2 dans les trois feuilles WL puis *Importer Excel* ; (2) mettre à jour le classeur entier en 3.2. Dans les deux cas, réécrire la phrase du §3.3quater « It is the template's defect » : le défaut est corrigé dans le modèle 3.2 et reste dans le classeur du projet (classe A une fois la décision prise).

**AUD-2-2 | B | `calc/domains/dead_load.py:170` (`if not r["material"]: continue`)** — Une charge saisie directement dans la colonne K d'une ligne sans matériau est ignorée : le modèle 3.2 (et la feuille non préfixée `Decke Innen-Innen` du projet) porte en ligne 20 « Installationen und Innenwände », type ak, K20 = 0,5 kN/m² saisi. Renommée `EL+AL-Decke`, Python imprime a_k = 5,4816 au lieu de 5,9816 et g_k + a_k = 6,4716 au lieu de 6,9716 (Excel J25/J26), sans avertissement ; le contrôle du « Gewählt » compare alors le choix à la somme incomplète, donc accepterait un choix sous la somme de la feuille. Le §3.3ter dit « rows with an empty Material cell are skipped, exactly as the sheet's own IF(E="", "", ...) does », mais cette ligne n'a pas de formule en K. Preuve : `p2/sweep_loads.py`, `sweep_loads.json` (dead → EL+AL-Decke) ; dump `p2/decke.txt` (K20 = 0.5, K22 = SUM(K8:K20)). Aucune feuille `EL+AL-*` actuelle du projet n'est touchée (balayage de toutes les feuilles : seule `Decke Innen-Innen` porte un K saisi). Options : (a) lire une telle ligne comme une couche de charge fixe (poids « — », charge = K) ; (b) refuser l'export en nommant la cellule ; (c) documenter la limite. Test proposé : fixture `tests/fixtures/workbook.py` avec une ligne sans matériau et K = 0,5, qui doit être comptée (a) ou refusée (b).

**AUD-2-3 | B | `calc/domains/dowel.py:463-469` (`_stiffness`) contre modèle C62 (Holz-Holz) et C66 (Stahl-Holz)** — Nouvel écart : K_ser,Verb Python = K_ser·n_tot·p·η_w(rigidité) ; le classeur n'applique aucun η_w. 22 des 59 cas calculés (tous ceux en FK 2 ou 3) : −10 % en FK 2, −25 % en FK 3, y compris l'exemple de `Verbindung.xlsm` (C62 = 22 503,251 ; export `VU-SD-10` 20 252,926). La norme donne raison à Python : SIA 265 3.2.1.3 (η_w convertit « die Tragwiderstände und die Steifigkeitswerte » de la FK 1 aux FK 2 et 3, Tabelle 4 p. 22 : 0,90/0,75) et Tabelle 25 p. 66 est « für Feuchteklasse 1 ». Décision : (1) l'inscrire comme écart connu au §3.3nonies et au §2.2 de `prompt-audit.md`, avec un test figé (valeur Excel × 0,9) ; (2) le signaler au responsable du modèle de référence.

**AUD-2-4 | B | `«rigid connection» template`, colonne AH (`=ABS(ATAN((Y+Z)/(AA+AB))*180/PI())`) et C50 (`=ABS(… − C12)`)** — Nouvel écart, côté classeur : l'angle force-fil du connecteur déterminant est calculé sur l'angle **non signé** de la force, puis diminué de α ; pour α ≠ 0 et une force penchée à l'opposé du fil (F_x/F_y < 0 en y-haut) il est faux par rapport à la grille que le classeur dessine lui-même (rangées selon (sin α, cos α)) : α = 30°, F_Ed,x = 10, F_Ed,y = 10 vers le bas → classeur 15°, géométrie 75°, Python (`connection.grain_angle`) 75° ; 6 des 10 cas à α ≠ 0, table ci-dessus (les 4 autres : α = 90°, force parallèle à un axe, ou force penchée du côté du fil). Le projet est juste ; aucun nombre imprimé du projet n'est touché. Options : signaler au responsable du modèle (formule signée, par ex. `ATAN2`), inscrire l'écart comme connu dans `prompt-audit.md` §2.2 pour les audits suivants.

**AUD-2-5 | A | CLAUDE.md §3.3nonies (« And one the norm states and the workbook never checks: … (130) and (131) »), `calc/domains/dowel.py:14`, `tests/test_dowel.py:303`, `prompt-audit.md` §2.2 (« les conditions des éq. (130)/(131), que le classeur ne vérifie pas »)** — Le classeur Stahl-Holz limite l'entrée t₁/t₂ (C20) à `decimal between 0.35 and 0.5` (validation de données, `openpyxl` : `C20 decimal 0.35 0.5`), soit exactement (131) t₁ ≥ 0,35·t₂ et (130) t₂ ≥ 2·t₁ ; par COM, `Validation.Value` est faux pour 0,3, 0,6 et 0,8 et vrai pour 0,35 à 0,5. Correction : remplacer par « the workbook enforces them only as the data validation of C20 (0.35 ≤ t₁/t₂ ≤ 0.5), which a pasted or typed-over value bypasses and which says nothing of which equation it guards; here they are checked and reported ». Pas de nombre changé ; pas de test nécessaire (documentation).

**AUD-2-6 | A | `calc/domains/dowel.py:13`** — Le docstring du module dit « Tabelle 45 equations (126)/(127) use sqrt(1/(1+beta_f)) » ; la norme p. 95 place ce crochet à l'**éq. (125)** (Seitenholz t₂, einschnittig), (126)/(127) étant la forme « Für β_f = 1 ». Correction : remplacer `Tabelle 45 equations (126)/(127) use` par `Tabelle 45 equation (125) uses` ; les autres mentions ((125) dans `_timber_corners` et `tests/test_dowel.py`) sont justes.

**AUD-2-7 | A | `tests/test_dowel.py:5, 41, 59, 82` et CLAUDE.md §3.3nonies (« Both of its sheets are reproduced to the last printed digit by tests/test_dowel.py »)** — Les valeurs figées du test (GL24h/GL24h, d = 14, 8 broches ; C25 = 27.1502, C44 = 93.0136) ne sont plus celles de `Verbindung.xlsm` commité, dont la feuille Holz-Holz porte le cas `VU-SD-10` (C24, d = 10, FK 2 : C25 = 25.83, C44 = 22.9048) ; elles sont celles du modèle `«dowel connections» template` (formules identiques cellule par cellule). La feuille Stahl-Holz est inchangée. Preuve : `diff p2/tpl_hh.txt p2/vb_hh.txt`. Correction : dans les docstrings, nommer « the template «dowel connections» template (000-ExternalFiles/201-excelTools), whose formulas Verbindung.xlsm shares » ; test de non-régression à ajouter : `test_verbindung_xlsm_holz_holz_is_VU_SD_10` avec C24/C24, d = 10, FK 2, t = 50/100, n_tot = 4, n = 2, a₁ = 120, zweischnittig → R_d 5.726197607571922 (C43), R_d,Verb 22.904790430287687 (C44), k_β 1.2656780778061667 (C40), k_red 0.9765451151545597 (C33), M_u,k 60910.39709468513 (C37), K_ser,Verb = 0,9 × 22503.25097829937 (C62, AUD-2-3).

**AUD-2-8 | A | `calc/norms/sia261-2020-tab08-nutzlasten.json` `_source`** — Seul fichier du tirage sans page ni chemin (§2 règle 13, « at a page that can be turned to ») ; Tabelle 8 est p. 37 de `SIA261-2020-DE.pdf`. Correction : ajouter « 000-ExternalFiles/000-Normes/SIA261-2020-DE.pdf p. 37 » à `_source`. Aucun nombre changé.

**AUD-2-9 | A | `prompt-audit.md` §2.1, ligne « «R_k to R_d» » de la table** — La table dit que les γ_M, η et k_mod de `norms/…tab01…`, `tab04…` sont « ce que dowel.py utilise ». Faux : le Rechner calcule R_d = R_k·η_mod/γ_M pour les Holzwerkstoffe de SIA 265/1 (γ_M 1,3 « Verbindung generell », 1,15 si Ds > 3 ; η_mod par KLED et FK), `sia265.gamma_m()` n'a aucun appelant hors `tests/test_norms.py` (grep), et `dowel.py` utilise k_α, η_w et η_t, pas γ_M. Correction : marquer ce modèle « aucun » (non couvert) ; ajouter `wind.py` à la ligne Belastungsannahmen (déjà présent) et noter que le modèle 3.2 n'a pas d'exemple enregistré.

**AUD-2-10 | C | modèle Biegesteifer 1.0, C18 `=(C13-2*C16)/(C17-1)`** — Un groupe à une seule file (C17 = 1) met toute la feuille en `#DIV/0!` (cas 1 × 4 et 1 × 1) ; le projet calcule ces groupes (1 × 4 : F_max 8,757 kN ; 1 × 1 avec moment : refus « I_p = 0 »).

**AUD-2-11 | C | `calc/domains/snow.py` `RESULT_CELLS`** — GiebeldachLM2 refusé (N37/N38) sur les 4 cas du balayage : point ouvert connu du §14, rappelé parce qu'il couvre 1 modèle de charge sur 5 de la liste déroulante.

**AUD-2-12 | C | rendu de `show-calc("snow-load", "SL", level: 3)`** — La ligne en nombres imprime « h_ref = 551.768 + ± 0 = 551.768 m » (la variable `korrektur` vaut le texte « ± 0 » du menu), et la citation « SIA 261 §Anhang D ». Lisible mais maladroit ; relève plutôt de la phase 3.

**AUD-2-13 | C | inventaire** — 23 modèles de référence sans module Python (liste au §2.1).

**AUD-2-14 | C | `calc/domains/connector.py:726-728` contre classeur B53/D53** — La longueur minimale de la connexion prend n = max(n_i) des pièces ; le classeur prend n de la pièce 1 (C30). Conformes sur les 62 cas, mais le cas n₂ > n₁ n'a pas été balayé.

**AUD-2-15 | C | balayages** — Défauts de harnais rencontrés et corrigés, à ne pas confondre avec des écarts : lignes f_h de la pièce 2 (décalage), `t_B` des tôles extérieures (C19 du classeur calculé mais non lu), chiffres gras mathématiques Unicode dans le PDF (normalisation NFKC), libellé « gk+ak= » présent deux fois dans les feuilles de couches (Summe et Gewählt).

## NON FAIT

- **NF-1** : niveau A des charges sur l'exemple du modèle `«load workbook» template` — le modèle n'enregistre aucun exemple (entrées vides, sorties `#N/A`). Remplacé par le classeur du projet (16/16) et par le balayage du niveau B.
- **NF-2** : balayage du vent (`wind.py`) — hors des priorités de la mission ; seul le constat AUD-2-1 (L70) a été établi, sur les caches du classeur du projet.

## Vérifications manuelles proposées à l'ingénieur

1. Ouvrir `WL-Velo` de `Belastungsannahmen.xlsm` à côté du modèle 3.2 : comparer L70 (AUD-2-1) et décider de la mise à jour.
2. Dans le modèle Biegesteifer, saisir α = 30°, F_Ed,x = 10, F_Ed,y = 10, M = 0 : lire C50 (15°) et le comparer à l'angle mesuré sur le dessin de la grille (75°) (AUD-2-4).
3. Décider du traitement d'une ligne de couche « Installationen und Innenwände » à charge saisie (AUD-2-2).

## Contrôles qui pourraient devenir des tests

- `tests/test_dowel.py` : table figée des 62 cas Stabdübel avec les valeurs Excel (R_d, R_d,Verb, k_β, k_red, t_1,1, t_1,2, t_2,2, K_ser,Verb), docstring nommant « «dowel connections» template », les écarts connus marqués par cas (éq. (125), n = 1, η_w de K_ser). Données prêtes : `p2/sweep_dowel.json` + `sweep_dowel_hh2.json`.
- `tests/test_connection.py` : les 29 cas du classeur Biegesteifer 1.0 (F_i par broche, F_max, numéro, conversion de repère z = −y, M = −M_Ed), en excluant l'angle pour α ≠ 0 et les groupes à une file (défauts du classeur). Données : `p2/sweep_polar.json`.
- Test de conversion : les trois cas élémentaires F_x, F_y, M sur la grille 3 × 4 (valeurs dans `sweep_polar.json`, cas 1 à 3).
- `tests/test_dead_load.py` : une ligne sans matériau avec K saisi (AUD-2-2), et le cas « Gartenplatten » sous « Beschichtung » (2200 kg/m³).
- `tests/test_snow.py` (ou `test_export.py`) : pour chaque modèle de charge lu, la formule imprimée réévaluée avec ses valeurs imprimées égale le résultat (64 vérifications, toutes conformes aujourd'hui).
- Garde sur les modèles : un test qui lit le numéro de version du nom de fichier des modèles couverts (1.62, 1.0, 3.2) et échoue quand il change, pour que l'oracle soit revu (le changement 3.1 → 3.2 de Belastungsannahmen serait passé inaperçu).
