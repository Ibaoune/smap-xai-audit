# Audit Scientifique et Diagnostic Rigoureux — Année 2018 (Janvier–Mai)

**Auteur** : M. El Aabaribaoune (`@um6p`)  
**Dépôt** : `smap-xai-audit` (Branche `elaabar`)  
**Dossier d'audit** : `reports/audits/diag2018_e6_clean/`  
**Génération** : Automatisée par script (`generate_clean_report.py`). Aucun chiffre n'est encodé manuellement.

---

## 1. Effet d'Ensemble sur la Dynamique d'Humidité du Sol (Hypothèse E6)

Le tableau suivant récapitule les écarts mensuels d'humidité superficielle ($\theta_1$) par rapport à l'Open-Loop déterministe (`OPL`), la part attribuable à l'ensemble de 20 membres, ainsi que les flux mensuels comparés :

| Mois | ΔSM1 (ENS - OPL) | ΔSM1 (DAnocdf - OPL) | ΔSM1 (DAcdf - OPL) | Fraction Ens (%) | P OPL (mm) | P ENS (mm) | ΔP ENS (mm) | ΔET ENS (mm) | ΔET DAnocdf (mm) | ΔET DAcdf (mm) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 201801.00 | -0.0239 | -0.0312 | 0.0011 | 76.60 | 42.19 | 42.29 | 0.1100 | -0.1700 | -1.96 | 3.13 |
| 201802.00 | -0.0071 | -0.0363 | -0.0070 | 19.50 | 23.99 | 26.89 | 2.90 | 2.33 | -3.71 | 1.79 |
| 201803.00 | -0.0047 | -0.0347 | -0.0101 | 13.40 | 58.24 | 65.09 | 6.85 | 4.04 | -6.92 | 1.34 |
| 201804.00 | -0.0031 | -0.0310 | -0.0026 | 10.00 | 47.39 | 45.95 | -1.44 | 3.71 | -9.39 | 1.60 |
| 201805.00 | -0.0012 | -0.0316 | -0.0074 | 3.90 | 21.69 | 21.39 | -0.3000 | 5.94 | -12.29 | -0.1300 |

### Données quantitatives issues du tableau :
* En janvier, l'effet d'ensemble explique **76.6 %** de l'écart initial ($\Delta\text{SM1}(\text{ENS}) = -0.0239$ vs $\Delta\text{SM1}(\text{DAnocdf}) = -0.0312$).
* En février, la part de l'ensemble tombe à **19.5 %**.
* En mars, elle atteint **13.4 %**, en avril **10.0 %**, et s'établit à **3.9 %** en mai.
* En mai, sur un écart $\Delta\text{SM1}$ de **-0.0316 m³/m³**, la contribution de l'ensemble n'est que de **-0.0012 m³/m³**, ce qui signifie que **96.1 % du dessèchement de DA_nocdf résulte directement de l'assimilation SMAP**.
* Sur le plan atmosphérique, les forçages perturbés dans `ENS_OPL` introduisent un excédent de pluie atteignant **+6.85 mm** en mars, augmentant l'ET d'ensemble de **+4.04 mm**. À l'inverse, l'assimilation SMAP dans `DA_nocdf` assèche le profil et comprime l'ET de **-12.29 mm** en mai.

