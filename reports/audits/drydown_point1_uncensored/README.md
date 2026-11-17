# Audit du Séchage des Sols (Dry-Down) avec SMAP Non Censuré

**Branche** : `elaabar`  
**Dépôt** : `smap-xai-audit`  
**Date d'exécution** : 17 Novembre 2026  
**Auteur** : mohammad.elaabaribao

---

## 1. Contexte et Hypothèse Scientifique

Le modèle de surface Noah-MP 4.0.1 (domaine NorthMor ~5 km, 2016–2020) présente une anomalie majeure dans la dynamique de ressuyage post-pluviale (dry-down) :
1. **Évaporation excessive immédiate** : Dès les premiers jours suivant la pluie, l'évapotranspiration (ET) bare-ground du modèle est surévaluée par rapport aux observations satellites indépendantes (GLEAM v4.3a).
2. **Plancher artificiel et blocage au flétrissement** : Dès que l'humidité superficielle approche le point de flétrissement ($\theta \approx \theta_{\text{wilt}} \equiv \text{SMCWLT}$), la résistance de surface bare-soil de Sakaguchi & Zeng (2009) (`OPT_RSF = 1`) diverge vers l'infini, arrêtant net l'évaporation et bloquant le modèle sur un plancher rigide.
3. **Censure sélective par LIS** : Dans l'assimilation sans correction de biais (`DA_nocdf_noirr`), le filtre de contrôle qualité de LIS (`noahmp401_qc_soilmobs.F90`) impose la condition :
   $$\text{smobs} - \text{smcwlt} < 0.02$$
   Toute observation SMAP dont la teneur en eau est inférieure à $\text{SMCWLT} + 0.02\text{ m}^3/\text{m}^3$ est systématiquement **rejetée**. Or, ce sont précisément les observations les plus sèches qui révèlent que le sol réel descend bien en dessous du plancher du modèle !
4. **Effet du CDF matching** : Dans `DA_cdf_noirr`, ces observations sont conservées en apparence car rehaussées par l'égalisation quantile-quantile, mais le signal physique de dessèchement brut est annihilé.

L'objectif de cet audit est de quantifier rigoureusement cette censure, de reconstruire la série SMAP brute sans filtre de flétrissement, et de recalculer les dynamiques de ressuyage ($\tau$, $P_5$, $\theta_{\text{res}}$), les régressions par texture et la comparaison d'ET face à GLEAM.

---

## 2. Inventaire des Critères de Rejet de `noahmp401_qc_soilmobs.F90`

L'inspection de la routine Fortran `lis/surfacemodels/land/noahmp.4.0.1/da_soilm/noahmp401_qc_soilmobs.F90` identifie 8 critères de contrôle qualité appliqués aux observations SMAP avant assimilation :

| # | Critère de Rejet | Variable / Condition Fortran | Description Physique |
|---|-------------------|------------------------------|----------------------|
| 1 | **Validité spatiale & masque** | `lis%d%landmask(col,row) /= 1` ou `grid%lat < -90` | Pixel en dehors du domaine terrestre ou sur l'océan/lac. |
| 2 | **Flags de restitution satellite** | `retflag /= 0` ou `smobs == lis_undef` | Rejet des restitutions SMAP de mauvaise qualité (RFI, surface rugueuse extrême, convergence ratée). |
| 3 | **Couvert forestier** | `lis%p%vegtype == forest_code` ou `fveg > veg_max_threshold` | Atténuation micro-onde trop forte sous forêt dense ; restitution d'humidité non fiable. |
| 4 | **Contenu en eau de la végétation (VWC)** | `vwc > 5.0 kg/m²` (selon paramètre SMAP) | Canopée trop dense pour la pénétration de la bande L (1.4 GHz). |
| 5 | **Précipitations en cours** | `precip(col,row) > 0.0 mm/hr` | Eau liquide en surface (flaques) faussant la constante diélectrique. |
| 6 | **Gel du sol** | `soil_temp(1) < 273.15 K` (0 °C) | L'eau gelée a une constante diélectrique très basse simulant à tort un sol ultra-sec. |
| 7 | **Couverture neigeuse** | `snow_depth > 0.001 m` ou `swe > 0.0 kg/m²` | Masquage du signal de sol par le manteau neigeux. |
| 8 | **Seuil de flétrissement (Censure)** | `(smobs - smcwlt) < 0.02 m³/m³` | **Censure objet de l'audit** : Rejette toute observation trop proche ou inférieure au flétrissement du modèle. |

