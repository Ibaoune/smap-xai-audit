# Traçabilité et Invalidation Scientifique des Résultats DA-CDF de la Section 3.1

Ce document formalise l'état d'invalidation scientifique des figures et données sources de la **Section 3.1 (Figure 3 et Figures supplémentaires S1 à S3)** du projet `smap-xai-audit`, suite à l'identification d'une discordance de domaine spatial dans la fonction de distribution cumulative (CDF) utilisée lors de la simulation historique d'assimilation EnKF.

---

## 1. Cause scientifique de l'invalidation

### 1.1. Rôle du CDF matching dans l'assimilation SMAP
Dans la modélisation hydrologique Noah-MP sous Land Information System (LIS), l'assimilation de données SMAP par filtre de Kalman d'ensemble (EnKF) applique un opérateur de mise à l'échelle non linéaire (*CDF matching*, `LIS_rescale_with_CDF_matching` dans `LIS_dataAssimMod.F90`). Cet opérateur ajuste les observations satellitaires brutes sur la climatologie d'humidité de surface du modèle hôte afin de prévenir les chocs hydriques et les biais systématiques.

Pour que cet ajustement soit physiquement et numériquement cohérent, les tables de CDF doivent être calculées sur la grille et le masque terrestre strictement identiques à ceux de la simulation d'assimilation :
- Domaine d'étude **NorthMor** : $121 \times 181$ mailles, résolution $0.05^\circ$ ($30.00^\circ\text{N}$ à $36.00^\circ\text{N}$, $-10.00^\circ\text{W}$ à $-1.00^\circ\text{W}$).
- Masque terrestre : exactement **16 030 points terrestres** actifs (`LANDMASK == 1`).

### 1.2. Discordance spatiale de la simulation historique DA-CDF
L'ancienne simulation `DA_cdf_noirr_2016_2020` (exécutée en juillet 2026 sous `NoahMP_Morocco` et archivée dans `_archive_oldCDF_20261027`) utilisait les fichiers CDF déclarés dans ses configurations LIS (`generated/configs/lis_DA_SMAP_cdf_noirr_*.config`) :
```ini
SMAP(NASA) model CDF file:       ./experiments/NorthMor/matrix_2016_2020/CDF/OUTPUT_noirr/smap_cdf.nc
SMAP(NASA) observation CDF file: ./experiments/NorthMor/matrix_2016_2020/CDF/OUTPUT_noirr/smap_cdf.nc
```

L'examen technique de ces fichiers (vérifiable via [`scripts/audits/check_cdf_domain.py`](file:///home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/scripts/audits/check_cdf_domain.py) et [`scripts/audits/audit_cdf_validity.py`](file:///home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/scripts/audits/audit_cdf_validity.py)) met en évidence :

1. **Ce qui est DÉMONTRÉ :**
   - **Incompatibilité géométrique et de masque :** Le fichier domaine historique `smap_cdf_domain.nc` couvrait un domaine spatial distinct plus large, où le domaine NorthMor ne correspondait qu'à un sous-domaine interne (lignes 184:305, colonnes 146:327).
   - **Décalage d'indexation 1D (`ngrid`) :** Lors de l'exécution, LIS lit les CDF comme un vecteur séquentiel 1D de tuiles terrestres. La dimension `ngrid` de l'ancien fichier ne correspondait pas à l'ordre des 16 030 tuiles terrestres de la grille NorthMor, provoquant une attribution erronée des paramètres de mise à l'échelle d'un pixel à un autre.

2. **Ce qui est NON QUANTIFIÉ (absence de diagnostic comparatif définitif) :**
   - La part exacte attribuable à ce décalage spatial dans les anomalies d'innovations, la magnitude des incréments et les flux hydrologiques n'a pas encore été mesurée de manière comparative.
   - Il n'est pas démontré que cette anomalie géométrique explique à elle seule l'ensemble des rejets d'observations (par exemple au test de pente interquartile IQR `iqr < 0.05 * span`).
   - D'autres contrôles qualité actifs dans LIS et Noah-MP (température de surface, présence de neige, gel du sol, contrôle du seuil de flétrissement) participent également au filtrage des observations SMAP, indépendamment du calcul de la CDF.

---

## 2. Chronologie détaillée

