# Spécifications de Modélisation (`configs/modeling/`)

**Auteur :** M. El Aabaribaoune (@um6p)
**Rôle :** Spécifications déclaratives des architectures d'apprentissage automatique et des protocoles de partitionnement des données.

---

## 1. Contenu du répertoire

- **[`models.yaml`](models.yaml) :** Déclare les dictionnaires d'hyperparamètres pour les modèles scikit-learn (Random Forest). Définit notamment les profils `pilot`, `RF_A`, `RF_B`, `RF_C` et `RF_D`.
- **[`splits.yaml`](splits.yaml) :** Spécifie le protocole de partitionnement temporel (Train 2016-2019, Test scellé 2020) et la définition des 5 folds géographiques pour les validations croisées spatiales.
