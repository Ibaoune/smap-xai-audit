# Rapport d'Audit Scientifique AUD-05, AUD-05B & AUD-05C : Contrôle du Bilan Hydrique Noah-MP, Référence Open Loop et Examen des Perturbations d'État

**Date :** 29 octobre 2026  
**Auteur :** Antigravity (Assistant IA) — Pair programming avec M. El Aabaribaoune  
**Statut :** Soumis pour validation  
**Périmètre d'analyse :** 611 pixels argileux dominants (`soiltype == 12`, `landcover > 4`, `landmask == 1`) sur la période 1er juillet – 31 août 2018 (62 jours).

---

## 1. Options hydrologiques et de nappe dans les configurations réelles

Dans toutes les simulations effectivement exécutées (`OPL_noirr_2016_2020`, `DA_nocdf_noirr_2016_2020`, `DA_nocdf_TEST_nowilt` et `OPL_hourly_201807`, inspectées dans `generated/configs/lis_*.config`) :
```ini
Noah-MP.4.0.1 runoff and groundwater option: 1  # 1 = SIMGM (Simple Groundwater Model, Niu et al. 2007)
```
- **Schéma hydrogéologique :** Modèle de nappe d'équilibre simple SIMGM (sous-routine `GROUNDWATER` dans `module_sf_noahmplsm_401.F90:8338`).

---

## 2. Définitions dans le code LIS / Noah-MP, unités et signification physique

Sources inspectées :
- `NoahMP401_main.F90` (interface LIS 7.5 – Noah-MP 4.0.1)
- `module_sf_noahmplsm_401.F90` (physique Noah-MP 4.0.1)
- `shared/MODEL_OUTPUT_LIST.TBL` (table des variables de sortie LIS)

| Variable | Fichier code & ligne | Unités code / NetCDF | Définition physique & rôle dans le bilan |
|---|---|---|---|
| `TotalPrecip_tavg` | `LIS_histDataMod.F90`, `MODEL_OUTPUT_LIST.TBL:18` | $\\text{kg}\\cdot\\text{m}^{-2}\\cdot\\text{s}^{-1}$ (mm/s) | Taux moyen de précipitation liquide et solide reçu à la surface du sol pendant l'intervalle de sortie (24 h). Cumul journalier : $\\times 86400$ s. |
| `Evap_tavg` | `NoahMP401_main.F90:1311` | $\\text{kg}\\cdot\\text{m}^{-2}\\cdot\\text{s}^{-1}$ (mm/s) | Évapotranspiration totale $QFX = ETRAN + ECAN + EDIR$ (transpiration + interception foliaire + évaporation directe du sol). |
| `Qs_tavg` | `NoahMP401_main.F90:1159` | $\\text{kg}\\cdot\\text{m}^{-2}\\cdot\\text{s}^{-1}$ (mm/s) | Ruissellement de surface (`runsf`), calculé selon la fraction saturée $Q_s = Q_{insur} \\cdot f_{sat}$. |
| `Qsb_tavg` | `NoahMP401_main.F90:1165` | $\\text{kg}\\cdot\\text{m}^{-2}\\cdot\\text{s}^{-1}$ (mm/s) | Ruissellement souterrain / drainage latéral (`runsb` = $Q_{dis}$). Vidange exponentielle de l'aquifère vers le réseau de drainage. |
| `WA` | `module_sf_noahmplsm_401.F90:8361` | mm | Stock d'eau dans l'aquifère non confiné sous la colonne de sol de 2 m (capacité max 5000 mm, yield spécifique $S_y = 0.20$). |
| `WT` | `module_sf_noahmplsm_401.F90:8362` | mm | Stock d'eau total aquifère + sol saturé. **Contrôle :** lorsque $ZWT \\ge 2$ m (nappe située sous la colonne de sol de 2 m, ce qui est le cas partout sur le domaine), le code pose explicitement $WT = WA$ (`module_sf_noahmplsm_401.F90:8459`). La différence $|WT - WA|$ dans tous les restarts est exactement de **0,000 mm**. $WT$ ne contient donc **aucune quantité physique supplémentaire**. |
| `ZWT` | `module_sf_noahmplsm_401.F90:8360` | m | Profondeur de la nappe sous la surface : $ZWT = 27.0 - WA / (1000 \\cdot 0.20)$ (bornée par $ZWT \\ge 1.5$ m). |
| `GWS` | `NoahMP401_main.F90:1039` | mm | Variable diagnostique LIS issue directement de `wa` (`LIS_MOC_GWS = wa`). |
| `RECH` (`QIN`) | `module_sf_noahmplsm_401.F90:8451` | mm/s | Flux vertical net entre couche 4 et nappe : $Q_{IN} = - K_A \\frac{\\psi_{ZWT} - \\psi_4}{ZWT - z_4}$. Si $Q_{IN} > 0$ : recharge ; si $Q_{IN} < 0$ : **remontée capillaire**. |

