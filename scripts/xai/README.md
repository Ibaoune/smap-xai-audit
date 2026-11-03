# Scripts d'Explicabilité Machine Learning — XAI (`scripts/xai/`)

**Auteur :** M. El Aabaribaoune (@um6p)
**Rôle :** Extraction des valeurs SHAP, calcul des importances par permutation, analyses de robustesse spatio-temporelle et génération des figures d'interprétabilité pour SOURCE, TRANSFER et VALUE.

---

## 1. Objectif scientifique

Le répertoire `scripts/xai/` implémente la boîte à outils d'interprétabilité statistique du projet.

Son objectif scientifique est d'**auditer les décisions prédictives des modèles Random Forest** afin de comprendre :
1. Quels facteurs environnementaux (humidité antérieure, pluie, texture de sol, couverture végétale) gouvernent l'attribution des incréments par le filtre EnKF (**SOURCE**).
2. Comment l'information injectée en surface est redistribuée vers les composantes hydrologiques profondes et couplées (**TRANSFER**).
3. Quels contextes pédo-climatiques conditionnent le gain ou la dégradation de l'évapotranspiration face au produit indépendant GLEAM v4.3a (**VALUE**).

---

## 2. Logique méthodologique et protocole de calcul

### Théorie des jeux coopératifs : TreeSHAP
L'explicabilité repose sur l'algorithme déterministe **TreeSHAP** (`shap.TreeExplainer`) configuré avec :
- `feature_perturbation = 'tree_path_dependent'`
- `model_output = 'raw'`
TreeSHAP garantit des propriétés mathématiques indispensables : **efficacité (additivité locale)**, **symétrie**, **monotonicité** et conservation de la somme des contributions vis-à-vis de la sortie du modèle.

### Conception des cohortes représentatives (RF-04A)
En raison du volume massif de données ($> 20 \times 10^6$ pixel-jours), les calculs SHAP sont exécutés sur des cohortes représentatives déterministes :
- **Cohorte universelle représentative :** 50 000 pixel-jours échantillonnés de manière équilibrée par mois hydrologique et par bloc spatial (graine 42).
- **Sous-ensemble de calcul SHAP :** **10 000 pixel-jours** imbriqués dans la cohorte de 50 000. Des tests de sensibilité ont prouvé une concordance de classement quasi parfaite ($\rho > 0{,}998$) entre 5k et 10k points.
- **Sous-ensemble de permutation :** 5 000 pixel-jours (5 répétitions sur l'erreur absolue).

### Analyses de stabilité et de robustesse
- **Décomposition par groupes scientifiques :** Les prédicteurs individuels sont agrégés selon le registre unifié de 58 variables (`configs/xai/feature_groups.yaml`) pour neutraliser les colinéarités locales.
- **Sensibilité saisonnière :** Découpage strict DJF (hiver) vs JJA (été).
- **Stabilité spatiale :** Évaluation sur 5 blocs géographiques régionaux indépendants (folds 0 à 4).
- **Analyse par signe (VALUE) :** Examen séparé descriptif des pixel-jours où $\text{value\_ae} > 0$ (gain) et $\text{value\_ae} < 0$ (dégradation).

---

## 3. Données et répertoires de sortie

Les sorties numériques du pipeline XAI sont archivées de façon structurée sous `data/processed/modeling/xai/` :
- `shap/` : Matrices complètes de valeurs SHAP au format Parquet.
- `cohorts/` : Index des pixel-jours des cohortes 50k et 10k.
- `summaries/` : Résumés statistiques par modèle (`mean_abs_shap`, `mean_signed_shap`, quantiles).
- `groups/` : Matrices d'importance relative par groupe scientifique.
- `permutation/` : Fichiers JSON d'importance par permutation.
- `seasonal/` et `spatial/` : Décompositions par saison et par fold spatial.

---

## 4. Fonctionnement technique et ordonnancement

La chaîne XAI s'exécute selon une séquence ordonnée :

```
Étape 1 : Préparation et audit de la cohorte
  └─► python scripts/xai/01_prepare_xai_cohorts.py --block <SOURCE|TRANSFER|VALUE>

Étape 2 : Exécution de TreeSHAP et de la permutation
  ├─► python scripts/xai/03_run_source_xai.py --experiment <exp>
  ├─► python scripts/xai/06_run_transfer_xai.py --experiment <exp> --target <target>
  └─► python scripts/xai/09_run_value_xai.py --experiment <exp>

Étape 3 : Synthèse statistique et agrégations de groupes
  ├─► python scripts/xai/04_summarize_source_xai.py
  ├─► python scripts/xai/07_summarize_transfer_xai.py
  └─► python scripts/xai/10_summarize_value_xai.py

Étape 4 : Tracé des figures d'audit XAI (matplotlib uniquement)
  ├─► python scripts/xai/05_plot_source_xai.py
  ├─► python scripts/xai/08_plot_transfer_xai.py
  └─► python scripts/xai/11_plot_value_xai.py

Étape 5 : Chaîne finale scellée 2020
  ├─► python scripts/xai/12_run_final_2020_xai.py
  ├─► python scripts/xai/13_summarize_final_2020_xai.py
  └─► python scripts/xai/14_consolidate_final_2020_xai.py
```

---

## 5. Validation et limites d'interprétation

1. **Contrôle d'additivité SHAP :**
   Pour chaque échantillon $i$, l'erreur d'additivité $\epsilon_i = |f(x_i) - (\phi_0 + \sum_j \phi_{ij})|$ est auditée. L'erreur médiane est rigoureusement inférieure à $2 \times 10^{-14}$ sur l'ensemble des modèles.
2. **Attribution prédictive $\neq$ Causalité physique :**
   SHAP décompose la variance expliquée par le modèle statistique ajusté. Une forte importance SHAP d'un prédicteur ne signifie pas qu'il est la cause physique du phénomène, mais qu'il constitue un puissant heuristique statistique exploité par les arbres de décision.
3. **Colinéarité :**
   Lorsque deux variables sont corrélées (ex. `ssm_lag1` et `rzsm_lag1`), TreeSHAP répartit leur attribution. L'interprétation doit toujours s'appuyer sur le groupe scientifique plutôt que sur une variable isolée.

---

## 6. Statut des résultats et références internes

- **[Vérifié]** Chaîne XAI exécutée et fermée pour la phase de développement 2019 (protocoles RF-04B documentés dans `docs/xai/06_source_xai.md`, `07_transfer_xai.md`, `08_value_xai.md`).
- **[Vérifié]** Modèles DA-NoCDF (Support natif) évalués et consolidés sur 2020 via les scripts `12` à `14`.
- **[En attente]** Calculs XAI pour la simulation DA-CDF corrigée : en attente de la régénération des tables Parquet complètes.
- **Documentation complète :** Consulter le protocole XAI global dans [`docs/xai/01_rf_xai_protocol.md`](../../docs/xai/01_rf_xai_protocol.md).
