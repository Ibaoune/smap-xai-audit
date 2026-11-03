# Scripts de Modélisation Prédictive et Baselines (`scripts/modeling/`)

**Auteur :** M. El Aabaribaoune (@um6p)
**Rôle :** Partitionnement spatio-temporel, calcul des modèles de référence (baselines), entraînement des forêts aléatoires (Random Forest) et évaluation scellée sur le banc de test 2020.

---

## 1. Objectif scientifique

Le répertoire `scripts/modeling/` implémente le cadre d'apprentissage automatique supervisé utilisé pour émuler et analyser le comportement de la chaîne d'assimilation SMAP / Noah-MP.

L'objectif n'est pas de substituer un réseau de neurones ou une forêt aléatoire au modèle physique Noah-MP, mais de **construire des émulateurs statistiques interprétables** capables de capturer les relations fonctionnelles complexes entre :
1. Les conditions environnementales antécédentes et les incréments EnKF (bloc **SOURCE**).
2. L'incrément de surface et la réponse des flux couplés (bloc **TRANSFER**).
3. Les caractéristiques écohydrologiques et la concordance avec GLEAM (bloc **VALUE**).

---

## 2. Logique méthodologique

### Protocole de scellement temporel strict
Pour garantir une évaluation sans fuite d'information (*data leakage*) et tester la capacité de généralisation des modèles sur une année hydrologique indépendante :
- **Période d'entraînement final (*Training refit*) :** 2016-01-08 au 2019-12-31 (4 années hydrologiques complètes).
- **Période de test scellée (*Holdout 2020*) :** 2020-01-01 au 2020-12-31. L'année 2020 n'a jamais été exposée aux modèles durant la phase d'optimisation.

### Architectures Random Forest (spécifiées dans `configs/modeling/models.yaml`)
- **Configuration `RF_A` (utilisée pour SOURCE et TRANSFER) :**
  - Arbres : `n_estimators = 300`, profondeur maximale `max_depth = 12`, feuilles minimales `min_samples_leaf = 10`, `max_features = 0.7`.
  - *Justification scientifique :* Profondeur modérée pour régulariser les modèles face aux colinéarités fortes et optimiser la robustesse des explications TreeSHAP.
- **Configuration `RF_B` (utilisée pour VALUE) :**
  - Arbres : `n_estimators = 300`, profondeur maximale `max_depth = 16`, feuilles minimales `min_samples_leaf = 5`, `max_features = 0.7`.
  - *Justification scientifique :* Flexibilité accrue pour capturer la structure résiduelle plus fine du gain d'erreur absolue face à GLEAM.

### Régimes de support d'évaluation
- **Support natif (`native_support`) :** Modèles entraînés et évalués sur le support d'assimilation propre à chaque simulation.
- **Support apparié (`matched_support`) :** Modèles restreints à l'intersection stricte des pixel-jours où CDF et NoCDF possèdent simultanément une innovation finie.

---

## 3. Données, variables et métriques d'évaluation

### Entrées
- Tables Parquet compilées sous `data/processed/modeling/`.
- Fichiers de partitionnement issus de `configs/modeling/splits.yaml`.

### Métriques statistiques calculées
Pour chaque cible, les performances sur le test 2020 sont évaluées via :
- Coefficient de détermination ($R^2$) et corrélation linéaire de Pearson ($r$).
- Erreur absolue moyenne ($\text{MAE}$) et erreur quadratique moyenne ($\text{RMSE}$).
- Biais moyen ($\text{Bias} = \bar{\hat{y}} - \bar{y}$).
- **Score de compétence relatif (*Skill Score*) :**
  $$\text{Skill}_{\text{metric}} = 1 - \frac{\text{Metric}_{\text{RF}}}{\text{Metric}_{\text{baseline}}}$$
  Où la baseline est la médiane mensuelle d'entraînement (SOURCE, VALUE) ou la moyenne mensuelle d'entraînement (TRANSFER).

---

## 4. Fonctionnement technique et ordre d'exécution

```
Étape 1 : Génération du protocole de split spatio-temporel
  └─► python scripts/modeling/01_prepare_split_protocol.py

Étape 2 : Calcul et consolidation des modèles baselines
  ├─► python scripts/modeling/02_run_baselines.py
  └─► python scripts/modeling/02_merge_baselines.py

Étape 3 : Création du masque de support apparié (si comparaison CDF/NoCDF)
  └─► python scripts/modeling/04_create_matched_support.py

Étape 4 : Réentraînement final déterministe sur 2016-2019
  └─► python scripts/modeling/05_refit_final_rf_2016_2019.py --block <SOURCE|TRANSFER|VALUE> --exp <exp>

Étape 5 : Évaluation sur l'année de test scellée 2020
  └─► python scripts/modeling/06_evaluate_final_2020.py --block <SOURCE|TRANSFER|VALUE> --exp <exp>
```

Les modèles sérialisés sont archivés sous `models/` avec leurs hachages SHA-256 et métadonnées d'entraînement.

---

## 5. Validation, contrôle qualité et limites d'interprétation

1. **Adéquation statistique $\neq$ Réalité terrain :**
   Les métriques mesurent strictement la capacité de la Random Forest à émuler les équations de Noah-MP et du filtre EnKF. Elles ne constituent en aucun cas une validation physique de terrain par rapport à des données in situ (débits jaugés, tours de flux).
2. **Faiblesse de la baseline climatologique :**
   La baseline mensuelle ne résout pas la persistance d'ordre 1 ($t-1$). Sur des variables d'état à forte inertie ($\Delta\text{RZSM}$), un score de compétence de 30 % par rapport à la climatologie reste modeste face à un prédicteur de persistance pure.
3. **Traçabilité des artefacts :**
   Les scripts bloquent immédiatement l'exécution si une variable interdite est détectée dans les colonnes ou si un échantillon de 2020 apparaît dans le jeu d'entraînement.

---

## 6. Statut des résultats et références internes

- **[Vérifié]** Modèles **DA-NoCDF (Support natif)** scellés et évalués sur 2020. Résultats de référence documentés dans [`docs/nocdf_native_rf_results.md`](../../docs/nocdf_native_rf_results.md) et exportables via `scripts/audits/export_nocdf_native_rf_metrics.py`.
- **[En attente]** Modèles **DA-CDF corrigée** : les entraînements définitifs seront lancés dès validation des tables de données complètes.
- **Documentation associée :** Consulter [`docs/modeling/`](../../docs/modeling/) pour la matrice de développement RF et [`configs/modeling/`](../../configs/modeling/) pour les hyperparamètres.
