# Audit Scientifique - Point C : Analyse Irrigation GMIA & Différence de Différences (SMAP − OL)

Ce rapport documente l'audit du **Point C**, évaluant la relation entre l'écart d'humidité du sol **SMAP − Open-Loop (OL)** et l'irrigation répertoriée par la base globale **GMIA** (*Global Map of Irrigation Areas*, FAO, v5), agrégée à l'empreinte spatiale de SMAP (~36 km).

---

## 1. Contexte et Objectifs de l'Audit

1. **Agrégation de la fraction irriguée GMIA** à ~36 km (fenêtre de convolution $7 \times 7$ pixels sur la grille 5 km de LIS avec masque terre) et partition en 4 classes d'intensité d'irrigation :
   - `0–1 %` : Zone témoin (quasi-nulle / non irriguée)
   - `1–10 %` : Faiblement irriguée
   - `10–30 %` : Moyennement irriguée
   - `> 30 %` : Fortement irriguée
2. **Comparaison saisonnière estivale (Juillet–Août, JA 2016–2020)** :
   - (a) Toutes observations SMAP brutes valides
   - (b) Observations acceptées par le contrôle qualité LIS (QC)
3. **Différence de Différences ($\Delta\Delta = \text{JA} − \text{MA}$)** :
   - Mesure de l'accroissement estival d'écart d'humidité du sol : $D = \langle\text{SMAP} - \text{OL}\rangle_{\text{JA}} - \langle\text{SMAP} - \text{OL}\rangle_{\text{MA}}$.
   - Évaluation à occupation du sol contrôlée (IGBP) :
     - Cultures pures (Classe 12 : *Croplands*)
     - Cultures + Mosaïque (Classes 12 + 14)
     - Cultures + Prairies (Classes 12 + 10 : *Croplands + Grasslands*)
     - Cultures + Mosaïque + Prairies (Classes 12 + 14 + 10)
     - Ensemble des surfaces non forestières (Classes MODIS-IGBP > 4)
   - Analyse comparative pour la période quinquennale (2016–2020) et pour l'année spécifique pluvieuse 2018.

---

## 2. Configuration et Produits SMAP lus par LIS

### 2.1. Lignes SMAP dans `lis.config` pour l'expérience DA-NoCDF
Dans l'expérience `DA_nocdf_noirr_2016_2020` (fichiers `generated/configs/lis_DA_SMAP_nocdf_noirr_YYYY-MM.config`), la section d'assimilation SMAP est paramétrée ainsi :

```ini
#---------------------DATA ASSIMILATION ----------------------------------
#Data assimilation options
Number of data assimilation instances:                1
Data assimilation algorithm:                          "EnKF"
Data assimilation set:                                "SMAP(NASA) soil moisture"
Data assimilation exclude analysis increments:        0 
Data assimilation output interval for diagnostics:    "1da"
Data assimilation number of observation types:        1
Data assimilation output ensemble spread:             1
Data assimilation scaling strategy:                   "none"
Data assimilation observation domain file:            ./data/lis_input/lis_input_NorthMor_5km.nc
Data assimilation output processed observations:      1 
Data assimilation output innovations:                 1 
Number of state variables:                            4

SMAP(NASA) soil moisture data designation:            SPL3SMP_E
SMAP(NASA) soil moisture data directory:              ./data/observations/SMAP_SPL3SMP_E
SMAP(NASA) soil moisture apply SMAP QC flags:         1
SMAP(NASA) soil moisture Composite Release ID:        "R19"
SMAP(NASA) model CDF file:                            ./data/cdf/smap_model_cdf.nc
SMAP(NASA) observation CDF file:                      ./data/cdf/smap_obs_cdf.nc
SMAP(NASA) soil moisture number of bins in the CDF:   100
SMAP(NASA) soil moisture use scaled standard deviation model: 0
SMAP(NASA) CDF read option:                           1
```

### 2.2. Lecteur LIS et options de Contrôle Qualité (QC)
- **Module lecteur LIS** : `src/lisf/lis/dataassim/obs/NASA_SMAPsm/NASASMAPsm_Mod.F90` et routine de lecture HDF5 `read_NASASMAPsm.F90`.
- **Répertoire des données** : `./data/observations/SMAP_SPL3SMP_E` (chemin absolu : `/srv/lustre01/.../NoahMP_Morocco/data/observations/SMAP_SPL3SMP_E`).
- **Stratégie de mise à l'échelle (Scaling)** : `"none"`. L'assimilation DA-NoCDF ingère directement les observations brutes sans correction de biais CDF.
- **Règles de filtrage QC** :
  1. **Filtrage VWC** : rejet de l'observation si le contenu en eau de la végétation dépasse le seuil critique :
     $$\text{VWC} > 5.0\text{ kg/m}^2 \implies \text{observation rejetée (udef)}$$
  2. **Drapeau de qualité SMAP** : évaluation du bit 0 de la variable `retrieval_qual_flag` :
     $$\text{ibits}(\text{sm\_qa}, 0, 1) == 0 \implies \text{qualité recommandée}$$
     Si le bit 0 vaut 1, la mesure est flaguée invalide (`-9999.0`).
  3. **Valeurs physiques valides** : exclusion des valeurs manquantes ou hors bornes d'étalonnage.