| Date | Événement technique et méthodologique | Statut de validation |
|---|---|---|
| **Juillet 2026** | Exécution de la simulation historique `DA_cdf_noirr_2016_2020` dans `NoahMP_Morocco` avec l'ancien fichier CDF non aligné. | Invalide (anomalie non identifiée à cette date) |
| **23 Septembre 2026** | Prétraitement de cette simulation dans `smap-xai-audit` produisant les séries `data/processed/daily_enkf/da_cdf/daily_innovation/` et `daily_signed_increment/`. | Données dérivées de la simulation non alignée |
| **11 Octobre 2026 (12:58–15:50 UTC)** | Exécution de `scripts/postprocessing/manuscript/sec3.1/` : génération des figures et des données sources (Source Data) de la Section 3.1. | Sorties basées sur les entrées du 23/09 |
| **11 Octobre 2026 (16:03 UTC)** | Commit Git `b2f74f3` archivant dans le dépôt les versions PNG raster de la Section 3.1 (`Fig3_a_d_support.png`, etc.). | Commit historique conservé, contenu scientifique obsolète |
| **24–25 Octobre 2026** | Identification de la discordance spatiale via les scripts d'audit (`scripts/audits/check_cdf_domain.py`, `scripts/audits/audit_cdf_validity.py`). | Discordance géométrique formellement établie |
| **25 Octobre 2026** | Régénération des tables CDF alignées géométriquement sur le domaine NorthMor via LDT (`OUTPUT_model_NorthMor/noahmp_model_cdf_NorthMor.nc` et `OUTPUT_obs_NorthMor/smap_obs_cdf_NorthMor.nc`). | Tables CDF géométriquement conformes (16 030 mailles) ; impact dynamique sur l'assimilation restant à évaluer |
| **27 Octobre 2026 (19:23 UTC)** | Archivage de l'ancienne simulation vers `NoahMP_Morocco/.../DA_cdf_noirr_2016_2020/_archive_oldCDF_20261027/`. Lancement de la NOUVELLE simulation `DA_cdf_noirr_2016_2020` avec les CDF réalignées. | Simulation en cours d'exécution (évaluation scientifique en attente des sorties complètes) |
| **29 Octobre 2026** | Audit CLEAN-03B confirmant que tous les fichiers actuels de `figures/manuscript/section_3_1/` proviennent de l'ancien run. | Invalidation formalisée pour la Section 3.1 |

---

## 3. Inventaire des résultats de la Section 3.1 et statut scientifique

