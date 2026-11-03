# Scripts Dédiés aux Analyses du Manuscrit (`scripts/postprocessing/manuscript/`)

**Auteur :** M. El Aabaribaoune (@um6p)
**Rôle :** Centralisation des scripts de post-traitement analytique, de génération des tableaux et de production des figures pour la publication scientifique.

---

## 1. Organisation interne

Le répertoire structure les analyses du manuscrit selon trois composantes complémentaires :

```
scripts/postprocessing/manuscript/
├── sec3.1/      # Diagnostics d'assimilation EnKF directs (Figure 3 et Suppléments S1-S3)
├── rf/          # Évaluation des modèles d'apprentissage (tables de métriques et figures d'audit)
└── tables/      # Génération automatisée des tableaux LaTeX et CSV à partir des registres
```

---

## 2. Rôle des sous-répertoires

1. **[`sec3.1/`](sec3.1/README.md) :**
   Contient la chaîne complète de calcul et de rendu graphique pour la Section 3.1 du papier :
   - Fréquences spatiales de support d'assimilation (Fig. 3a–d).
   - Distribution et cartes des incréments signés sur support apparié (Fig. 3e–h).
   - Analyses de sensibilité à l'échantillonnage et bilans hydriques saisonniers (Figs. S1–S3).
2. **[`rf/`](rf/rf_eval/README.md) :**
   Consolide les métriques de performance des modèles Random Forest ($R^2$, Pearson $r$, MAE, RMSE, Skill score) sur l'année de test scellée 2020.
3. **`tables/` :**
   Scripts (`make_table.py`, `parse_registry.py`) compilant les caractéristiques prédictives et les résultats tabulés à partir des registres YAML pour garantir une reproduction sans saisie manuelle.

---

## 3. Dépendances et traçabilité

- **Entrées :** Séries temporelles NetCDF de `data/processed/daily_enkf/` et `data/interim/noahmp/`, ainsi que les sorties d'évaluation de `data/processed/modeling/xai/`.
- **Sorties :** Écrites dans `figures/manuscript/` et `tables/`.
- **Avertissement CDF historique :** Les anciens résultats Section 3.1 conditionnés par l'ancienne CDF invalidée sont préservés à titre historique sous `figures/legacy/section_3_1/`. Les scripts de ce dossier seront réexécutés sur les données de la DA-CDF corrigée.