---

## 3. Examen de l'hypothèse de remontée capillaire (AUD-05)

1. **Existence physique dans la paramétrisation :**
   - La remontée capillaire est représentée dans SIMGM (`module_sf_noahmplsm_401.F90:8451`) lorsque le potentiel matriciel de la couche 4 devient plus négatif que la charge hydraulique de l'aquifère ($Q_{IN} < 0$). L'eau est alors transférée de l'aquifère vers la couche 4 (`MLIQ(4) = MLIQ(4) - QIN * DT`, et `WA` diminue d'autant).
2. **Disponibilité dans les sorties LIS existantes :**
   - Ce flux n'est **pas disponible** dans les sorties historiques. Dans `shared/MODEL_OUTPUT_LIST.TBL`, `Qrec`, `RechToGW` et `RechFromGW` ont l'indicateur `select = 0` (non archivés).
3. **Analyse du rôle dans le résidu différentiel de +32,31 mm :**
   - La remontée capillaire constitue un **flux interne** à la colonne sol-aquifère : toute eau quittant la nappe pour monter dans la couche 4 réduit le stock `WA` du même montant qu'elle augmente le stock du sol `SMC(4)`.
   - Dans le bilan total fermé ($\\Delta S_{total} = \\Delta S_{sol} + \\Delta S_{WA}$), ce flux interne **s'annule rigoureusement**.
   - Par ailleurs, les restarts instantanés montrent que la variation du stock de nappe $\\Delta S_{WA}$ sur les 62 jours est de **-4,333 mm** dans le Contrôle et **-4,339 mm** dans Nowilt, soit un écart différentiel négligeable de **-0,006 mm**.
   - La remontée capillaire ne permet donc pas d'expliquer le résidu différentiel de +32,31 mm.

---

## 4. Bilan hydrique comparatif : Open Loop (OPL), Contrôle (DA-Ctrl) et Nowilt (AUD-05B)

Calculé sur les mêmes **611 pixels argileux** du 1er juillet 2018 00:00 au 1er septembre 2018 00:00 (62 jours) à partir des états instantanés des fichiers restart `LIS_RST_NOAHMP401` et des 62 fichiers d'historique journalier :

| Terme hydrologique (mm) | OPL (Open Loop) | DA-Ctrl (Contrôle) | Nowilt (Sans seuil) | Différence (Nowilt − Ctrl) |
|---|---:|---:|---:|---:|
| **Précipitation ($P$)** | 2,405 | 2,411 | 2,411 | 0,000 |
| **Incréments EnKF ($Incr$, L1–L4)** | 0,000 | +0,020 | -21,553 | -21,573 |
| **Inflow Total ($P + Incr$)** | **+2,405** | **+2,431** | **-19,142** | **-21,573** |
| Évapotranspiration totale ($ET$) | 38,907 | 87,430 | 40,421 | -47,009 |
| *— Évaporation du sol ($ESoil$)* | *9,837* | *54,718* | *11,292* | *-43,426* |
| *— Transpiration végétale ($TVeg$)* | *28,598* | *32,215* | *28,657* | *-3,557* |
| *— Interception canopée ($ECan$)* | *0,472* | *0,498* | *0,472* | *-0,026* |
| Ruissellement surface ($Q_s$) | 0,328 | 0,175 | 0,204 | +0,029 |
| Drainage / baseflow ($Q_{sb}$) | 5,623 | 3,400 | 3,400 | -0,000 |
| **Outflow Total ($ET + Q_s + Q_{sb}$)** | **44,857** | **91,006** | **44,025** | **-46,981** |
| **Flux net ($Inflow - Outflow$)** | **-42,452** | **-88,575** | **-63,167** | **+25,408** |
| $\\Delta S$ Sol (0–2 m, restarts) | -35,490 | -25,020 | -31,895 | -6,875 |
| $\\Delta S$ Nappe ($WA$, restarts) | -6,498 | -4,333 | -4,339 | -0,006 |
| **$\\Delta S$ Total (Sol + Nappe)** | **-41,988** | **-29,353** | **-36,233** | **-6,880** |
| **RÉSIDU DE BILAN TOTAL** | **-0,464** | **-59,222** | **-26,934** | **+32,288** |