---

## 3. Format des Fichiers SMAP et Variables HDF5

- **Produit satellite** : SMAP Enhanced L3 Radiometer Global Daily 9 km EASE-Grid Soil Moisture (`SPL3SMP_E`), Version 6 (`ECSVersionID = 006`, Release `R19240`).
- **Format des granules** : HDF5 (hiérarchique standard). Fichiers nommés sous la forme :
  `SMAP_L3_SM_P_E_YYYYMMDD_R19240_001.h5`
- **Résolution spatiale** : Grille globale cylindrique EASE-Grid 2.0 à 9 km ($1624\text{ lignes} \times 3856\text{ colonnes}$).
- **Groupes et Variables HDF5** :
  - **Passage descendant AM (~06:00 heure solaire locale)** :
    - Groupe : `/Soil_Moisture_Retrieval_Data_AM`
    - Humidité du sol : `soil_moisture` (type `float32`, unité $\text{m}^3/\text{m}^3$, algorithme par défaut DCA/SCA)
    - Qualité d'inversion : `retrieval_qual_flag` (type `uint16`, masque binaire de qualité)
    - Végétation : `vegetation_water_content` (type `float32`, $\text{kg/m}^2$)
  - **Passage ascendant PM (~18:00 heure solaire locale)** :
    - Groupe : `/Soil_Moisture_Retrieval_Data_PM`
    - Humidité du sol : `soil_moisture_pm` (type `float32`, $\text{m}^3/\text{m}^3$)
    - Qualité d'inversion : `retrieval_qual_flag_pm` (type `uint16`)
    - Végétation : `vegetation_water_content_pm` (type `float32`, $\text{kg/m}^2$)
- **Priorité des orbites dans LIS** : Les données du matin (AM, 06:00) sont prioritaires ; le passage du soir (PM, 18:00) n'est injecté que là où la trace AM est absente.

---

## 4. Sources Exactes Utilisées par le Script d'Audit

Le script `scripts/audits/point_c_gmia_and_diff_in_diff.py` exploite directement les sorties binaires et NetCDF du cluster :

### 4.1. Données SMAP
- **Chemin** : `/srv/lustre01/.../NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output/YYYY-MM/DAOBS/YYYYMM/`
- **Fichiers** : `LISDAOBS_YYYYMMDDHHMM.1gs4r` (fichiers binaires directs GrADS écrits par LIS).
- **Heures de passage effectives** : `06:00`, `07:00`, `18:00`, `19:00 UTC`.
- **Structure binaire** : Chaque fichier contient deux enregistrements séquentiels Fortran (`>i4`, `>f4` de taille 21 901 flottants, correspondant à la grille 5 km du domaine Nord-Maroc $121 \times 181$) :
  - `rec1` : Observation SMAP projetée sur la grille LIS avant filtrage QC complet (**toutes observations brutes valides**).
  - `rec2` : Observation SMAP conservée après application stricte des filtres QC (**observations acceptées par le QC**).

### 4.2. Données Open-Loop (OL)
- **Chemin** : `/srv/lustre01/.../NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/output/YYYY-MM/SURFACEMODEL/YYYYMM/` (avec fallback sur `CDF/combined_OPL_noirr/SURFACEMODEL/YYYYMM/`).
- **Fichiers** : `LIS_HIST_YYYYMMDD0000.d01.nc` (fichiers journaliers NetCDF de synthèse écrits à 00:00:00 UTC le lendemain, intégrant la moyenne journalière sur 24h).
- **Variable** : `SoilMoist_tavg` (humidité volumique du sol moyenne sur 24h).
- **Couche** : Couche 1 (`SoilMoist_tavg[0, :, :]`), correspondant à la tranche superficielle $0 - 10\text{ cm}$.
- **Unité** : $\text{m}^3/\text{m}^3$.

---

## 5. Résultats Synthétiques de l'Audit

Les résultats détaillés sont stockés dans ce dossier sous forme de tables CSV, d'un fichier NPZ des distributions spatiales, et d'une figure haute résolution :