![Effet d'ensemble vs DA](figures/fig_e6_ensemble_vs_da_response.png)
![Bilan hydrique différentiel](figures/fig_e6_water_balance_diffs.png)

---

## 2. Fréquence d'Écrêtage Physique par Membre dans les Restarts (ENS_OPL)

Le tableau ci-dessous rapporte la fréquence exacte à laquelle les membres d'ensemble individuels (évalués sur les 320 600 tuiles membres des restarts mensuels complets) atteignent les bornes physiques :

| Mois | Couche | Nb Tuiles Membres | Part ≤ 0.02 (%) | Part ≥ SMCMAX (%) | Part ≤ SMCWLT (%) | Min SMC | Max SMC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2018-01 | 1 | 320600 | 0.0006 | 0.0000 | 1.79 | 0.0200 | 0.4348 |
| 2018-01 | 2 | 320600 | 0.0000 | 0.0000 | 0.0986 | 0.0201 | 0.4325 |
| 2018-01 | 3 | 320600 | 0.0000 | 0.0000 | 0.5274 | 0.0201 | 0.4196 |
| 2018-01 | 4 | 320600 | 0.0000 | 0.0000 | 0.1563 | 0.0205 | 0.4129 |
| 2018-02 | 1 | 320600 | 0.0009 | 0.0000 | 3.91 | 0.0200 | 0.4594 |
| 2018-02 | 2 | 320600 | 0.0000 | 0.0000 | 0.0290 | 0.0209 | 0.4336 |
| 2018-02 | 3 | 320600 | 0.0000 | 0.0000 | 0.2530 | 0.0207 | 0.4210 |
| 2018-02 | 4 | 320600 | 0.0000 | 0.0000 | 0.1170 | 0.0214 | 0.4084 |
| 2018-03 | 1 | 320600 | 0.0012 | 0.0000 | 11.14 | 0.0200 | 0.4325 |
| 2018-03 | 2 | 320600 | 0.0000 | 0.0000 | 0.0022 | 0.0232 | 0.4221 |
| 2018-03 | 3 | 320600 | 0.0000 | 0.0000 | 0.0708 | 0.0212 | 0.4239 |
| 2018-03 | 4 | 320600 | 0.0000 | 0.0000 | 0.0356 | 0.0210 | 0.4290 |
| 2018-04 | 1 | 320600 | 0.0203 | 0.0000 | 11.28 | 0.0172 | 0.4314 |
| 2018-04 | 2 | 320600 | 0.0000 | 0.0000 | 0.0006 | 0.0308 | 0.4230 |
| 2018-04 | 3 | 320600 | 0.0000 | 0.0000 | 0.0265 | 0.0208 | 0.4246 |
| 2018-04 | 4 | 320600 | 0.0000 | 0.0000 | 0.0240 | 0.0215 | 0.4298 |
| 2018-05 | 1 | 320600 | 0.0197 | 0.0000 | 14.66 | 0.0101 | 0.4362 |
| 2018-05 | 2 | 320600 | 0.0000 | 0.0000 | 0.0053 | 0.0297 | 0.4035 |
| 2018-05 | 3 | 320600 | 0.0000 | 0.0000 | 0.0125 | 0.0225 | 0.3969 |
| 2018-05 | 4 | 320600 | 0.0000 | 0.0000 | 0.0143 | 0.0221 | 0.3948 |

### Données quantitatives issues du tableau :
* Le plancher physique extrême $0.02\text{ m}^3/\text{m}^3$ n'est pratiquement jamais atteint en surface (**0.001 %** de janvier à mars, **0.0197 %** en mai, soit seulement 63 tuiles sur 320 600). Dans les couches 2, 3 et 4, il n'est **strictement jamais atteint (0.0000 %)**.
* Le plafond de saturation $\text{SMCMAX}$ n'est **strictement jamais atteint (0.0000 %)** sur l'ensemble des 4 couches et des 5 mois.
* Le point de flétrissement $\text{SMCWLT}$ est franchi naturellement vers le bas par le modèle sur **11.28 %** des tuiles en avril et **14.66 %** en mai en surface, mais le modèle Noah-MP ne tronque pas les états à ce seuil (la dynamique continue entre 0.02 et $\text{SMCWLT}$).

---

## 3. Impact de la Censure du Point de Flétrissement (Hypothèse E5)

### 3.1. Volume d'Observations Acceptées face à la Censure Théorique

Le tableau ci-dessous confronte le nombre d'observations SMAP assimilées dans `DA_nocdf` (avec censure) et dans `DA_nocdf_nowilt` (sans censure) au volume de censure théorique déduit des fichiers SMAP bruts :

| Mois | Obs DA_nocdf | Obs DA_nowilt | Surplus Obs | Hausse (%) | Censure Théorique | Concordance (%) |
| --- | --- | --- | --- | --- | --- | --- |
| 201801.00 | 121390.00 | 185323.00 | 63933.00 | 52.67 | 71593.00 | 89.30 |
| 201802.00 | 104873.00 | 161076.00 | 56203.00 | 53.59 | 67725.00 | 82.99 |
| 201803.00 | 125382.00 | 229007.00 | 103625.00 | 82.65 | 108535.00 | 95.48 |
| 201804.00 | 138181.00 | 255836.00 | 117655.00 | 85.15 | 118123.00 | 99.60 |
| 201805.00 | 117545.00 | 228823.00 | 111278.00 | 94.67 | 111260.00 | 100.02 |

### Données quantitatives issues du tableau :
* La levée de la censure augmente le nombre d'observations acceptées de **+52.7 %** en janvier, **+82.7 %** en mars, et **+94.7 %** en mai.
* En mai, **+111278** observations supplémentaires sont injectées dans le filtre d'assimilation.
* La concordance entre le surplus réel d'observations et la censure théorique attendue est de **95.48 % en mars**, **99.60 % en avril** et **100.02 % en mai**.

![Observations acceptées mensuelles](figures/fig_e5_accepted_obs_monthly.png)

### 3.2. Réponse Hydrodynamique par Classe Texturale (Moyenne Printemps MAM)

| ID | Texture | Argile (%) | SMCWLT | ΔSM1 (nowilt - nocdf) | ΔSMcol (mm) | Incr EnKF nowilt | Incr EnKF nocdf | ΔET (mm/mois) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Sand | 3.00 | 0.0100 | -0.0015 | -0.0004 | -0.0006 | -0.0005 | -0.1467 |
| 3 | Sandy Loam | 10.00 | 0.0470 | -0.0134 | -0.0006 | -0.0014 | -0.0008 | -2.51 |
| 4 | Silt Loam | 13.00 | 0.0840 | -0.0466 | -0.0069 | -0.0032 | -0.0010 | -9.21 |
| 6 | Loam | 19.00 | 0.0660 | -0.0138 | -0.0003 | -0.0016 | -0.0008 | -3.35 |
| 7 | Sandy Clay Loam | 27.00 | 0.0690 | -0.0016 | -0.000057 | -0.0003 | -0.0002 | -0.4867 |
| 9 | Clay Loam | 34.00 | 0.1030 | -0.0168 | -0.0010 | -0.0026 | -0.0016 | -4.97 |
| 12 | Clay | 58.00 | 0.1380 | -0.0201 | -0.0020 | -0.0024 | -0.0014 | -7.24 |

### Données quantitatives issues du tableau :
* Sur sol argileux (Clay, 58 % argile, $\text{SMCWLT} = 0.138$), l'incrément moyen EnKF passe de **-0.00142** à **-0.00237**, provoquant un assèchement supplémentaire $\Delta\text{SM1}$ de **-0.0201 m³/m³** (colonne asséchée de **-0.00 mm**) et une baisse d'ET de **-7.24 mm/mois**.
* Sur sol limoneux (Silt Loam, $\text{SMCWLT} = 0.084$), l'assèchement additionnel $\Delta\text{SM1}$ est de **-0.0466 m³/m³** et la réduction d'ET atteint **-9.21 mm/mois**.

![Impact de la censure par texture](figures/fig_e5_nowilt_vs_da_and_ens.png)

---

## 4. Dynamique de Séchage Horaire et Cycle Diurne SMAP (Simulations Horaires 2018)

### 4.1. Dynamique de Ressuyage Post-Pluviale (OL_rsf2 vs OL_ctrl)

| Texture | Argile (%) | SMCWLT | τ ctrl (j) | τ rsf2 (j) | Δτ (j) | θres ctrl | θres rsf2 | P5 ctrl | P5 rsf2 | ≤WLT ctrl (%) | ≤WLT rsf2 (%) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sand | 3.00 | 0.0100 | 8.97 | 10.19 | 1.22 | 0.0763 | 0.0010 | 0.0096 | 0.0088 | 9.11 | 53.26 |
| Sandy Loam | 10.00 | 0.0470 | 8.03 | 13.05 | 5.02 | 0.1578 | 0.0615 | 0.0423 | 0.0347 | 9.16 | 24.07 |
| Silt Loam | 13.00 | 0.0840 | 7.96 | 12.69 | 4.73 | 0.1888 | 0.1419 | 0.0845 | 0.0780 | 4.32 | 22.72 |
| Loam | 19.00 | 0.0660 | 7.29 | 10.27 | 2.98 | 0.1684 | 0.0526 | 0.0576 | 0.0510 | 9.60 | 28.84 |
| Sandy Clay Loam | 27.00 | 0.0690 | 6.69 | 14.09 | 7.40 | 0.1635 | 0.0566 | 0.0741 | 0.0693 | 1.88 | 4.67 |
| Clay Loam | 34.00 | 0.1030 | 8.43 | 10.27 | 1.84 | 0.1741 | 0.1204 | 0.1221 | 0.1197 | 0.0000 | 0.0000 |
| Clay | 58.00 | 0.1380 | 8.68 | 12.84 | 4.16 | 0.1887 | 0.1868 | 0.1889 | 0.1895 | 0.0000 | 0.0000 |

### Données quantitatives issues du tableau :
* Pour la texture dominante Loam (19 % argile, 13 828 événements ajustés), le temps caractéristique de séchage médian $\tau$ passe de **7.29 jours** dans `ctrl` à **10.27 jours** dans `rsf2` ($\Delta\tau = +2.98\text{ j}$).
* L'humidité résiduelle $\theta_{\text{res}}$ chute de **0.168** dans `ctrl` à **0.053** dans `rsf2`.
* La fréquence à laquelle le sol superficiel passe sous le seuil $\text{SMCWLT}$ passe de **9.6 %** dans `ctrl` à **28.8 %** dans `rsf2` pour le Loam, et de **9.1 %** à **53.3 %** pour le Sable.

![Comparaison séchage rsf2 vs ctrl](figures/fig_ol_rsf2_vs_ctrl_drydown_tau_p5.png)

### 4.2. Biais d'Échantillonnage Temporel SMAP face à la Moyenne Journalière (Printemps MAM)

| Texture | Argile (%) | Biais 06h UTC (MAM) | Biais 18h UTC (MAM) | Amplitude Diurne (MAM) |
| --- | --- | --- | --- | --- |
| Sand | 3.00 | 0.0001 | -0.0002 | 0.0003 |
| Sandy Loam | 10.00 | 0.0015 | -0.0016 | 0.0031 |
| Silt Loam | 13.00 | 0.0026 | -0.0020 | 0.0046 |
| Loam | 19.00 | 0.0015 | -0.0017 | 0.0032 |
| Sandy Clay Loam | 27.00 | 0.0016 | -0.0016 | 0.0032 |
| Clay Loam | 34.00 | 0.0028 | -0.0032 | 0.0060 |
| Clay | 58.00 | 0.0034 | -0.0036 | 0.0070 |

### Données quantitatives issues du tableau :
* Le passage descendant (06:00 UTC) surestime systématiquement la moyenne 24h (+0.0001 à +0.0034 m³/m³).
* Le passage ascendant (18:00 UTC) sous-estime systématiquement la moyenne 24h (-0.0002 à -0.0036 m³/m³).
* L'amplitude diurne moyenne au printemps atteint **0.0070 m³/m³** (0.70 vol. %) sur sol argileux.

![Biais temporel SMAP](figures/fig_ol_overpass_vs_daily_mean.png)

---

## 5. Bilan d'Eau Complet et Conservation des Masses

### 5.1. Bilan d'Eau DA_nocdf − ENS_OPL (Confrontation aux Incréments EnKF)

Le tableau suivant présente le bilan d'eau mensuel intégré calculé à partir des restarts complets (SMC 4 couches + aquifère WA + canopée CANWAT + neige SNEQV) et des flux cumulés journaliers (Precipitation, ET, Qs, Qsb) pour la différence `DA_nocdf − ENS_OPL` :

| Mois | P ENS | P DA | ΔP | ΔET | ΔQs | ΔQsb | ΔStock ENS | ΔStock DA | Δ(ΔStock) | Bilan Flux | Résidu (mm) | Incrément EnKF (mm) | Écart (mm) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2018-01 | 44.63 | 44.63 | 0.0000 | -1.82 | 0.0500 | 0.7800 | 29.93 | 25.34 | -4.59 | 0.9800 | 5.58 | -8.70 | -3.12 |
| 2018-02 | 31.77 | 31.77 | -0.0000 | -6.56 | 0.1400 | 1.48 | 10.98 | 4.52 | -6.46 | 4.93 | 11.39 | -12.90 | -1.51 |
| 2018-03 | 56.52 | 56.52 | 0.0000 | -10.87 | 0.4000 | 2.07 | 16.00 | 0.8800 | -15.12 | 8.40 | 23.52 | -25.57 | -2.04 |
| 2018-04 | 46.27 | 46.27 | 0.0000 | -13.62 | 0.1600 | 1.51 | 1.60 | -7.81 | -9.41 | 11.95 | 21.36 | -22.48 | -1.12 |
| 2018-05 | 21.96 | 21.96 | -0.0000 | -18.16 | 0.0300 | 0.5800 | -25.42 | -25.40 | 0.0200 | 17.55 | 17.53 | -17.55 | -0.0200 |

#### Données quantitatives issues du tableau :
* En mai, la variation nette des flux $\Delta P - \Delta ET - \Delta Q_s - \Delta Q_{sb}$ est de **+17.55 mm**, la variation différentielle de stock $\Delta(\Delta\text{Stock})$ est de **+0.02 mm**, ce qui donne un résidu de bilan de **+17.53 mm**.
* Les incréments EnKF cumulés sur le mois de mai totalisent exactement **-17.55 mm** d'eau extraite.
* L'écart inexpliqué entre le résidu de bilan et l'incrément EnKF n'est que de **-0.02 mm** en mai (concordance supérieure à **99.8 %**).
* En mars, l'incrément EnKF totalise **-25.57 mm** d'eau extraite face à un résidu de bilan de **+23.52 mm** (écart de **-2.04 mm**).
* **Conclusion** : Le déficit d'eau de `DA_nocdf` par rapport à `ENS_OPL` est rigoureusement et quantitativement imputable aux incréments d'assimilation EnKF négatifs.

### 5.2. Bilan Interne de Chaque Simulation Seule ($P - ET - Q_s - Q_{sb} - \Delta\text{Stock}$)

Le tableau ci-dessous rapporte le résidu de bilan d'eau interne propre à chaque simulation, calculé individuellement à partir de ses flux cumulés et de ses restarts :

| Mois | Résidu Interne ENS (mm) | Résidu Interne DA (mm) | Incrément EnKF (mm) | Résidu Interne OL_DAIC (mm) |
| --- | --- | --- | --- | --- |
| 2018-01 | -3.61 | 1.97 | -8.70 | -0.3600 |
| 2018-02 | -4.89 | 6.50 | -12.90 | -0.2800 |
| 2018-03 | -7.85 | 15.67 | -25.57 | -0.4000 |
| 2018-04 | -6.73 | 14.62 | -22.48 | -0.3400 |
| 2018-05 | -8.46 | 9.07 | -17.55 | -0.3500 |

#### Données quantitatives issues du tableau :
* Pour `OL_DAIC_2018` (run 1 membre déterministe, sans perturbation ni DA), le résidu de fermeture est remarquable : **-0.36 mm** en janvier, **-0.28 mm** en février, **-0.40 mm** en mars, **-0.34 mm** en avril et **-0.35 mm** en mai. Noah-MP conserve donc la masse d'eau à moins de 0.40 mm/mois près.
* Pour `ENS_OPL_2018`, le résidu interne négatif (-3.61 à -8.46 mm/mois) s'explique par les perturbations d'état aléatoires additives injectées toutes les 3 heures sur la couche 1 d'humidité du sol.
* Pour `DA_nocdf_2018`, le résidu interne est positif et reflète exactement l'extraction d'eau par les incréments d'assimilation EnKF.

### 5.3. Bilan d'Eau Différentiel ENS_OPL − OL_DAIC (Effet d'Ensemble Pur)

Le tableau ci-dessous présente le bilan d'eau mensuel complet entre la moyenne d'ensemble sans assimilation (`ENS_OPL_2018`, 20 membres) et le run déterministe 1 membre (`OL_DAIC_2018`), en utilisant le forçage pluviométrique déterministe $P_{\text{OPL}}$ :

| Mois | P ENS | P OL_DAIC | ΔP | ΔET | ΔQs | ΔQsb | ΔStock ENS | ΔStock OL | Δ(ΔStock) | Bilan Flux | Résidu (mm) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2018-01 | 44.63 | 44.52 | 0.1100 | 2.81 | 0.0400 | 0.3300 | 29.93 | 29.76 | 0.1700 | -3.07 | -3.25 |
| 2018-02 | 31.77 | 31.70 | 0.0800 | 4.31 | 0.0300 | 0.2200 | 10.98 | 10.86 | 0.1200 | -4.49 | -4.61 |
| 2018-03 | 56.52 | 56.39 | 0.1400 | 5.86 | 0.1900 | 0.8900 | 16.00 | 15.35 | 0.6500 | -6.79 | -7.45 |
| 2018-04 | 46.27 | 46.16 | 0.1200 | 5.75 | 0.0900 | 0.4600 | 1.60 | 1.39 | 0.2000 | -6.19 | -6.39 |
| 2018-05 | 21.96 | 21.90 | 0.0500 | 7.54 | 0.0200 | 0.3700 | -25.42 | -25.65 | 0.2400 | -7.88 | -8.11 |

#### Données quantitatives issues du tableau :
* $\Delta P = P_{\text{ENS}} - P_{\text{OL}}$ est infime : **+0.11 mm** en janvier, **+0.08 mm** en février, **+0.14 mm** en mars, **+0.12 mm** en avril, **+0.05 mm** en mai (écart maximal de **0.14 mm/mois < 1 mm/mois**), confirmant la stricte conservation du forçage pluviométrique dans l'ensemble.
* L'excédent d'évapotranspiration $\Delta ET$ (+2.81 mm en janvier à +7.54 mm en mai) quantifie la non-linéarité stomatique et racinaire induite par les perturbations météorologiques sur l'ensemble des membres.
* La variation différentielle de stock $\Delta(\Delta\text{Stock})$ reste modérée (+0.12 à +0.65 mm), démontrant que le membre représentatif reproduit fidèlement la trajectoire d'accumulation hydrique moyenne.

---

## 6. Liste des Fichiers CSV Sources du Dossier

Tous les tableaux ci-dessus sont directement générés à partir des 10 fichiers suivants :
1. `e6_ensemble_effect_monthly.csv`
2. `e6_boundary_truncation_ens_opl.csv`
3. `e6_member_truncation_restarts.csv`
4. `e5_censorship_obs_count_monthly.csv`
5. `e5_nowilt_impact_by_texture.csv`
6. `ol_hourly_drydown_comparison.csv`
7. `ol_smap_overpass_sampling_bias.csv`
8. `water_balance_da_minus_ens_monthly.csv`
9. `water_balance_ens_minus_daic_monthly.csv`
10. `internal_water_balance_monthly.csv`