*Définition du résidu : $R = (Inflow - Outflow) - \\Delta S_{total}$. Un résidu négatif indique que l'outflow dépasse la somme des apports et de la déplétion des stocks mesurée.*

### Observations sur les données :
1. **Fermeture en Open Loop :** En Open Loop (simulation directe non perturbée, sans assimilation), le résidu de bilan est de **-0,464 mm sur 62 jours** (soit une moyenne de **-0,007 mm/jour**). Ce résultat montre que le modèle Noah-MP 4.0.1 présente une fermeture quasi-parfaite de son bilan en simulation directe sur cette période.
2. **Décomposition arithmétique du résidu différentiel :** Le résidu différentiel (+32,29 mm) correspond exactement à l'écart entre les résidus des deux simulations d'assimilation :
   $$R_{diff} = R_{Nowilt} - R_{Ctrl} = -26,934 - (-59,222) = +32,288\\text{ mm}$$

---

## 5. Examen technique des perturbations d'état et des bornes (AUD-05C)

### 5.1. Configuration dans LIS
Dans la configuration EnKF exécutée (`lis_DA_SMAP_nocdf_noirr_2018-07.config`) et les tables associées :
- **Algorithme :** `"GMAO scheme"` (`gmaopert_Mod.F90:1286`, perturbations spatialement et temporellement corrélées).
- **Fréquence :** `State perturbation frequency: "3hr"` (`LIS_lsmMod.F90:749`).
- **Couche concernée et amplitude :** Définies dans `noahmp_sm_pertattribs.txt` :
  - *Couche 1 (0–10 cm) :* perturbation additive (type 0), $\\sigma = 0,004\\text{ m}^3/\\text{m}^3$, $\\text{std\\_max} = 2,5$ (borne maximale de perturbation à $\\pm 0,010\\text{ m}^3/\\text{m}^3$), $\\tau = 43200\\text{ s}$ (12 h).
  - *Couches 2 à 4 :* $\\sigma = 0,00$ (aucune perturbation d'état).
- **Centrage d'ensemble :** Dans `LIS_lsmMod.F90:1215-1240` (`applyLSMPert`), le code applique la correction de Ryu et al. (2009) (`LIS_rc%pert_bias_corr = 1`) qui soustrait la moyenne d'ensemble des perturbations avant QC pour garantir une perturbation moyenne théorique nulle.

### 5.2. Valeur exacte de `smcwlt` sur argile et distinction des seuils de bornage
Les vérifications dans les fichiers de paramètres et le code confirment :
1. **Valeur de `smcwlt` sur argile (classe 12) :**
   Dans `data/land_params/noahmp401_parms/SOILPARM.TBL` (table `STAS`, ligne 15 pour `CLAY`) :
   $$\\text{WLTSMC} = 0,138\\text{ m}^3/\\text{m}^3$$
2. **Seuil effectif de filtrage des observations SMAP :**
   Dans `NoahMP401_qc_soilmobs.F90:272` :
   ```fortran
   elseif(smobs(t) - smcwlt_obs(t) .lt. 0.02) then 
      smobs(t) = LIS_rc%udef
   ```
   Le seuil déduit pour l'argile à partir de `SOILPARM.TBL` et du code QC est donc :
   $$\\text{Seuil SMAP déduit} = 0,138 + 0,02 = 0,158\\text{ m}^3/\\text{m}^3$$
   *(La mention antérieure de 0,218 était une erreur d'inattention, rectifiée ici). Ce seuil est déduit sous réserve de confirmer lors de l'audit AUD-06 la correspondance effective avec le champ spatial `smcwlt_obs(t)` sur les pixels concernés.*
3. **Planchers numériques de sécurité distincts dans le code :**
   - *QC post-perturbation (`NoahMP401_qcsoilm.F90:68-69`, via `noahmp_sm_attribs.txt`) :* borne basse $\\text{smmin1} = 0,01\\text{ m}^3/\\text{m}^3$.
   - *QC lors de l'assimilation (`noahmp401_setsoilm.F90:66, 154`) :* paramètre strict `MIN_THRESHOLD = 0.02` bloquant la mise à jour si $\\theta_1 + \\Delta < 0,02\\text{ m}^3/\\text{m}^3$.

### 5.3. Distribution de l'humidité L1 aux restarts EnKF (12 220 valeurs : 611 pixels × 20 membres)

| Statistique ($\\text{m}^3/\\text{m}^3$) | DA-Ctrl (2018-07-01 00:00) | DA-Ctrl (2018-09-01 00:00) | Nowilt (2018-09-01 00:00) |
|---|---:|---:|---:|
| **Minimum absolu** | 0,02014 | 0,02002 | 0,02002 |
| **Quantile 1%** | 0,02999 | 0,03056 | 0,02457 |
| **Quantile 5%** | 0,05688 | 0,05964 | 0,03779 |
| **Médiane** | 0,19644 | 0,19608 | 0,12100 |
| **Moyenne d'ensemble** | 0,19600 | 0,19434 | 0,13422 |
| **Quantile 95%** | 0,31171 | 0,30120 | 0,27310 |
| **Maximum absolu** | 0,43852 | 0,44292 | 0,44292 |
| Nombre de valeurs $\\le 0,020$ | **0** | **0** | **0** |
| Nombre de valeurs $\\le 0,050$ | 473 (3,9 %) | 411 (3,4 %) | 1247 (10,2 %) |
| Nombre de valeurs $\\le 0,100$ | 1734 (14,2 %) | 1559 (12,8 %) | 4663 (38,2 %) |

**Analyse des distributions :**
- Aucun membre n'atteint la borne $\\text{smmin1} = 0,01$.
- Les valeurs minimales observées aux restarts s'arrêtent juste au-dessus de `MIN_THRESHOLD = 0.02`.
- **Limite de représentativité :** Ces distributions ne documentent que deux instants ponctuels (00:00 UTC au début et à la fin de la période de 62 jours). Elles ne permettent pas d'observer l'état d'humidité au moment précis de l'application de chacun des 496 cycles tri-horaires de perturbations.

### 5.4. Opérateur d'agrégation d'ensemble dans LIS
Dans `LIS_historyMod.F90:8775-8785` (`gather_gridded_output_patch`), le diagnostic des flux pour les fichiers historiques `SURFACEMODEL/LIS_HIST` effectue :
```fortran
var1(c) = var1(c) + var(t) * LIS_surface(n,mtype)%tile(t)%fgrd * LIS_surface(n,mtype)%tile(t)%pens
```
Avec `pens = 1.0 / nensem` ($1/20 = 0,05$) et `fgrd = 1.0`, le flux historique représente **rigoureusement la même moyenne arithmétique** sur les 20 membres que celle calculée sur les états instantanés des restarts ($\\frac{1}{20}\\sum_{m=1}^{20}$). Aucune divergence arithmétique n'est introduite par l'agrégation.

### 5.5. Disponibilité des sorties et quantification du bilan net
- Les sorties existantes de LIS ne tracent aucun flux cumulé d'eau associé aux perturbations stochastiques d'état ou de forçage. Les fichiers `DAPERT` ne contiennent que les états du générateur pseudo-aléatoire pour les reprises de calcul.
- Par conséquent, les données disponibles **ne permettent pas de mesurer la contribution massique exacte des perturbations**, ni de prouver quantitativement qu'elles sont responsables des -59,22 mm de résidu dans le Contrôle.

---

## 6. Limitation méthodologique majeure : Interprétation de l'écart DA − OL

Une précaution méthodologique stricte s'impose :
- La simulation **Open Loop (OL)** est une simulation déterministe à **un seul membre**, sans perturbations météorologiques, sans perturbations d'état et sans assimilation.
- La simulation **DA-NoCDF** utilise un ensemble EnKF de **20 membres**, avec des forçages atmosphériques perturbés (pluie multiplicative $\\sigma = 0,50$, rayonnement solaire $\\sigma = 0,30$), des perturbations d'état tri-horaires sur la couche 1 ($\\sigma = 0,004$), et un filtre d'assimilation SMAP (qui filtre les observations sur sol sec selon le critère smcwlt_obs).

Par conséquent, **l'écart DA − OL ne permet pas, à lui seul, d'isoler l'effet causal des observations SMAP**. De plus, les différences constatées entre DA et OL (notamment la plus forte évaporation dans DA-Ctrl) **ne peuvent pas être affirmées comme étant causées par les perturbations EnKF**, ce mécanisme n'étant pas démontré par les données. Les écarts DA − OL peuvent résulter :
1. Des perturbations de forçage et d'état et de la dispersion non-linéaire sur les 20 membres,
2. Des analyses SMAP antérieures accumulées dans l'historique de la simulation (effets mémoires de stock),
3. Des interactions complexes entre perturbations et assimilation,
4. De l'effet propre des observations satellitaires effectivement assimilées sur la période.

---

## 7. Conclusions d'audit

### A. VALIDÉ
1. **Fermeture du bilan en Open Loop :** Le bilan d'eau se ferme à -0,464 mm sur 62 jours (-0,007 mm/jour), indiquant que le modèle biophysique direct Noah-MP 4.0.1 ne présente pas de défaut structurel de bilan en simulation directe non perturbée.
2. **Identité des réservoirs souterrains :** $WT = WA$ rigoureusement sur tout le domaine en raison de $ZWT \\ge 2,0$ m (différence maximale = 0,000 mm).
3. **Cohérence de l'opérateur d'agrégation :** Les flux `LIS_HIST` et les états de restart utilisent la même moyenne arithmétique d'ensemble $\\frac{1}{20}\\sum_{m=1}^{20}$.
4. **Réfutation de la remontée capillaire externe :** La remontée capillaire étant un flux interne sol-aquifère qui s'annule dans le bilan total ($\\Delta S_{tot} = \\Delta S_{sol} + \\Delta S_{WA}$), et l'écart différentiel sur la nappe étant quasi-nul (-0,006 mm), elle ne peut pas expliquer le résidu de +32,31 mm.
5. **Paramètres de flétrissement :** $\\text{smcwlt} = 0,138\\text{ m}^3/\\text{m}^3$ sur argile (classe 12) dans `SOILPARM.TBL`. Combiné au critère `smobs(t) - smcwlt_obs(t) < 0.02` dans `NoahMP401_qc_soilmobs.F90`, cela conduit à un seuil déduit de $0,138 + 0,02 = 0,158\\text{ m}^3/\\text{m}^3$, sous réserve de confirmer la correspondance effective avec le champ spatial `smcwlt_obs(t)` sur les pixels concernés.

### B. NON DÉMONTRÉ
1. **Origine exacte des résidus EnKF (-59,22 mm dans DA-Ctrl et -26,93 mm dans Nowilt) :** En l'absence d'archivage des flux de perturbation par LIS, l'hypothèse selon laquelle la troncature basse asymétrique des perturbations d'état injecterait l'eau excédentaire reste non démontrée quantitativement.
2. **Défaut de conservation de LIS :** Les données actuelles ne permettent pas de conclure à un défaut de conservation de masse dans le code de LIS/Noah-MP lors des étapes EnKF.

### C. CONSÉQUENCES POUR LE PAPIER XAI–HyMAP
1. **Interprétation des incréments et des flux dans l'analyse XAI :**
   - Sur les sols argileux en période estivale, selon nos diagnostics préalables (dont le taux de rejet approchant 99 % et la comptabilisation exacte seront vérifiés formellement lors d'AUD-06), une très large majorité des observations SMAP semble rejetée par le filtre de flétrissement (seuil déduit à $0,158\\text{ m}^3/\\text{m}^3$), rendant les incréments effectifs quasi-nuls (+0,02 mm sur 2 mois).
   - L'augmentation de l'évaporation du sol ($ESoil$) observée dans DA-Ctrl (54,7 mm contre 9,8 mm en OL) ne peut pas être attribuée aux seules observations SMAP, ni affirmée comme étant causée par les perturbations EnKF (ce mécanisme n'étant pas démontré). Les différences DA − OL peuvent résulter des perturbations, des analyses SMAP antérieures (effets mémoires) et de leurs interactions. L'attribution causale XAI doit donc expliciter cette imbrication sans poser de causalité simpliste.
2. **Impact de l'expérience Nowilt :**
   - Le test Nowilt montre que forcer l'assimilation sans seuil applique -21,55 mm d'incréments négatifs qui assèchent la couche de surface et ramènent l'évaporation du sol à 11,29 mm (très proche des 9,84 mm de l'OL).
   - Ce résultat confirme la très grande sensibilité du couplage SMAP–Noah-MP au choix du seuil de filtrage sur sol sec, un point méthodologique central à discuter dans le manuscrit.
3. **Communication sur les bilans hydriques :**
   - Le manuscrit ne doit pas présenter le résidu différentiel de +32,31 mm comme une preuve de remontée capillaire non modélisée, cette hypothèse étant réfutée par la conservation sol-nappe.
   - Les comparaisons hydrologiques entre DA et OL doivent systématiquement expliciter la différence de configuration (1 membre déterministe vs 20 membres stochastiques) pour éviter toute attribution causale erronée.
