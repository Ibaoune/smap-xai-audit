# Scripts de comptabilité des incréments d'analyse EnKF

Ce répertoire rassemble les scripts historiques de calcul et de visualisation de l'ajustement en eau de surface (0–10 cm) induit par l'assimilation EnKF, converti en équivalent lame d'eau ($100 \times \text{incr en m}^3\,\text{m}^{-3} \rightarrow \text{mm}$).

## Rôle des scripts et ordre d'exécution

L'exécution doit respecter l'ordre séquentiel suivant :

1. **`process_water_accounting.py` :**
   - **Rôle :** Lit les incréments événementiels d'assimilation (2016–2020), applique les masques d'activité journaliers et calcule les composantes d'ajustement ($W_{\text{positive}}$, $W_{\text{removal}}$, $W_{\text{absolute}}$, $W_{\text{net}}$) sur support natif et apparié.
   - **Entrées :** `data/interim/enkf/{da_cdf,da_nocdf}/increment_signed/` et `data/processed/daily_enkf/{da_cdf,da_nocdf}/daily_absolute_increment/`.
   - **Sorties :** Fichiers temporaires racine (`cdf_matched_temp.nc`, `nocdf_matched_temp.nc`, masques, `*.npy`) et rapport de contrôle numérique `qc_report.txt`.
2. **`plot_water_accounting.py` :**
   - **Rôle :** Agrège temporellement (mensuel, saisonnier, cumul 5 ans) et spatialement les composantes d'ajustement, exporte les données de synthèse et génère les visualisations.
   - **Entrées :** Fichiers intermédiaires `cdf_matched_temp.nc`, `nocdf_matched_temp.nc` et masque d'élévation `data/processed/static/elevation/elevation.nc`.
   - **Sorties de données :** Séries mensuelles, saisonnières et grilles cumulées `analysis_water_accounting_*` (conservées à la racine du dépôt pour les dépendances aval).
   - **Sorties graphiques :** `figures/water_balance/Figure_S8.png`, `Figure_S8.pdf` et `figures/water_balance/QC_maps.png`.

## Répertoire d'exécution et environnement

- **Exécution impérative depuis la racine :** Les scripts doivent être lancés depuis la racine du dépôt (`smap-xai-audit`) afin de résoudre correctement les chemins relatifs des données :
  ```bash
  python scripts/postprocessing/water_accounting/process_water_accounting.py
  python scripts/postprocessing/water_accounting/plot_water_accounting.py
  ```
- **Environnement Python requis :** `xarray`, `numpy`, `pandas`, `matplotlib`, `netCDF4`.

## Dépendances intermédiaires et limites scientifiques

- **Dépendance intermédiaire absente :** Les fichiers `cdf_matched_temp.nc` et `nocdf_matched_temp.nc` sont éphémères et absents du dépôt. `plot_water_accounting.py` ne peut pas être exécuté isolément sans lancer préalablement `process_water_accounting.py`.
- **Exécution non vérifiée :** L'exécution complète de bout en bout de cette chaîne n'a pas été retestée dans cet audit.
- **Statut de provenance :** **INVALIDÉ POUR PUBLICATION**. Cette chaîne ingère la simulation historique `DA_cdf_noirr_2016_2020` affectée par le décalage spatial des tables CDF (cf. [`docs/invalidated_legacy_cdf_results.md`](../../../docs/invalidated_legacy_cdf_results.md)). Les totaux appariés et les différences NoCDF − CDF ne constituent pas des résultats scientifiques validés.
- **Portée méthodologique :** Ce diagnostic documente uniquement la comptabilité des perturbations d'incréments EnKF et ne constitue pas un bilan hydrologique complet de Noah-MP (conservation de masse fermée flux/stocks).
