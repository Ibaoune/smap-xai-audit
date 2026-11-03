# Scripts de comptabilité des incréments d'analyse EnKF

Ce répertoire rassemble les scripts historiques de calcul et de visualisation de l'ajustement en eau de surface (0–10 cm) induit par l'assimilation EnKF, converti en équivalent lame d'eau ($100 \times \text{incr en m}^3\,\text{m}^{-3} \rightarrow \text{mm}$).

## Rôle des scripts et ordre d'exécution

L'exécution doit respecter l'ordre séquentiel suivant :

1. **`process_water_accounting.py` :**
   - **Rôle :** Lit les incréments événementiels d'assimilation (2016–2020), applique les masques d'activité journaliers et calcule les composantes d'ajustement ($W_{\text{positive}}$, $W_{\text{removal}}$, $W_{\text{absolute}}$, $W_{\text{net}}$) sur support natif et apparié.
   - **Entrées :** `data/interim/enkf/{da_cdf,da_nocdf}/increment_signed/` et `data/processed/daily_enkf/{da_cdf,da_nocdf}/daily_absolute_increment/`.
   - **Sorties :** Fichiers temporaires (`cdf_matched_temp.nc`, `nocdf_matched_temp.nc`, masques, `*.npy`) et rapport de contrôle numérique `qc_report.txt`, écrits dans un dossier d'exécution dédié sous `data/processed/water_accounting/runs/historical_repro_20261102/`.
2. **`plot_water_accounting.py` :**
   - **Rôle :** Agrège temporellement (mensuel, saisonnier, cumul 5 ans) et spatialement les composantes d'ajustement, exporte les données de synthèse et génère les visualisations.
   - **Entrées :** Fichiers intermédiaires `cdf_matched_temp.nc`, `nocdf_matched_temp.nc` dans le dossier de run et masque d'élévation `data/processed/static/elevation/elevation.nc`.
   - **Sorties de données :** Séries mensuelles, saisonnières, grilles cumulées et tableau de synthèse `analysis_water_accounting_*` écrites directement dans le dossier de run.
   - **Sorties graphiques :** Figures générées dans le sous-dossier `figures/` du dossier de run (`Figure_S8.png`, `Figure_S8.pdf`, `QC_maps.png`). Aucune écriture dans `figures/water_balance/`.

## Répertoire d'exécution et environnement

- **Sécurisation de la chaîne historique :**
  Les deux scripts sont **désactivés par défaut** afin d'empêcher toute exécution accidentelle de la simulation DA-CDF invalidée ou toute pollution du dépôt.
  Pour exécuter la chaîne à des fins de reproduction technique, les deux scripts doivent être lancés avec un identifiant d'exécution concret :
  ```bash
  # Étape 1 : prétraitement et génération des intermédiaires
  python scripts/postprocessing/water_accounting/process_water_accounting.py \
    --include-legacy-cdf \
    --output-dir data/processed/water_accounting/runs/historical_repro_20261102

  # Étape 2 : agrégation, tableaux de synthèse et figures
  python scripts/postprocessing/water_accounting/plot_water_accounting.py \
    --include-legacy-cdf \
    --run-dir data/processed/water_accounting/runs/historical_repro_20261102
  ```
  Le répertoire `--output-dir` / `--run-dir` doit être strictement situé sous `data/processed/water_accounting/runs/`. Tout chemin vers la racine du dépôt, vers `legacy_cdf_2016_2020/` ou vers un fichier/dossier existant est strictement refusé.
  La reproduction technique ne constitue pas une validation scientifique des données.

- **Environnement Python requis :** `xarray`, `numpy`, `pandas`, `matplotlib`, `netCDF4`.

## Dépendances intermédiaires et limites scientifiques

- **Dépendance intermédiaire :** Les fichiers `cdf_matched_temp.nc` et `nocdf_matched_temp.nc` reliant les deux scripts sont absents par défaut du dépôt. `plot_water_accounting.py` ne peut pas être exécuté sans lancer préalablement `process_water_accounting.py` dans le même dossier de run.
- **Exécution non vérifiée :** L'exécution complète de bout en bout de cette chaîne n'a pas été retestée dans cet audit.
- **Statut de provenance :** **INVALIDÉ POUR PUBLICATION**. Cette chaîne ingère la simulation historique `DA_cdf_noirr_2016_2020` affectée par le décalage spatial des tables CDF (cf. [`docs/invalidated_legacy_cdf_results.md`](../../../docs/invalidated_legacy_cdf_results.md)). Les totaux appariés et les différences NoCDF − CDF ne constituent pas des résultats scientifiques validés.
- **Portée méthodologique :** Ce diagnostic documente uniquement la comptabilité des perturbations d'incréments EnKF et ne constitue pas un bilan hydrologique complet de Noah-MP (conservation de masse fermée flux/stocks).