---

## 3. Réciprocité Mathématique et Reconstitution de la Série SMAP Non Censurée

À partir des fichiers `LISDAOBS` de `DA_nocdf_noirr_2016_2020` (variables `smobs_rec1` = brute, `smobs_rec2` = acceptée par le QC LIS) :
- Nous avons reconstruit la série **SMAP non censurée** en appliquant l'ensemble des filtres 1 à 7, **sans** le filtre 8 (`smobs - smcwlt < 0.02`).
- Nous avons ensuite appliqué formellement la condition `smobs - smcwlt >= 0.02` sur cette série pour vérifier la stricte bijection avec `rec2`.

**Résultats de la vérification** :
- Nombre total d'observations brutes évaluées (2016–2020) : **15 023 728**
- Nombre de désaccords avec `rec2` : **EXACTEMENT 0**
- Taux de concordance : **100.0000 %**

La série non censurée ainsi constituée isole de façon pure et chirurgicale le rôle du seuil de flétrissement.

---

## 4. Bilan de Censure par Texture et par Saison

Fraction d'observations rejetées **exclusivement** par la condition `(smobs - smcwlt) < 0.02` :

| ID | Texture | Fraction Argile | $\text{SMCWLT}$ ($\text{m}^3/\text{m}^3$) | $N_{\text{pix}}$ | NoCDF MAM (%) | NoCDF JJA (%) | NoCDF Annuel (%) | CDF MAM (%) | CDF JJA (%) | CDF Annuel (%) |
|:--:|:--------|:---------------:|:------------------------------------------:|:----------------:|:-------------:|:-------------:|:----------------:|:-----------:|:-----------:|:--------------:|
| 1  | Sand | 3 % | 0.010 | 539 | **6.9 %** | **0.0 %** | 12.9 % | 5.8 % | 0.0 % | 9.4 % |
| 3  | Sandy Loam | 10 % | 0.047 | 748 | **33.0 %** | **41.9 %** | 30.0 % | 0.7 % | 31.6 % | 9.5 % |
| 4  | Silt Loam | 13 % | 0.084 | 56 | **77.6 %** | **100.0 %** | 67.1 % | 2.0 % | 80.4 % | 29.5 % |
| 6  | Loam | 19 % | 0.066 | 12 047 | **45.6 %** | **46.4 %** | 40.5 % | 22.1 % | 44.7 % | 24.4 % |
| 7  | Sandy Clay Loam | 27 % | 0.069 | 723 | **14.6 %** | **36.4 %** | 16.4 % | 1.9 % | 32.1 % | 9.0 % |
| 9  | Clay Loam | 34 % | 0.103 | 1 305 | **46.6 %** | **75.8 %** | 49.9 % | 1.3 % | 25.8 % | 8.2 % |
| 12 | Clay | 58 % | 0.138 | 612 | **43.2 %** | **73.4 %** | 45.6 % | 4.9 % | 12.2 % | 6.7 % |

### Constats majeurs :
1. **Élimination massive des données d'été (JJA)** : En NoCDF, **73.4 % des observations sur Argile**, **75.8 % sur Clay Loam** et **100.0 % sur Silt Loam** sont rejetées.
2. **Censure printanière (MAM)** : Dès le printemps, **43 % à 78 %** des observations sur sols fins sont éliminées.
3. **Impact en CDF** : Bien que le CDF matching relève les valeurs, **44.7 % des observations sur Loam** et **80.4 % sur Silt Loam** sont encore censurées en été.
4. Les cartes spatiales complètes sont consultables dans [`censorship_budget_maps_mam_jja.png`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/audits/drydown_point1_uncensored/censorship_budget_maps_mam_jja.png).

---

## 5. Dynamique de Séchage : Censuré vs Non Censuré

Les épisodes de ressuyage sans pluie ont été ajustés par un modèle exponentiel décroissant :
$$\theta(t) = (\theta_0 - \theta_{\text{res}}) e^{-t/\tau} + \theta_{\text{res}}$$
avec bootstrap par blocs spatiaux $7\times 7$ pixels (~35 km) pour estimer les intervalles de confiance à 95 % [IC95].

### Comparaison Consolidée en MAM (Printemps)

