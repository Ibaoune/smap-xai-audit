# Diagnostics de comptabilité des incréments et bilan hydrique

Ce répertoire rassemble les visualisations relatives aux transferts d'eau induits par l'assimilation EnKF et aux diagnostics hydrologiques du modèle de surface Noah-MP.

## Distinction conceptuelle fondamentale

- **Comptabilité des incréments d'analyse (*Water Accounting*) :** Évalue la quantité d'eau artificiellement introduite ou retirée dans la couche de surface (0–10 cm) par les incréments EnKF ($100 \times \text{incr en m}^3\,\text{m}^{-3} \rightarrow \text{mm}$). Ce diagnostic comptable ne constitue pas un bilan hydrologique complet ni une démonstration de fermeture du cycle de l'eau.
- **Bilan hydrique complet (*Hydrologic Water Balance*) :** Nécessite l'évaluation intégrée de l'ensemble des flux de surface (précipitations, composantes d'évapotranspiration, ruissellement et drainage) et des variations de stocks (profil racinaire et aquifère) modélisés par Noah-MP.

## Figures disponibles

- **`Figure_S8.png` / `Figure_S8.pdf` :** Prototype d'ajustement en eau comparant DA-CDF et DA-NoCDF sur support apparié (2016–2020) : (a) climatologie mensuelle de l'activité absolue, (b) bilan net d'ajustement, (c) carte spatiale de différence cumulée (NoCDF − CDF), (d) histogramme du bilan cumulé par domaine.
- **`QC_maps.png` :** Cartes de contrôle spatial 2D des cumuls d'ajustement absolu ($W_{\text{absolute}}$) et net ($W_{\text{net}}$) pour DA-CDF et DA-NoCDF.

## Figures historiques préservées vs Nouvelles reproductions

- **Figures historiques préservées (`figures/water_balance/`) :** Les figures présentes dans ce dossier (`Figure_S8.png`, `Figure_S8.pdf`, `QC_maps.png`) sont figées et suivies sous Git. Elles documentent l'état historique des diagnostics de la DA-CDF invalidée. Les scripts ne peuvent plus écrire dans ce répertoire.
- **Figures d'une nouvelle reproduction technique :** En cas d'exécution explicite autorisée via `--include-legacy-cdf`, les nouvelles figures sont strictement isolées dans le sous-dossier `figures/` du répertoire de run, par exemple :
  `data/processed/water_accounting/runs/historical_repro_20261102/figures/`

## Chaîne de scripts et dépendances

1. [`process_water_accounting.py`](../../scripts/postprocessing/water_accounting/process_water_accounting.py) :
   - *Entrées :* Incréments signés événementiels (`data/interim/enkf/{da_cdf,da_nocdf}/increment_signed/`) et incréments absolus journaliers (`data/processed/daily_enkf/{da_cdf,da_nocdf}/daily_absolute_increment/`) pour 2016–2020.
   - *Sorties :* Fichiers temporaires (`cdf_matched_temp.nc`, `nocdf_matched_temp.nc`, masques, `qc_report.txt`) écrits dans le dossier de run.
2. [`plot_water_accounting.py`](../../scripts/postprocessing/water_accounting/plot_water_accounting.py) :
   - *Entrées :* Fichiers intermédiaires dans le dossier de run et masque d'élévation (`data/processed/static/elevation/elevation.nc`).
   - *Sorties :* Synthèses tabulaires/grilles (`analysis_water_accounting_*`) dans le dossier de run et figures dans `<run-dir>/figures/`.

Exemple d'exécution de reproduction technique :
```bash
python scripts/postprocessing/water_accounting/plot_water_accounting.py \
  --include-legacy-cdf \
  --run-dir data/processed/water_accounting/runs/historical_repro_20261102
```

## Statut de reproductibilité et de validité scientifique

- **Reproductibilité conditionnelle :** Les fichiers intermédiaires reliant les deux scripts sont absents par défaut du dépôt. Une reproduction technique nécessite l'exécution préalable de `process_water_accounting.py` avec le même dossier de run.
- **Statut scientifique :** **INVALIDÉ POUR PUBLICATION**. Les figures reposent sur la simulation historique DA-CDF affectée par un décalage spatial de grille (détaillé dans [`docs/invalidated_legacy_cdf_results.md`](../../docs/invalidated_legacy_cdf_results.md)) et sur un échantillonnage apparié conditionné par ce run erroné. Ces visualisations sont conservées uniquement à des fins de traçabilité de l'audit et ne doivent pas être utilisées comme résultats scientifiques validés.
