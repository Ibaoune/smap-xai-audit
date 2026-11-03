# Pipeline de Post-traitement et Rendu — Manuscrit Section 3.1 (Figure 3)

> [!WARNING]
> **Notice d'invalidation historique — Données DA-CDF :**
> Les métriques et figures de la simulation DA-CDF répertoriées dans ce document reposent sur l'ancienne simulation CDF à grille géographique discordante, formellement invalidée (voir [`docs/invalidated_legacy_cdf_results.md`](../../../../docs/invalidated_legacy_cdf_results.md)).
> Les scripts de ce répertoire sont configurés pour être réexécutés sur les données de la DA-CDF corrigée (dont les prétraitements 01–20 sont validés pour 2016–2020), ce qui produira les nouvelles figures définitives pour la Section 3.1.
> Seules les métriques de la simulation DA-NoCDF constituent des références scientifiques vérifiées.

Ce répertoire contient l'ensemble des scripts de traitement des données et de production des figures pour la **Section 3.1** du manuscrit (*SMAP / Noah-MP Assimilation Audit*).

---

## 1. Contexte Scientifique

La Section 3.1 examine les caractéristiques fondamentales des diagnostics d'assimilation EnKF entre les expériences **DA-CDF** (correction de biais standard via CDF-matching) et **DA-NoCDF** (sans correction de biais) sur le domaine du Maroc (2016–2020).

Le message scientifique repose sur deux piliers indissociables :