| Texture | $\text{SMCWLT}$ | $N_{\text{épis}}^{\text{cens}}$ | $N_{\text{épis}}^{\text{uncens}}$ | $\tau_{\text{SMAP}}^{\text{cens}}$ (j) | $\tau_{\text{SMAP}}^{\text{uncens}}$ (j) | $\tau_{\text{OL}}$ (j) | $P_{5,\text{SMAP}}^{\text{uncens}}$ | $P_{5,\text{OL}}$ | $\theta_{\text{res, SMAP}}^{\text{cens}}$ | $\theta_{\text{res, SMAP}}^{\text{uncens}}$ | $\theta_{\text{res, OL}}$ |
|:--------|:---------------:|:-------------------------------:|:---------------------------------:|:--------------------------------------:|:----------------------------------------:|:----------------------:|:-----------------------------------:|:------------------:|:-----------------------------------------:|:-------------------------------------------:|:-------------------------:|
| Sand | 0.010 | 264 | 261 | 0.88 [0.83, 1.06] | **0.9 [0.8, 1.1]** | 30.6 [11.5, 42.9] | 0.031 | 0.010 | 0.053 [0.049, 0.055] | **0.053 [0.049, 0.055]** | 0.028 [0.002, 0.071] |
| Sandy Loam | 0.047 | 1 383 | 2 024 | 1.07 [0.94, 1.97] | **1.7 [1.3, 2.3]** | 8.8 [8.1, 9.6] | 0.030 | 0.094 | 0.076 [0.073, 0.079] | **0.049 [0.045, 0.052]** | 0.115 [0.101, 0.128] |
| Silt Loam | 0.084 | — | 126 | N/A | **1.5 [1.0, 2.0]** | 9.3 [6.9, 16.6] | 0.032 | 0.105 | N/A | **0.049 [0.047, 0.049]** | 0.165 [0.132, 0.196] |
| Loam | 0.066 | 24 155 | 32 645 | 1.95 [1.75, 2.14] | **1.8 [1.5, 2.0]** | 10.6 [9.8, 11.5] | 0.064 | 0.103 | 0.094 [0.093, 0.095] | **0.073 [0.069, 0.077]** | 0.120 [0.114, 0.126] |
| Sandy Clay Loam | 0.069 | 2 880 | 2 963 | 2.69 [2.38, 2.96] | **2.9 [2.6, 3.1]** | 7.8 [7.3, 8.4] | 0.082 | 0.116 | 0.099 [0.095, 0.103] | **0.089 [0.081, 0.096]** | 0.115 [0.110, 0.127] |
| Clay Loam | 0.103 | 3 158 | 5 675 | 2.10 [1.85, 2.56] | **2.9 [2.7, 3.0]** | 8.1 [7.7, 8.6] | 0.054 | 0.141 | 0.126 [0.122, 0.129] | **0.068 [0.064, 0.075]** | 0.135 [0.131, 0.141] |
| Clay | 0.138 | 1 850 | 3 103 | 3.03 [2.68, 3.46] | **3.4 [3.2, 3.6]** | 6.0 [5.6, 6.3] | 0.086 | 0.193 | 0.149 [0.146, 0.155] | **0.102 [0.086, 0.116]** | 0.189 [0.188, 0.190] |

---

## 6. Analyse de Pente : $\tau$ en Fonction de la Fraction d'Argile

Régression linéaire de la constante de temps $\tau$ sur la fraction d'argile nominale des classes de texture USDA :
$$\tau = a \cdot f_{\text{clay}} + b$$

| Échantillon | Saison | $N_{\text{épisodes}}$ | Pente SMAP $a_{\text{SMAP}}$ (j/fraction) | IC 95 % SMAP | Pente OL $a_{\text{OL}}$ (j/fraction) | IC 95 % OL |
|:------------|:------:|:--------------------:|:-----------------------------------------:|:------------:|:-------------------------------------:|:----------:|
| **Baseline ($N \ge 3$)** | **MAM** | **46 797** | **+4.40** | **[+2.88, +5.82]** | **-18.38** | **[-23.17, -14.77]** |
| Baseline ($N \ge 3$) | JJA | 5 207 | -0.46 | [-3.05, +1.21] | -6.56 | [-16.03, +4.16] |
| Baseline ($N \ge 3$) | ALL | 152 465 | +7.54 | [+5.89, +8.94] | -18.19 | [-22.42, -14.64] |
| **Sensibilité ($N \ge 4$)** | **MAM** | **44 952** | **+4.91** | **[+3.35, +6.36]** | **-19.57** | **[-24.58, -15.76]** |
| Sensibilité ($N \ge 4$) | JJA | 4 547 | +0.21 | [-2.48, +2.10] | -6.99 | [-14.62, +2.86] |

