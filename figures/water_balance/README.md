# Diagnostics de comptabilité des incréments et bilan hydrique

Ce répertoire rassemble les visualisations relatives aux transferts d'eau induits par l'assimilation EnKF et aux diagnostics hydrologiques du modèle de surface Noah-MP.

## Distinction conceptuelle fondamentale

- **Comptabilité des incréments d'analyse (*Water Accounting*) :** Évalue la quantité d'eau artificiellement introduite ou retirée dans la couche de surface (0–10 cm) par les incréments EnKF ($100 \times \text{incr en m}^3\,\text{m}^{-3} \rightarrow \text{mm}$). Ce diagnostic comptable ne constitue pas un bilan hydrologique complet ni une démonstration de fermeture du cycle de l'eau.
- **Bilan hydrique complet (*Hydrologic Water Balance*) :** Nécessite l'évaluation intégrée de l'ensemble des flux de surface (précipitations, composantes d'évapotranspiration, ruissellement et drainage) et des variations de stocks (profil racinaire et aquifère) modélisés par Noah-MP.

## Figures disponibles

- **`Figure_S8.png` / `Figure_S8.pdf` :** Prototype d'ajustement en eau comparant DA-CDF et DA-NoCDF sur support apparié (2016–2020) : (a) climatologie mensuelle de l'activité absolue, (b) bilan net d'ajustement, (c) carte spatiale de différence cumulée (NoCDF − CDF), (d) histogramme du bilan cumulé par domaine.
- **`QC_maps.png` :** Cartes de contrôle spatial 2D des cumuls d'ajustement absolu ($W_{\text{absolute}}$) et net ($W_{\text{net}}$) pour DA-CDF et DA-NoCDF.

## Chaîne de scripts et dépendances

1. [`process_water_accounting.py`](../../scripts/postprocessing/water_accounting/process_water_accounting.py) :
   - *Entrées :* Incréments signés événementiels (`data/interim/enkf/{da_cdf,da_nocdf}/increment_signed/`) et incréments absolus journaliers (`data/processed/daily_enkf/{da_cdf,da_nocdf}/daily_absolute_increment/`) pour 2016–2020 (présents sur le disque).
   - *Sorties :* Fichiers temporaires racine (`cdf_matched_temp.nc`, `nocdf_matched_temp.nc`, masques, `qc_report.txt`).
2. [`plot_water_accounting.py`](../../scripts/postprocessing/water_accounting/plot_water_accounting.py) :
   - *Entrées :* Fichiers intermédiaires (`cdf_matched_temp.nc`, `nocdf_matched_temp.nc`) et masque d'élévation (`data/processed/static/elevation/elevation.nc`).
   - *Sorties :* Synthèses tabulaires/grilles à la racine (`analysis_water_accounting_*`) et figures dans ce répertoire (`Figure_S8.*`, `QC_maps.png`).

## Statut de reproductibilité et de validité scientifique

- **Reproductibilité incomplète :** Les fichiers intermédiaires `cdf_matched_temp.nc` et `nocdf_matched_temp.nc` reliant les deux scripts sont actuellement absents du dépôt. La réexécution de bout en bout de la chaîne n'a pas été testée.
- **Statut scientifique :** **INVALIDÉ POUR PUBLICATION**. Les figures reposent sur la simulation historique DA-CDF affectée par un décalage spatial de grille (détaillé dans [`docs/invalidated_legacy_cdf_results.md`](../../docs/invalidated_legacy_cdf_results.md)) et sur un échantillonnage apparié conditionné par ce run erroné. Ces visualisations sont conservées uniquement à des fins de traçabilité de l'audit et ne doivent pas être utilisées comme résultats scientifiques validés.