1. **Différence de support diagnostic (Fig. 3a–d)** :
   * Les expériences CDF et NoCDF n'opèrent **pas** sur le même support d'innovations finies (NoCDF assimile 3.7× plus de pixel-jours en raison de l'absence de troncature aux bornes de la fonction de transfert CDF).
   * Les diagnostics en support natif caractérisent chaque expérience individuellement, mais **ne permettent pas** une comparaison directe loyale.
2. **Structure des incréments sur support apparié (Fig. 3e–h)** :
   * Une comparaison directe loyale nécessite de conditionner l'analyse sur l'**intersection exacte des pixel-jours finis** (*exact matched support*).
   * Sur ce support apparié (2 441 779 pixel-jours), CDF applique une correction systématiquement asséchante ($\mu = -0.0071\ \text{m}^3\,\text{m}^{-3}$, 96.7% de séchage), tandis que NoCDF présente un comportement mixte bimodal centré près de zéro ($\mu = -0.0010\ \text{m}^3\,\text{m}^{-3}$, 36.2% d'humidification).

---

## 2. Organisation des Scripts

| Script | Rôle | Entrées principales | Sorties générées |
| :--- | :--- | :--- | :--- |
| **`process_fig3_data.py`** | Traitement des séries EnKF 2016–2020, masquage strict, climatologies et statistiques pour la Fig. 3. | `elevation.nc`, `daily_innovation_*.nc`, `daily_signed_increment_*.nc` | `Fig3_a_d_source_data.nc`, `Fig3_a_d_source_data.csv`, `Fig3_e_h_source_data.nc`, `Fig3_e_h_source_data.csv`, `matched_increments_1d.npz`, `matched_spatial_summary.csv`, `Fig3_qc_report.txt` |
| **`plot_fig3.py`** | Rendu graphique haute résolution (500 DPI raster + vecteur PDF) de la Fig. 3 (blocs 3a–d et 3e–h). | Fichiers sources produits par `process_fig3_data.py` | `Fig3_a_d_support.png`, `Fig3_a_d_support.pdf`, `Fig3_e_h_matched_updates.png`, `Fig3_e_h_matched_updates.pdf` |
| **`process_supplementary_data.py`** | Extraction et préparation des données pour les figures supplémentaires S1–S3. | Séries EnKF 2016–2020, `elevation.nc`, résultats de bilan d'eau | `FigS1_distributions.npz`, `FigS2_source_data.nc`, `FigS3_cumulative_map.nc`, `water_accounting_monthly_climatology.csv`, `water_accounting_summary_table.csv`, `FigS1_S3_qc_report.txt` |
| **`plot_fig_s1.py`** | Rendu de la Fig. S1 (Sensibilité à l'échantillonnage natif vs apparié pour CDF et NoCDF). | `FigS1_distributions.npz` | `FigS1_sample_matching_sensitivity.png`, `FigS1_sample_matching_sensitivity.pdf` |
| **`plot_fig_s2.py`** | Rendu de la Fig. S2 (Différences saisonnières DJF, MAM, JJA, SON sur support apparié). | `FigS2_source_data.nc` | `FigS2_seasonal_matched_diff.png`, `FigS2_seasonal_matched_diff.pdf` |
| **`plot_fig_s3.py`** | Rendu de la Fig. S3 (Comptabilité hydrique en couche de surface : climatologie, carte, barres cumulées). | `water_accounting_monthly_climatology.csv`, `water_accounting_summary_table.csv`, `FigS3_cumulative_map.nc` | `FigS3_water_accounting.png`, `FigS3_water_accounting.pdf` |

---

## 3. Guide d'Exécution

Les scripts sont conçus pour être exécutés de façon robuste depuis n'importe quel emplacement (résolution automatique de la racine du projet `smap-xai-audit`).

### Prérequis environnement
Activer l'environnement conda du projet :
```bash
conda activate smap-xai-audit
```

### A. Pipeline de la Figure Principale 3
```bash
# 1. Extraction et calculs de la Figure 3
python scripts/postprocessing/manuscript/sec3.1/process_fig3_data.py

# 2. Rendu graphique des deux blocs de la Figure 3 (Fig 3a–d et Fig 3e–h)
python scripts/postprocessing/manuscript/sec3.1/plot_fig3.py
```

### B. Pipeline des Figures Supplémentaires S1–S3
```bash
# 1. Extraction et calculs pour les figures supplémentaires
python scripts/postprocessing/manuscript/sec3.1/process_supplementary_data.py

# 2. Rendu graphique des Figures S1, S2 et S3
python scripts/postprocessing/manuscript/sec3.1/plot_fig_s1.py
python scripts/postprocessing/manuscript/sec3.1/plot_fig_s2.py
python scripts/postprocessing/manuscript/sec3.1/plot_fig_s3.py
```

---

## 4. Données d'Entrée (Inputs)

Les scripts exploitent les données gelées situées dans :
* **Masque d'élévation et domaine** : `data/processed/static/elevation/elevation.nc`
* **Diagnostics journaliers EnKF (2016–2020)** :
  * CDF : `data/processed/daily_enkf/da_cdf/daily_innovation/daily_innovation_{year}.nc`
  * CDF : `data/processed/daily_enkf/da_cdf/daily_signed_increment/daily_signed_increment_{year}.nc`
  * NoCDF : `data/processed/daily_enkf/da_nocdf/daily_innovation/daily_innovation_{year}.nc`
  * NoCDF : `data/processed/daily_enkf/da_nocdf/daily_signed_increment/daily_signed_increment_{year}.nc`

---

## 5. Produits Générés (Outputs)

Tous les livrables sont écrits de manière reproductible dans le dossier :
`figures/manuscript/section_3_1/`

### A. Données sources et statistiques
1. **`Fig3_a_d_source_data.nc`** : Fréquences spatiales de support natif (`freq_cdf`, `freq_nocdf`) et écart de support (`freq_diff` en points de pourcentage).
2. **`Fig3_a_d_source_data.csv`** : Climatologie mensuelle du support (Jan–Déc) pour CDF natif, NoCDF natif, et support apparié.
3. **`Fig3_e_h_source_data.nc`** : Cartes spatiales 2D des incréments moyens signés sur support apparié (`mean_cdf_matched`, `mean_nocdf_matched`, `mean_diff_matched`).
4. **`matched_increments_1d.npz`** : Tableaux 1D compressés des $2\,441\,779$ incréments signés appariés (`cdf_mat`, `nocdf_mat`).
5. **`Fig3_e_h_source_data.csv`** : Statistiques complètes de distribution (moyenne, écart-type, médiane, percentiles Q0.5 à Q99.5, fractions d'assèchement/humidification).
6. **`matched_spatial_summary.csv`** : Synthèse spatiale des cartes de moyennes.
7. **`Fig3_qc_report.txt`** : Rapport d'audit numérique automatique validant la cohérence mathématique des résultats de la Figure 3.
8. **`FigS1_distributions.npz`**, **`FigS2_source_data.nc`**, **`FigS3_cumulative_map.nc`** : Jeux de données sources pour les figures S1 à S3.
9. **`water_accounting_monthly_climatology.csv`**, **`water_accounting_summary_table.csv`** : Séries mensuelles et synthèses tabulées du bilan hydrique.
10. **`FigS1_S3_qc_report.txt`** : Rapport de contrôle qualité complet pour les suppléments S1–S3.

### B. Figures finales pour le manuscrit
1. **`Fig3_a_d_support.png`** / **`Fig3_a_d_support.pdf`** :
   * Bloc 1 (Fréquence d'assimilation) :
     * (a) Fréquence d'assimilation CDF [%] (palette discrète YlGnBu, 10 classes)
     * (b) Fréquence d'assimilation NoCDF [%] (palette discrète YlGnBu, 10 classes)
     * (c) Écart NoCDF − CDF [points de pourcentage] (palette discrète tronquée RdBu_r, 10 classes)
     * (d) Climatologie mensuelle de la fréquence d'assimilation [%]
2. **`Fig3_e_h_matched_updates.png`** / **`Fig3_e_h_matched_updates.pdf`** :
   * Bloc 2 (Structure des incréments sur support apparié) :
     * (e) Distributions des incréments signés appariés (histogrammes en marches sans remplissage)
     * (f) Moyenne CDF appariée [$\text{m}^3\,\text{m}^{-3}$] (palette discrète BrBG, 14 classes)
     * (g) Moyenne NoCDF appariée [$\text{m}^3\,\text{m}^{-3}$] (palette discrète BrBG, 14 classes)
     * (h) Différence moyenne NoCDF − CDF [$\text{m}^3\,\text{m}^{-3}$] (palette discrète RdBu_r, 14 classes)
3. **`FigS1_sample_matching_sensitivity.png`** / **`FigS1_sample_matching_sensitivity.pdf`** :
   * Figure S1 (Sensibilité à l'appariement d'échantillons) :
     * (a) Incréments CDF : support natif vs apparié
     * (b) Incréments NoCDF : support natif vs apparié
4. **`FigS2_seasonal_matched_diff.png`** / **`FigS2_seasonal_matched_diff.pdf`** :
   * Figure S2 (Différences saisonnières NoCDF − CDF sur support apparié) :
     * (a) Hiver (DJF), (b) Printemps (MAM), (c) Été (JJA), (d) Automne (SON)
5. **`FigS3_water_accounting.png`** / **`FigS3_water_accounting.pdf`** :
   * Figure S3 (Bilan d'ajustement en équivalent-eau de la couche de surface) :
     * (a) Activité d'ajustement absolue mensuelle [mm]
     * (b) Bilan net mensuel d'ajustement [mm]
     * (c) Différence spatiale cumulée d'ajustement absolu (NoCDF − CDF) [mm]
     * (d) Bilan cumulé sur échantillon apparié [mm] (Humidification, Séchage, Activité, Bilan net)

---

## 6. Métriques de Référence et Audit Qualité (Frozen Baseline)

L'audit numérique automatique confirme les valeurs figées suivantes :

| Métrique | DA-CDF | DA-NoCDF | Écart / Note |
| :--- | :--- | :--- | :--- |
| **Pixel-jours natifs** | 2 456 233 | 7 507 641 | Ratio NoCDF/CDF = 3.06× |
| **Pixel-jours appariés** | **2 441 779** | **2 441 779** | 100% de concordance temporelle |
| **Pixel-jours non-appariés** | 14 454 (0.59%) | 5 065 862 (67.48%) | NoCDF assimile massivement hors CDF |
| **Incrément moyen signé** | **$-0.0071\ \text{m}^3\,\text{m}^{-3}$** | **$-0.0010\ \text{m}^3\,\text{m}^{-3}$** | Écart net = $+0.0061\ \text{m}^3\,\text{m}^{-3}$ |
| **Incrément moyen absolu** | $0.0129\ \text{m}^3\,\text{m}^{-3}$ | $0.0128\ \text{m}^3\,\text{m}^{-3}$ | Activité globale similaire |
| **Fraction séchage ($<0$)** | 60.3% (pixels: 96.7%) | 52.4% (pixels: 63.8%) | Asymétrie spatiale majeure |
| **Fraction humidification ($>0$)**| 39.7% (pixels: 3.3%) | 47.6% (pixels: 36.2%) | NoCDF ré-humidifie fréquemment |