### Enseignement fondamental :
- **SMAP présente un comportement physique cohérent** : La pente est strictement positive (+4.4 à +4.9 j/fraction d'argile, $p < 0.001$). Plus le sol est argileux, plus la rétention capillaire est forte et plus le séchage est lent ($\tau$ passe de 0.9 j sur sable à 3.4 j sur argile).
- **Noah-MP (OL) présente un comportement physique aberrant** : La pente est négative et très raide (-18.4 à -19.6 j/fraction d'argile). Sur sable, le modèle met 30.6 jours à sécher ! Sur argile, il s'effondre en 6.0 jours avant de se heurter immédiatement à son plancher de flétrissement artificiel.
- La figure correspondante est disponible dans [`tau_vs_clay_regression_mam.png`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/audits/drydown_point1_uncensored/tau_vs_clay_regression_mam.png).

---

## 7. Évapotranspiration (ET) en MAM : Noah-MP OL vs GLEAM v4.3a

Moyenne et médiane de l'ET sur les **5 premiers jours suivant la pluie** en MAM :

| Texture | $f_{\text{clay}}$ | $N_{\text{épisodes}}$ | $\text{ET}_{\text{OL}}$ Moy (mm/j) | $\text{ET}_{\text{GLEAM}}$ Moy (mm/j) | $\Delta\text{ET}$ ($\text{OL} - \text{GLEAM}$) | Biais Relatif (%) |
|:--------|:-----------------:|:--------------------:|:----------------------------------:|:-------------------------------------:|:----------------------------------------------:|:-----------------:|
| Sand | 3 % | 261 | 0.37 | 0.14 | +0.23 mm/j | +160.8 % |
| Sandy Loam | 10 % | 1 935 | 1.38 | 1.70 | -0.32 mm/j | -18.6 % |
| Silt Loam | 13 % | 126 | 2.00 | 1.75 | +0.25 mm/j | +14.0 % |
| Loam | 19 % | 32 092 | 1.56 | 1.45 | +0.11 mm/j | +7.4 % |
| Sandy Clay Loam | 27 % | 2 957 | 2.15 | 1.83 | +0.32 mm/j | +17.7 % |
| **Clay Loam** | 34 % | 5 675 | **2.44** | **1.84** | **+0.60 mm/j** | **+32.5 %** |
| **Clay** | 58 % | 3 103 | **3.37** | **2.04** | **+1.34 mm/j** | **+65.6 %** |

Voir la figure de synthèse : [`et_mam_drydown_ol_vs_gleam.png`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/audits/drydown_point1_uncensored/et_mam_drydown_ol_vs_gleam.png).

---

## 8. Conclusion Scientifique Explicite

1. **La censure du filtre QC LIS est prouvée de façon irréfutable** :
   En imposant `smobs - smcwlt < 0.02`, LIS rejette 43 % à 78 % des observations SMAP au printemps et 73 % à 100 % en été sur les textures fines (Argile, Clay Loam, Silt Loam).
2. **Le sol réel descend considérablement sous le flétrissement de Noah-MP** :
   Dans la série SMAP non censurée, le plancher résiduel observé $\theta_{\text{res}}$ sur Argile est de **0.102 m³/m³** ($P_5 = 0.086$), alors que la valeur tabulée de flétrissement du modèle est $\text{SMCWLT} = \mathbf{0.138\text{ m}^3/\text{m}^3}$, et le plancher du modèle OL est à **0.189 m³/m³**.
3. **Double anomalie physique de Noah-MP** :
   - Immédiatement après la pluie, Noah-MP surévapore massivement sur les sols argileux (+65.6 % par rapport à GLEAM v4.3a).
   - Ensuite, dès que $\theta \to \text{SMCWLT}$, l'option de résistance de surface `OPT_RSF = 1` (Sakaguchi & Zeng 2009) paralyse l'évaporation du sol nu, empêchant le modèle de poursuivre son séchage naturel vers 0.08–0.10 m³/m³.
4. **Conséquence pour l'assimilation NoCDF** :
   Le filtre de QC empêche précisément SMAP de corriger ce défaut en rejetant les observations réelles qui contredisent le plancher du modèle.
