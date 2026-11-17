# Répertoire des Sorties Graphiques (`figures/`)

**Auteur :** M. El Aabaribaoune (@um6p)
**Rôle :** Centralisation, classification thématique et traçabilité des représentations visuelles des diagnostics hydrologiques, des performances d'apprentissage et de l'explicabilité XAI.

---

## 1. Objectif scientifique

Le répertoire `figures/` héberge les artefacts graphiques produits par la chaîne d'audit `smap-xai-audit`. Il permet de :
1. **Visualiser les diagnostics EnKF directs** : innovations satellitaires, incréments d'analyse, distribution spatiale des corrections et masques d'échantillonnage.
2. **Évaluer les bilans d'eau régionaux** : stockage d'eau cumulé dans le sol et réallocation des flux couplés (évapotranspiration, ruissellement).
3. **Restituer les résultats d'apprentissage et de XAI** : courbes de dépendance partielle, profils d'attribution globale TreeSHAP (beeswarm, importances relatives de groupes), stabilités spatiales sur 5 blocs et contrastes saisonniers (DJF vs JJA).

---

## 2. Organisation thématique cible

Les figures sont organisées selon des répertoires thématiques autonomes :

```
figures/
├── assimilation/       # Diagnostics directs du filtre EnKF (innovations, incréments, distributions)
├── water_balance/      # Bilans hydrologiques de masse et comptabilité de l'eau
├── modeling/           # Courbes d'apprentissage, protocoles de split et métriques d'évaluation RF
├── xai/                # Profils d'attribution TreeSHAP, permutation d'importance et dépendances
├── audit/              # Figures de contrôle qualité et synthèses d'audit scellées
├── legacy/             # Archives historiques des résultats invalidés
│   └── section_3_1/    # Anciennes figures Section 3.1 conditionnées par la CDF à grille erronée
└── manuscript/         # Figures spécifiques destinées à l'assemblage du manuscrit
```

---

## 3. Règle d'or de traçabilité scientifique

Chaque figure produite ou archivée dans ce répertoire doit impérativement être accompagnée des métadonnées de reproductibilité suivantes :
1. **Script déterministe producteur :** Le script exact sous `scripts/` (ex. `scripts/xai/05_plot_source_xai.py`).
2. **Données d'entrée traçables :** Le chemin exact des fichiers sources (fichiers NetCDF dans `data/interim/` ou Parquet dans `data/processed/modeling/`).
3. **Expérience modélisée :** Indication claire de l'expérience concernée (`opl`, `da_nocdf` ou `da_cdf` corrigée).
4. **Support d'évaluation :** Précision du régime de support (`native_support` ou `matched_support`).

---

## 4. Statut des résultats et gestion des archives historiques

- **[Vérifié] Figures DA-NoCDF :** Les figures d'audit associées au premier lot scellé NoCDF (Holdout 2020) sont disponibles dans `figures/audit/` (`nocdf_native_rf_2020_metrics.pdf` et `.png`).
- **[Archive formelle] Sorties DA-CDF historiques :** Toutes les figures générées avant le 27 octobre 2026 reposant sur l'ancienne simulation DA-CDF (ou sur un échantillonnage apparié dépendant de celle-ci) ont été déplacées vers `figures/legacy/section_3_1/`. Elles sont formellement invalidées en raison d'une discordance de grille géographique dans le calcul initial de la CDF. Consulter [`docs/invalidated_legacy_cdf_results.md`](../docs/invalidated_legacy_cdf_results.md) pour la documentation détaillée des empreintes SHA-256 et des motifs d'invalidation.
- **[En attente] Régénération DA-CDF corrigée :** Les nouvelles figures comparatives CDF vs NoCDF seront générées directement dans leurs répertoires thématiques respectifs dès finalisation des nouveaux entraînements de modèles.
