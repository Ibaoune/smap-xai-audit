# Traçabilité et provenance des résultats Random Forest DA-NoCDF (Support natif)

**Date d'audit :** 30 octobre 2026  
**Dépôt :** `/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit`  
**Auteur :** Antigravity (CLEAN-03E)  
**Référence d'invalidation CDF :** [`docs/invalidated_legacy_cdf_results.md`](invalidated_legacy_cdf_results.md)  

---

## 1. Objet et périmètre

Le présent document consigne la provenance, les métadonnées et les performances d'évaluation du premier lot de modèles Random Forest (RF) scientifiquement vérifiés et reproductibles issus de la simulation d'assimilation **DA-NoCDF** (sans correction CDF préalable).

Suite à l'invalidation des anciennes sorties DA-CDF documentée dans [`docs/invalidated_legacy_cdf_results.md`](invalidated_legacy_cdf_results.md), ce lot est strictement restreint aux modèles entraînés et évalués sur le **support natif (`native_support`)**. Tous les résultats issus du support apparié (`matched_support`) ou dépendant directement de la simulation DA-CDF antérieure au 27 octobre 2026 sont formellement exclus de ce périmètre.

---

## 2. Provenance des données sources

Les modèles et métriques consignés reposent exclusivement sur les chaînes de données suivantes :

### 2.1. Simulations terrestres LIS / Noah-MP (Domaine NorthMor)
- **DA-NoCDF :** Simulation d'assimilation EnKF des observations SMAP brutes (sans redimensionnement CDF préalable), exécutée sur la grille NorthMor (121 $\times$ 181 mailles, 16 030 pixels continentaux actifs).
- **OPL (Open-Loop) :** Simulation de contrôle sans assimilation, partageant la même géométrie, la même météorologie de forçage et la même paramétrisation des états initiaux.
- **Chemins d'accès intermédiaires :**
  - Données d'incréments journaliers EnKF : `data/processed/daily_enkf/da_nocdf/`
  - Trajectoires journalières d'états et de flux : `data/interim/noahmp/da_nocdf/` et `data/interim/noahmp/opl/`
  - Forçages météorologiques atmosphériques : `data/interim/noahmp/forcing/`

