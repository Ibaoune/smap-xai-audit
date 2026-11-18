# Réponses Documentées aux Questions Ouvertes du Manuscrit

Ce document synthétise les réponses aux cinq questions ouvertes relatives aux réglages de modélisation Noah-MP/LIS, à l'assimilation EnKF, à la procédure de CDF matching, au routage HyMAP et aux stations hydrométriques. Chaque élément est indexé par ses fichiers sources et numéros de lignes précis.

---

## Question 1 : Profondeur de la Nappe Phréatique ($Z_{\text{WT}}$) dans l'Open-Loop (OL)

- **Présence en sortie** : **OUI**, la variable est activée dans la table de sorties de production et présente dans tous les fichiers NetCDF journaliers de l'OL (`WaterTableD_tavg`).
- **Schéma d'eaux souterraines** : Schéma SIMGM (Simple Groundwater Model, Niu et al. 2007) avec aquifère non confiné sous la colonne de sol de 2 m et nappe phréatique dynamique à 2 voies (recharge et drainage latéral).
- **Sources** :
  - Table de sorties : [`experiments/NorthMor/matrix_2016_2020/shared/MODEL_OUTPUT_LIST.TBL`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/shared/MODEL_OUTPUT_LIST.TBL#L78) :
    `WaterTableD: 1 m - 1 0 0 1 174 1 # Water table depth (m)` (Ligne 78).
  - Configuration Noah-MP : [`experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/config/lis_OPL_noirr_2016_2020.config`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/config/lis_OPL_noirr_2016_2020.config#L92) :
    `Noah-MP.4.0.1 runoff and groundwater option: 1` (Ligne 92).

---

## Question 2 : Spécifications Complètes du CDF Matching

- **Échelle spatiale** : **Pixel par pixel** (aucun regroupement par classe). Le domaine contient $N_{\text{grid}} = 16\,030$ mailles terrestres sur la grille 121×181.
- **Période d'étalonnage** : **5 ans entiers**, du **1er janvier 2016 au 1er janvier 2021** (période d'audit complète).
- **Stratification temporelle** : **Stratification mensuelle indépendante** ($N_{\text{times}} = 12$ mois). Une fonction de transfert CDF distincte est calculée pour chaque mois de l'année.
- **Nombre de quantiles (bins)** : **100 bins** (centiles de 1 % à 100 %).
- **Sources** :
  - Configuration LDT : [`experiments/NorthMor/matrix_2016_2020/CDF/ldt.config.cdf.model.NorthMor`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/CDF/ldt.config.cdf.model.NorthMor#L140-L141) :
    - Ligne 140 : `Number of bins to use in the CDF: 100`
    - Ligne 141 : `Temporal resolution of CDF: "monthly"`
    - Lignes 164–175 : Dates de début `2016 01 01 00 00` et fin `2021 01 01 00 00`.
  - Fichier NetCDF de distribution : `experiments/NorthMor/matrix_2016_2020/CDF/OUTPUT_model_NorthMor/noahmp_model_cdf_NorthMor.nc` (dimensions : `ngrid = 16030`, `ntimes = 12`, `nbins = 100`).

---

## Question 3 : Erreur d'Observation SMAP et Réglages des Perturbations Stochastiques

- **Erreur d'observation SMAP** :
  - Type : Additif, écart-type $\sigma_o = 0.04\text{ m}^3/\text{m}^3$.
  - Décorrélation temporelle : $43\,200\text{ s}$ (12 heures).
  - Décorrélation spatiale : $0.25^\circ$ (~25 km).
  - Source : [`data/pert_package/smap_pertattribs.txt`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/pert_package/smap_pertattribs.txt#L1-L3) (Lignes 1–3).
- **Perturbations des forçages atmosphériques (Schéma GMAO)** :
  - Rayonnement solaire incident (SW) : Multiplicatif, $\sigma = 0.30$, temps de corrélation $\tau = 86\,400\text{ s}$ (24 h).
  - Précipitation convective et stratiforme : Multiplicatif, $\sigma = 0.50$, $\tau = 86\,400\text{ s}$ (24 h).
  - Corrélation croisée (SW vs Pluie) : **$-0.80$** (physiquement cohérent avec la nébulosité).
  - Source : [`data/pert_package/forcing_pertattribs.txt`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/pert_package/forcing_pertattribs.txt#L1-L6) (Lignes 1–6).
- **Perturbations de l'état (Humidité du sol)** :
  - Couche 1 (0–10 cm) : Additif, $\sigma = 0.004\text{ m}^3/\text{m}^3$, $\tau = 43\,200\text{ s}$ (12 h).
  - Couches 2, 3, 4 : Non perturbées directement (mise à jour par covariance EnKF).
  - Source : [`data/pert_package/noahmp_sm_pertattribs.txt`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/pert_package/noahmp_sm_pertattribs.txt#L1-L3) (Lignes 1–3).

---

## Question 4 : Paramètres et Formulation du Modèle de Routage HyMAP

- **Source du Modèle Numérique de Terrain (MNT)** : **MERIT-Hydro** à 3 secondes d'arc (~90 m), sur la projection LIS NorthMor 5 km.
  - Source : [`experiments/NorthMor/routing/configs/ldt_hymap2.config`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/routing/configs/ldt_hymap2.config#L28-L45) et grille `ldt_hymap/lis_input_corrigee.d01.nc`.
- **Formulation hydrodynamique** : **Onde cinématique** (Kinematic wave router) résolue par méthode explicite le long du réseau hydrographique dérivé de MERIT-Hydro.
  - Source : [`experiments/NorthMor/routing/configs/lis_hymap2_da_nocdf_2016_2020.config`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/routing/configs/lis_hymap2_da_nocdf_2016_2020.config#L85-L95).
- **Pas de temps de routage** : **15 minutes** (`HYMAP2 routing model time step: 15mn`).
  - Source : [`experiments/NorthMor/routing/configs/lis_hymap2_da_nocdf_2016_2020.config`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/routing/configs/lis_hymap2_da_nocdf_2016_2020.config#L88) (Ligne 88).
- **Réservoir linéaire (Linear Reservoir Flag)** : **Désactivé** (`flag = 0`) dans le run standard (`linres0`) ; activé (`flag = 1`) dans la sensibilité historique avec réservoir d'eaux souterraines linéaire.
  - Source : [`experiments/NorthMor/routing/configs/lis_hymap2_da_nocdf_2016_2020.config`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/routing/configs/lis_hymap2_da_nocdf_2016_2020.config#L92) (Ligne 92).

---

## Question 5 : Stations Hydrométriques de Débit Disponibles

Les 12 stations de référence suivies par les Agences de Bassin Hydraulique du Sebou (ABHS) et du Bouregreg-Chaouia (ABHBC) sont récapitulées ci-dessous :

| Nom de la Station | Bassin | Latitude (°N) | Longitude (°W) | Aire Drainée (km²) | Position par rapport aux Barrages | Taux Couverture (2016–2020) |
|:------------------|:------:|:-------------:|:--------------:|:------------------:|:----------------------------------|:---------------------------:|
| **Mjara** | Ouergha (Sebou) | 34.542 | -4.981 | 3 950 | **Amont direct barrage Al Wahda** | 94.2 % |
| **Ratba** | Ouergha (Sebou) | 34.618 | -4.712 | 1 420 | **Amont barrage Al Wahda** | 89.6 % |
| **Tabouda** | Ouergha (Sebou) | 34.654 | -4.510 | 830 | **Amont barrage Al Wahda** | 91.0 % |
| **Ain Timedrine** | Ouergha aval | 34.425 | -5.412 | 6 150 | **Aval barrage Al Wahda** | 87.4 % |
| **Azib Soltane** | Sebou moyen | 34.180 | -4.850 | 12 400 | Amont confluence Ouergha / Sebou | 96.8 % |
| **Ain Aicha** | Oued Ouergha | 34.482 | -4.685 | 1 120 | Amont barrage Al Wahda | 88.5 % |
| **Sidi Jabeur** | Oued Inaouene | 34.210 | -4.312 | 3 240 | Amont barrage Idriss 1er (affluent Sebou) | 92.1 % |
| **Sidi Allal Tazi** | Bas Sebou | 34.520 | -6.310 | 38 500 | **Aval Al Wahda et exutoire Gharb** | 95.3 % |
| **Ras El Fathia** | Bouregreg | 33.512 | -6.490 | 7 420 | **Amont direct barrage SMBA** | 92.7 % |
| **Tsalat** | Bouregreg | 33.380 | -6.210 | 2 810 | **Amont barrage SMBA** | 86.4 % |
| **Ain Grou** | Oued Grou | 33.450 | -6.550 | 3 150 | **Amont barrage SMBA** | 89.1 % |
| **Sidi Amira** | Bouregreg aval | 33.950 | -6.820 | 9 850 | **Aval barrage SMBA** | 82.3 % |

- **Sources** :
  - Inventaire des stations : [`experiments/NorthMor/routing/stations/stations_sebou_bouregreg.csv`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/routing/stations/stations_sebou_bouregreg.csv)
  - Métriques et validation de débit : [`smap-xai-audit/reports/qc/streamflow/`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/qc/streamflow/)
