# Synthèse des Expériences de Sensibilité — Mars 2018
**Date de génération :** 2026-11-19 16:13:54
**Branche Git :** `elaabar` | **Rapport d'audit :** Neutre, purement descriptif, sans interprétation.
---
## 1. Bilan Interne ($P - ET - Q_s - Q_{sb} - \Delta\text{Stock}$) — Mars 2018
Formule : $\text{Résidu} = P - ET - Q_s - Q_{sb} - \Delta\text{Stock}$
Stock total = 4 couches SMC + WA + CANWAT + SNEQV (moyenne d'ensemble sur pixels terrestres).

| run | P_mm | ET_mm | Qs_mm | Qsb_mm | dStock_mm | Residu_mm | Stock_start_mm | Stock_end_mm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ENS_OPL_2018 | 56.52 | 41.35 | 2.79 | 4.23 | 16.0 | -7.85 | 5228.59 | 5244.59 |
| OL_DAIC_2018 | 56.39 | 35.49 | 2.61 | 3.34 | 15.35 | -0.4 | 5227.8 | 5243.15 |
| ENS_FORC_201803 | 56.52 | 36.23 | 2.77 | 4.01 | 15.49 | -1.98 | 5228.59 | 5244.08 |
| ENS_STATE_201803 | 56.39 | 41.47 | 2.79 | 4.24 | 16.15 | -8.26 | 5228.59 | 5244.74 |
| ENS_NOSTATE_201803 | 56.52 | 35.51 | 2.77 | 3.89 | 14.71 | -0.35 | 5228.59 | 5243.29 |

Fichier source : `sensitivity_internal_water_balance_201803.csv`

---
## 2. Différence Maximale Absolue ENS_FORC − ENS_OPL au 31 Mars 2018

| variable | level | source | max_abs_diff | mean_abs_diff | is_exact_zero |
| --- | --- | --- | --- | --- | --- |
| ET_daily_avg (Evap_tavg) | Surface | LIS_HIST_201804010000 (31 Mars) | 1.2606208324432373 | 0.22832622183016218 | False |
| SoilMoist_daily_avg (Layer 1) | Layer 1 | LIS_HIST_201804010000 (31 Mars) | 0.053752198815345764 | 0.001627266206223743 | False |
| SoilMoist_daily_avg (Layer 2) | Layer 2 | LIS_HIST_201804010000 (31 Mars) | 0.03887799382209778 | 0.0004276291697901335 | False |
| SoilMoist_daily_avg (Layer 3) | Layer 3 | LIS_HIST_201804010000 (31 Mars) | 0.027320146560668945 | 0.00028217527469247115 | False |
| SoilMoist_daily_avg (Layer 4) | Layer 4 | LIS_HIST_201804010000 (31 Mars) | 0.04252326488494873 | 0.00017545150357042337 | False |
| SMC_restart_members (Layer 1) | Layer 1 | LIS_RST_NOAHMP401_201803312345 (23:45) | 0.3578389883041382 | 0.043099720860301 | False |
| SMC_restart_ens_mean (Layer 1) | Layer 1 | LIS_RST_NOAHMP401_201803312345 (23:45) | 0.05461697280406952 | 0.0019932602318985643 | False |
| SMC_restart_members (Layer 2) | Layer 2 | LIS_RST_NOAHMP401_201803312345 (23:45) | 0.15295881032943726 | 0.016280154337082815 | False |
| SMC_restart_ens_mean (Layer 2) | Layer 2 | LIS_RST_NOAHMP401_201803312345 (23:45) | 0.040408238768577576 | 0.0004972822875881374 | False |
| SMC_restart_members (Layer 3) | Layer 3 | LIS_RST_NOAHMP401_201803312345 (23:45) | 0.17384140193462372 | 0.00956931491977932 | False |
| SMC_restart_ens_mean (Layer 3) | Layer 3 | LIS_RST_NOAHMP401_201803312345 (23:45) | 0.027232617139816284 | 0.00029950424498940585 | False |
| SMC_restart_members (Layer 4) | Layer 4 | LIS_RST_NOAHMP401_201803312345 (23:45) | 0.1826780140399933 | 0.004761647244058991 | False |
| SMC_restart_ens_mean (Layer 4) | Layer 4 | LIS_RST_NOAHMP401_201803312345 (23:45) | 0.042201071977615356 | 0.00018273033503807861 | False |

Fichier source : `diff_ens_forc_vs_ens_opl_20180331.csv`

---
## 3. Détection des Remplacements de Membres (Moyenne Midrange $(max + min)/2$) dans ENS_FORC

| restart_file | n_members_all_4_layers_exact_mid | n_members_all_4_layers_close_1e6 | layer_1_exact_mid | layer_2_exact_mid | layer_3_exact_mid | layer_4_exact_mid | total_evaluated_members |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LIS_RST_NOAHMP401_201802282345.d01.nc | 0 | 1 | 0 | 0 | 1 | 57 | 320600 |
| LIS_RST_NOAHMP401_201803312345.d01.nc | 0 | 0 | 0 | 0 | 0 | 6 | 320600 |
| LIS_RST_NOAHMP401_201804010000.d01.nc | 78 | 78 | 79 | 78 | 79 | 86 | 320600 |

Fichier source : `ens_forc_midrange_replacement_counts.csv`

