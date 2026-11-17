# Configurations de la Chaîne d'Audit (`configs/`)

**Auteur :** M. El Aabaribaoune (@um6p)
**Rôle :** Centralisation des contrats de données, des hyperparamètres de modélisation et du registre des caractéristiques XAI.

---

## 1. Rôle scientifique et architectural

Le répertoire `configs/` constitue la source de vérité déclarative du projet. Son rôle est de garantir qu'aucun paramètre critique (liste de variables, hyperparamètre de modèle, partitionnement temporel ou masquage) ne soit codé en dur dans les scripts Python.

Il est structuré en trois sous-dossiers fonctionnels :
```
configs/
├── datasets/          # Contrats de données pour la construction des tables Parquet
│   ├── source.yaml    # Contrat du bloc SOURCE (35 prédicteurs contextuels, cibles, exclusions)
│   ├── transfer.yaml  # Contrat du bloc TRANSFER (52 prédicteurs, 4 cibles couplées)
│   └── value.yaml     # Contrat du bloc VALUE (52 prédicteurs à 0.25°, cible value_ae)
├── modeling/          # Spécifications d'apprentissage automatique
│   ├── models.yaml    # Architectures et hyperparamètres Random Forest (RF_A, RF_B, etc.)
│   └── splits.yaml    # Protocole de découpage temporel (train 2016-2019, holdout 2020)
└── xai/               # Taxonomie et regroupement des prédicteurs
    └── feature_groups.yaml # Registre unifié des 58 prédicteurs en 9 groupes scientifiques
```

---

## 2. Contrats de données (`configs/datasets/`)

Chaque fichier YAML définit formellement :
- Les **variables cibles** principales et secondaires.
- Les **caractéristiques obligatoires** classées par groupe physique (états antécédents, forçages, statiques, temporels).
- Les **variables interdites** (*forbidden predictors*) pour éliminer tout risque de fuite d'information (*data leakage*) ou de relation tautologique.
- Les **caractéristiques à variance nulle** exclues par défaut (ex. classes de sol ou de végétation absentes du domaine NorthMor).

---

## 3. Spécifications de modélisation (`configs/modeling/`)

- **`models.yaml` :** Définit les configurations Random Forest utilisées dans le projet :
  - `RF_A` (SOURCE et TRANSFER) : 300 arbres, profondeur maximale 12, `min_samples_leaf` = 10, `max_features` = 0.7.
  - `RF_B` (VALUE) : 300 arbres, profondeur maximale 16, `min_samples_leaf` = 5, `max_features` = 0.7.
- **`splits.yaml` :** Scelle les bornes temporelles d'apprentissage et de test, interdisant toute exposition prématurée de l'année 2020.

---

## 4. Registre d'explicabilité (`configs/xai/`)

Le fichier `feature_groups.yaml` associe chaque prédicteur individuel à l'un des 9 groupes scientifiques standardisés :
1. `antecedent_soil_moisture_state`
2. `meteorological_forcing`
3. `antecedent_lsm_fluxes`
4. `assimilation_diagnostics`
5. `forcing_perturbation_controls`
6. `trajectory_memory`
7. `soil_properties`
8. `land_cover_or_vegetation`
9. `temporal_context` / `topography`

Ce regroupement permet d'analyser l'attribution TreeSHAP au niveau des processus physiques et neutralise les incertitudes d'attribution induites par les colinéarités locales entre prédicteurs individuels.