- `point_c_raw_output.txt` : Sortie texte brute générée par le script d'audit.
- `smap_ol_bias_ja_2016_2020.csv` : Biais moyen et médian SMAP − OL en Juillet-Août (toutes obs vs QC acceptées).
- `diff_in_diff_2016_2020.csv` : Différence de différences $\Delta\Delta$ (JA − MA) pour 2016–2020 avec IC bootstrap 95%.
- `diff_in_diff_2018.csv` : Différence de différences $\Delta\Delta$ spécifique à l'année 2018 avec IC bootstrap 95%.
- `mann_whitney_tests.csv` : Tests statistiques U de Mann-Whitney comparant la classe témoin (0–1 %) à chaque classe irriguée.
- `point_c_pixel_distributions.npz` : Grilles 2D ($121 \times 181$) de toutes les variables et masques.
- `diff_in_diff_by_gmia_class.png` et `.pdf` : Figure comparative avec barres d'erreur bootstrap à 95% et $N$ annoté.

### 5.1. Biais estival SMAP − OL en Juillet-Août (2016–2020)
*Sur pixels non-forêt (`vegt > 4`) :*

| Classe GMIA 36km | N pixels | (a) Toutes obs : Moyenne | (a) Médiane | (b) QC acc : Moyenne | (b) Médiane | $\Delta$ (b) − (a) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **0–1 %** | 6384 | +0.01462 m³/m³ | +0.01261 | +0.01934 m³/m³ | +0.01840 | +0.00472 |
| **1–10 %** | 3024 | +0.02000 m³/m³ | +0.02109 | +0.02580 m³/m³ | +0.02659 | +0.00580 |
| **10–30 %** | 461 | +0.01315 m³/m³ | +0.01109 | +0.02875 m³/m³ | +0.02854 | +0.01560 |
| **> 30 %** | 133 | -0.02081 m³/m³ | -0.01924 | +0.00901 m³/m³ | +0.00680 | +0.02982 |

> **Constat majeur sur le QC** : Dans les zones fortement irriguées (> 30 %), les observations brutes SMAP sont plus sèches que l'OL (-0.02081 m³/m³). Le filtre QC élimine massivement les valeurs basses ou perturbées, relevant la moyenne de +0.02982 m³/m³ (6 fois plus que sur les zones non irriguées).

### 5.2. Différence de Différences ($\Delta\Delta$ = JA − MA)

#### Période Quinquennale 2016–2020 :
- **Cultures seules (Classe 12)** :
  - 0–1 % : Moyenne = +0.03323 m³/m³ [IC95% : 0.02845, 0.03798], Médiane = +0.04300 ($N=148$)
  - 1–10 % : Moyenne = +0.02524 m³/m³ [IC95% : 0.02118, 0.02926], Médiane = +0.03754 ($N=283$)
  - 10–30 % : Moyenne = +0.02635 m³/m³ [IC95% : 0.01969, 0.03327], Médiane = +0.02639 ($N=93$)
  - \> 30 % : Moyenne = +0.04140 m³/m³ [IC95% : 0.03832, 0.04444], Médiane = +0.04191 ($N=147$)
  - *Test Mann-Whitney vs 0–1 %* : Pour > 30 %, $p = 0.177$ (non significatif). L'accroissement estival pluriannuel des cultures irriguées n'est pas statistiquement distinct des cultures pluviales non irriguées.
- **Cultures + Prairies (Classes 12 + 10)** :
  - 0–1 % : Moyenne = +0.06848 m³/m³, Médiane = +0.07325 ($N=394$)
  - 1–10 % : Moyenne = +0.03433 m³/m³, Médiane = +0.04482 ($N=437$, $p < 0.0001$)
  - 10–30 % : Moyenne = +0.03069 m³/m³, Médiane = +0.03097 ($N=130$, $p < 0.0001$)
  - \> 30 % : Moyenne = +0.04323 m³/m³, Médiane = +0.04380 ($N=169$, $p < 0.0001$)
  - *Constat* : Les zones témoins (0–1 %) affichent un accroissement estival plus prononcé que les zones irriguées en raison du dessèchement prononcé de l'Open-Loop en conditions naturelles non perturbées.

#### Année Spécifique 2018 :
- **Cultures seules (Classe 12)** :
  - 0–1 % : Moyenne = +0.01234 m³/m³, Médiane = +0.01720 ($N=144$)
  - 1–10 % : Moyenne = +0.01122 m³/m³, Médiane = +0.00983 ($N=279$, $p = 0.714$)
  - 10–30 % : Moyenne = +0.03444 m³/m³, Médiane = +0.02228 ($N=93$, $p < 0.0001$)
  - \> 30 % : Moyenne = +0.04930 m³/m³, Médiane = +0.05216 ($N=147$, $p < 0.0001$)
  - *Constat* : En 2018 (année pluvieuse), les cultures intensément irriguées (> 30 %) présentent un signal d'accroissement estival significativement quadruplé par rapport aux cultures sèches témoin (+0.04930 vs +0.01234 m³/m³, $p < 0.0001$).
