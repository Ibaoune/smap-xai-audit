# Scripts de Post-traitement et Synthèse (`scripts/postprocessing/`)

**Auteur :** M. El Aabaribaoune (@um6p)
**Rôle :** Consolidation des résultats analytiques, calculs des bilans hydriques de masse et génération des tableaux et figures pour la valorisation scientifique.

---

## 1. Objectif scientifique

Le répertoire `scripts/postprocessing/` regroupe les scripts dédiés à la phase finale de la recherche :
1. **Validation hydrologique et bilans de masse (`water_accounting/`) :** Quantifier l'impact volumique cumulé de l'assimilation d'humidité sur le bilan d'eau régional (fermeture du bilan, stockage racinaire cumulé, réallocation des flux d'évapotranspiration et de ruissellement).
2. **Génération des livrables de synthèse (`manuscript/`) :** Produire les tableaux de métriques formels et les diagnostics d'assimilation de surface (Section 3.1) destinés aux publications scientifiques.

---

## 2. Organisation interne

Le répertoire est subdivisé selon deux axes scientifiques distincts :

```
scripts/postprocessing/
├── manuscript/
│   ├── sec3.1/                 # Scripts d'analyse et de tracé pour les diagnostics EnKF directs
│   ├── tables/                 # Génération automatisée des tableaux de métriques
│   └── rf/rf_eval/             # Consolidation des métriques d'évaluation Random Forest
└── water_accounting/           # Diagnostic volumique et comptabilité de l'eau
    ├── 01_compute_soil_storage.py
    ├── 02_compute_water_fluxes.py
    └── 03_diagnose_water_closure.py
```

---

## 3. Données et flux de travail

- **Entrées :** Séries temporelles NetCDF standardisées de `data/interim/noahmp/` et `data/processed/daily_enkf/`, ainsi que les fichiers de métriques consolidés de `data/processed/modeling/xai/`.
- **Sorties :** Tableaux CSV exportés dans `tables/` et figures vectorielles haute résolution dans `figures/`.

---

## 4. Statut et traçabilité

- **[Vérifié]** Les scripts de post-traitement sont agnostiques et s'exécutent via des arguments CLI pointant vers les expériences choisies (`opl`, `da_nocdf`, `da_cdf`).
- **Précautions relatives à la DA-CDF :** Les anciens résultats historiques issus de la simulation CDF à grille discordante ont été formellement archivés sous `figures/legacy/section_3_1/` et `data/processed/water_accounting/legacy_cdf_2016_2020/`. Les scripts actuels sont configurés pour régénérer les sorties scientifiques à partir de la DA-CDF corrigée.