Les fichiers ci-dessous, situés dans [`figures/manuscript/section_3_1/`](file:///home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/figures/manuscript/section_3_1/), reposent sur la simulation historique DA-CDF ou sur une comparaison conjointe CDF / NoCDF :

| Fichier | Nature | Statut Git actuel | Script producteur | Dépendance d'entrée directe | Statut scientifique |
|---|---|:---:|---|---|:---:|
| `Fig3_a_d_support.png` | Figure raster (500 DPI) | Suivi (`b2f74f3`) | `plot_fig3.py` | `Fig3_a_d_source_data.*` | **INVALIDÉ (Comparatif)** |
| `Fig3_a_d_support.pdf` | Figure vectorielle | Non suivi (`??`) | `plot_fig3.py` | `Fig3_a_d_source_data.*` | **INVALIDÉ (Comparatif)** |
| `Fig3_a_d_source_data.csv` | Source Data tabulaire | Non suivi (`??`) | `process_fig3_data.py` | `daily_innovation_*.nc` (CDF & NoCDF) | **INVALIDÉ (Comparatif)** |
| `Fig3_a_d_source_data.nc` | Source Data grille NetCDF | Non suivi (`??`) | `process_fig3_data.py` | `daily_innovation_*.nc` (CDF & NoCDF) | **INVALIDÉ (Comparatif)** |
| `Fig3_e_h_matched_updates.png` | Figure raster (500 DPI) | Suivi (`b2f74f3`) | `plot_fig3.py` | `Fig3_e_h_source_data.*` | **INVALIDÉ (Apparié)** |
| `Fig3_e_h_matched_updates.pdf` | Figure vectorielle | Non suivi (`??`) | `plot_fig3.py` | `Fig3_e_h_source_data.*` | **INVALIDÉ (Apparié)** |
| `Fig3_e_h_source_data.csv` | Source Data tabulaire | Non suivi (`??`) | `process_fig3_data.py` | `daily_signed_increment_*.nc` | **INVALIDÉ (Apparié)** |
| `Fig3_e_h_source_data.nc` | Source Data grille NetCDF | Non suivi (`??`) | `process_fig3_data.py` | `daily_signed_increment_*.nc` | **INVALIDÉ (Apparié)** |
| `Fig3_qc_report.txt` | Rapport de contrôle numérique | Non suivi (`??`) | `process_fig3_data.py` | Sorties intermédiaires Fig 3 | **HISTORIQUE** |
| `matched_spatial_summary.csv` | Résumé statistique spatial | Non suivi (`??`) | `process_fig3_data.py` | Sorties intermédiaires Fig 3 | **INVALIDÉ (Apparié)** |
| `matched_increments_1d.npz` | Échantillons 1D appariés (18 Mo) | Ignoré (`.gitignore`) | `process_fig3_data.py` | Sorties intermédiaires Fig 3 | **INVALIDÉ (Apparié)** |
| `FigS1_sample_matching_sensitivity.png` | Figure raster (500 DPI) | Suivi (`b2f74f3`) | `plot_fig_s1.py` | `FigS1_source_data.csv` | **INVALIDÉ (Apparié)** |
| `FigS1_sample_matching_sensitivity.pdf` | Figure vectorielle | Non suivi (`??`) | `plot_fig_s1.py` | `FigS1_source_data.csv` | **INVALIDÉ (Apparié)** |
| `FigS1_source_data.csv` | Source Data tabulaire | Non suivi (`??`) | `process_supplementary_data.py` | `daily_signed_increment_*.nc` | **INVALIDÉ (Apparié)** |
| `FigS1_distributions.npz` | Distributions 1D (53 Mo) | Ignoré (`.gitignore`) | `process_supplementary_data.py` | `daily_signed_increment_*.nc` | **INVALIDÉ (Apparié)** |
| `FigS1_S3_qc_report.txt` | Rapport de contrôle numérique | Non suivi (`??`) | `process_supplementary_data.py` | Sorties intermédiaires Fig S1–S3 | **HISTORIQUE** |
| `FigS2_seasonal_matched_differences.png` | Figure raster (500 DPI) | Suivi (`b2f74f3`) | `plot_fig_s2.py` | `FigS2_source_data.nc` | **INVALIDÉ (Apparié)** |
| `FigS2_seasonal_matched_differences.pdf` | Figure vectorielle | Non suivi (`??`) | `plot_fig_s2.py` | `FigS2_source_data.nc` | **INVALIDÉ (Apparié)** |
| `FigS2_source_data.nc` | Source Data grille saisonnière | Non suivi (`??`) | `process_supplementary_data.py` | `daily_signed_increment_*.nc` | **INVALIDÉ (Apparié)** |
| `FigS2_seasonal_summary.csv` | Résumé saisonnier | Non suivi (`??`) | `process_supplementary_data.py` | `daily_signed_increment_*.nc` | **INVALIDÉ (Apparié)** |
| `FigS3_water_accounting.png` | Figure raster (500 DPI) | Suivi (`b2f74f3`) | `plot_fig_s3.py` | Grille cumulée et CSV climatologie | **INVALIDÉ (Comparatif)** |
| `FigS3_water_accounting.pdf` | Figure vectorielle | Non suivi (`??`) | `plot_fig_s3.py` | Grille cumulée et CSV climatologie | **INVALIDÉ (Comparatif)** |
| `FigS3_monthly_climatology.csv` | Climatologie mensuelle ajustement | Non suivi (`??`) | `process_supplementary_data.py` | `daily_signed_increment_*.nc` | **INVALIDÉ (Comparatif)** |
| `FigS3_cumulative_map.nc` | Grille cumulée d'ajustement | Non suivi (`??`) | `process_supplementary_data.py` | `daily_signed_increment_*.nc` | **INVALIDÉ (Comparatif)** |
| `FigS3_water_accounting_summary.csv` | Synthèse bilan comptable eau | Non suivi (`??`) | `process_supplementary_data.py` | `daily_signed_increment_*.nc` | **INVALIDÉ (Comparatif)** |

### Distinction essentielle concernant l'expérience DA-NoCDF :
- **Résultats comparatifs ou appariés (CDF vs NoCDF) :** Invalidés pour publication, car l'échantillon apparié ($CDF > 0 \land NoCDF > 0$) et les écarts ($NoCDF - CDF$) dépendent directement des pas d'assimilation erronés de DA-CDF.
- **Résultats intrinsèques à DA-NoCDF :** Les métriques et diagnostics calculés **exclusivement** à partir de `DA_nocdf_noirr_2016_2020` (par exemple la fréquence de support natif NoCDF isolée dans le panneau 3b, ou les incréments natifs NoCDF sans conditionnement à CDF) **ne sont pas invalidés par cette anomalie**. Leur réutilisation reste scientifiquement envisageable sous réserve de vérifier l'absence d'interdépendance dans le code de post-traitement.

---

## 4. Statut du commit historique `b2f74f3`

Le 11 octobre 2026 à 16:03:28 +0100, le commit suivant a été enregistré sur la branche `elaabar` :
```
commit b2f74f35f299d9b626f2355ddfc6cb4e5fbf41e2
Author: M. El Aabaribaoune
Date:   Sun Oct 11 16:03:28 2026 +0100

    feat(manuscript): add Section 3.1  high-res PNG figures (Fig 3 and S1–S3)
```

Ce commit incluait les 5 images PNG raster :
- `figures/manuscript/section_3_1/Fig3_a_d_support.png`
- `figures/manuscript/section_3_1/Fig3_e_h_matched_updates.png`
- `figures/manuscript/section_3_1/FigS1_sample_matching_sensitivity.png`
- `figures/manuscript/section_3_1/FigS2_seasonal_matched_differences.png`
- `figures/manuscript/section_3_1/FigS3_water_accounting.png`

**Règle de gestion Git :**
- L'historique Git n'est pas réécrit : le commit `b2f74f3` reste intact en tant que jalon historique de l'état d'avancement au 11 octobre 2026.
- Les fichiers binaires PNG suivis par Git sont documentés comme scientifiquement obsolètes.
- Aucun des fichiers non suivis correspondants (PDF, CSV, NetCDF) ne doit être ajouté à l'index Git dans leur état actuel.

---

## 5. Conséquences pour le manuscrit

1. **Non-utilisabilité comme résultats définitifs :**
   Les chiffres rapportés dans le manuscrit concernant la fréquence spatiale du support natif de DA-CDF, le taux d'écart de support par rapport à DA-NoCDF, les statistiques des incréments appariés et le bilan volumétrique d'ajustement en eau de surface ne peuvent pas figurer comme résultats validés dans la version finale du papier.
2. **Portée des conclusions méthodologiques :**
   La problématique conceptuelle centrale du papier — à savoir que l'assimilation d'observations satellitaires avec et sans correction de biais induit des supports spatiotemporels hétérogènes justifiant un appariement rigoureux des échantillons — demeure pertinente. Toutefois, l'amplitude quantitative exacte de ces effets doit être recalculée avec la simulation réalignée.

---

## 6. Délimitation du périmètre et analyses complémentaires

L'invalidation formelle actée dans ce document concerne **strictement la Section 3.1 et les Figures S1 à S3**.

Concernant les autres blocs d'analyse :
- **Modèles Random Forest (Figure 4, Table S2) :**
  L'impact sur les performances RF dépend des jeux de données d'entraînement (2016–2019) et de holdout (2020) réellement ingérés. Toute conclusion sur leur validité requiert un audit de provenance dédié traçant l'utilisation de cibles ou prédicteurs issus de `da_cdf`.
- **Analyses d'attribution XAI / SHAP (Figures 5, 6, 7) :**
  Les importances de groupes de variables et les valeurs SHAP associées doivent faire l'objet d'un examen spécifique de leurs cohortes et de leurs fichiers sources.
- **Audit du bilan hydrique (AUD-05) :**
  L'audit AUD-05 porte sur la période juillet–août 2018 pour `OPL`, `DA_nocdf` et `DA_nowilt`. Il ne dépend pas de `da_cdf` et n'est pas concerné par cette discordance.

> [!IMPORTANT]
> Aucune conclusion d'invalidité ne doit être extrapolée aux modèles Random Forest et aux attributions XAI sans vérification préalable de leurs contrats de données respectifs.

---

## 7. Conditions de réhabilitation et de validation future

La réhabilitation des résultats de la Section 3.1 ne saurait être automatique et exige le respect des étapes suivantes :

1. **Achèvement complet de la simulation DA-CDF réalignée :**
   La simulation `DA_cdf_noirr_2016_2020` (actuellement en cours d'exécution sous `NoahMP_Morocco`) doit avoir achevé ses 60 mois de calcul (2016–2020 complets) sans interruption.
2. **Évaluation scientifique préalable de la simulation :**
   La conformité géométrique des tables CDF (`scripts/audits/check_cdf_domain.py`) ne préjuge pas de la qualité hydrologique des sorties. Un contrôle statistique approfondi des innovations et des incréments générés par le nouveau run (via [`scripts/audits/eval_da_cdf_test.py`](file:///home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/scripts/audits/eval_da_cdf_test.py) ou équivalent) doit confirmer la cohérence physique de l'assimilation avant toute exploitation.
3. **Mise à jour du prétraitement EnKF journalier :**
   Réexécution du prétraitement EnKF pour actualiser les séries journalières dans `data/processed/daily_enkf/da_cdf/`.
4. **Régénération des Source Data et des figures de Section 3.1 :**
   Exécution des scripts de post-traitement de la Section 3.1 sur les données réalignées :
   ```bash
   python scripts/postprocessing/manuscript/sec3.1/process_fig3_data.py
   python scripts/postprocessing/manuscript/sec3.1/process_supplementary_data.py
   python scripts/postprocessing/manuscript/sec3.1/plot_fig3.py
   python scripts/postprocessing/manuscript/sec3.1/plot_fig_s1.py
   python scripts/postprocessing/manuscript/sec3.1/plot_fig_s2.py
   python scripts/postprocessing/manuscript/sec3.1/plot_fig_s3.py
   ```
5. **Revue critique des contrôles qualité :**
   Comparaison méthodique des nouveaux rapports QC (`Fig3_qc_report.txt`, `FigS1_S3_qc_report.txt`) avec les sorties historiques pour quantifier rigoureusement l'impact du réalignement de domaine sur les résultats du manuscrit.