### 2.2. Données satellitaires indépendantes pour le bloc VALUE
- **Jeu de données :** GLEAM (*Global Land Evaporation Amsterdam Model*).
- **Version exacte vérifiée dans les métadonnées NetCDF :** **GLEAM v4.3a** (et non v3.8a).
  - *Auteurs :* Hydro-Climate Extremes Lab (H-CEL), Université de Gand.
  - *Référence :* Miralles, D.G. et al. 2025: *Global land evaporation and soil moisture dataset at 0.1° resolution from 1980 to near present*, Scientific Data, 12, 416, doi: [10.1038/s41597-025-04610-y](https://doi.org/10.1038/s41597-025-04610-y).
  - *Fichiers sources bruts :* `/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/validation/evapotranspiration/GLEAM/raw/E_*_GLEAM_v4.3a.nc`
  - *Agrégation spatiale :* Projection et recouvrement exact des aires sur la maille $0.25^\circ$ GLEAM (4 110 pixels actifs sur le domaine d'étude).

---

## 3. Protocoles temporels et absence de fuite (*data leakage*)

Les modèles ont été entraînés et testés selon le protocole de scellement strict défini dans `configs/modeling/splits.yaml` :
- **Entraînement final (*refit*) :** 2016-01-08 au 2019-12-31 (4 années hydrologiques complètes).
- **Test d'évaluation scellé (*holdout*) :** 2020-01-01 au 2020-12-31 (1 année indépendante).
- **Contrôles de non-fuite :**
  - Tous les prédicteurs dynamiques retardés (`ssm_lag1`, `precip_pre3d_sum`, `precip_pre7d_sum`, etc.) sont strictement calculés vers le passé ($t-1$ à $t-7$).
  - Aucun échantillon de l'année 2020 n'a été exposé à l'apprentissage (assertions bloquantes dans `05_refit_final_rf_2016_2019.py`).

---

## 4. Synthèse des modèles et métriques d'évaluation 2020

Les modèles ont été scellés sous le commit `bb777c91889d76ecab02067520c9a9f948f3563e` (`FINAL_REFIT_PRE_2020`).

| Bloc | Variable cible | Unité | Config RF | Prédicteurs | $N_{\text{train}}$ (2016–2019) | $N_{\text{test}}$ (2020) | $R^2$ | Pearson $r$ | MAE | RMSE | Biais | MAE Skill | RMSE Skill |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SOURCE** | `daily_absolute_increment` | $\text{m}^3\,\text{m}^{-3}$ | RF_A | 35 | 5 881 531 | 1 596 590 | 0.247 | 0.497 | 0.0081 | 0.0132 | -0.00018 | 0.154 | 0.144 |
| **TRANSFER** | `delta_rzsm` | $\text{m}^3\,\text{m}^{-3}$ | RF_A | 52 | 23 307 620 | 5 866 980 | 0.475 | 0.709 | 0.0147 | 0.0217 | +0.00201 | 0.330 | 0.279 |
| **TRANSFER** | `delta_et` | $\text{mm}\,\text{d}^{-1}$ | RF_A | 52 | 23 307 620 | 5 866 980 | 0.567 | 0.760 | 0.1498 | 0.2506 | -0.03793 | 0.412 | 0.325 |
| **TRANSFER** | `delta_surface_runoff` | $\text{mm}\,\text{d}^{-1}$ | RF_A | 52 | 23 307 620 | 5 866 980 | 0.465 | 0.723 | 0.0026 | 0.0385 | -0.00078 | 0.550 | 0.269 |
| **TRANSFER** | `delta_baseflow` | $\text{mm}\,\text{d}^{-1}$ | RF_A | 52 | 23 307 620 | 5 866 980 | 0.329 | 0.601 | 0.0286 | 0.1809 | -0.01230 | 0.498 | 0.182 |
| **VALUE** | `value_ae` | $\text{mm}\,\text{d}^{-1}$ | RF_B | 52 | 5 975 940 | 1 504 260 | 0.311 | 0.568 | 0.1484 | 0.2400 | +0.01495 | 0.222 | 0.164 |

*Note sur les baselines :* Les scores de skill relatifs ($\text{Skill} = 1 - \text{Metric}_{\text{RF}} / \text{Metric}_{\text{baseline}}$) sont calculés par rapport à une climatologie mensuelle d'entraînement (médiane mensuelle pour SOURCE et VALUE, moyenne mensuelle pour TRANSFER).

---

## 5. Précision épistémologique et limites

1. **Nature des performances :**  
   Les métriques ci-dessus mesurent strictement **l'adéquation prédictive statistique** des modèles Random Forest vis-à-vis des cibles diagnostiques et des trajectoires de modèles définies par le protocole d'audit. Elles **ne constituent pas une validation hydrologique indépendante** de la réalité physique des flux sur le terrain (absence de données de validation in situ de débit jaugé ou de tours à flux eddy-covariance).
2. **Absence de comparaison avec DA-CDF :**  
   Ces résultats représentent le comportement intrinsèque de la chaîne DA-NoCDF. Aucune conclusion comparative relative vis-à-vis de l'assimilation avec correction CDF ne peut être tirée de ce lot, la simulation DA-CDF corrigée étant en cours d'exécution.
3. **Exclusion du support apparié :**  
   Le modèle `SOURCE da_nocdf (matched_support)` ($N_{\text{test}} = 596\,877$), bien qu'entraîné sur des cibles NoCDF, a vu sa cohorte conditionnée par les masques d'assimilation de l'ancienne CDF invalide. Il est donc écarté de ce premier lot validé et sera régénéré ultérieurement.

---

## 6. Livrables associés et reproductibilité

- **Tableau de données exporté :** [`tables/audit/nocdf_native_rf_2020_metrics.csv`](../tables/audit/nocdf_native_rf_2020_metrics.csv)
- **Figure de diagnostic :** [`figures/audit/nocdf_native_rf_2020_metrics.pdf`](../figures/audit/nocdf_native_rf_2020_metrics.pdf) et [`figures/audit/nocdf_native_rf_2020_metrics.png`](../figures/audit/nocdf_native_rf_2020_metrics.png)
- **Script déterministe producteur :** [`scripts/audits/export_nocdf_native_rf_metrics.py`](../scripts/audits/export_nocdf_native_rf_metrics.py)

Pour régénérer l'ensemble des livrables de façon déterministe à partir des sorties figées du dépôt :
```bash
python3 scripts/audits/export_nocdf_native_rf_metrics.py
```
