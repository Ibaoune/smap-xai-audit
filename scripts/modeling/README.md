# Scripts de Modélisation Prédictive et Baselines (`scripts/modeling/`)

**Auteur :** M. El Aabaribaoune (@um6p)
**Rôle :** Partitionnement spatio-temporel, calcul des modèles de référence (baselines), entraînement des forêts aléatoires (Random Forest) et évaluation scellée sur le banc de test 2020.

---

## 1. Objectif scientifique

Le répertoire `scripts/modeling/` implémente le cadre d'apprentissage automatique supervisé utilisé pour émuler et analyser le comportement de la chaîne d'assimilation SMAP / Noah-MP sur la grille NorthMor ($121 \times 181$ mailles, résolution $0{,}05^\circ \approx 5\text{ km}$).

L'objectif n'est pas de substituer un réseau de neurones ou une forêt aléatoire au modèle physique Noah-MP, mais de **construire des émulateurs statistiques interprétables** capables d'analyser :
1. Dans quelle mesure le contexte environnemental antécédent et statique permet d'anticiper l'intensité des incréments EnKF (bloc **SOURCE**).
2. La réponse dynamique des flux couplés à l'incrément de surface (bloc **TRANSFER**).
3. Les facteurs prédictifs de concordance avec la référence externe GLEAM v4.3a (bloc **VALUE**).

---

## 2. Logique méthodologique

### Protocole de scellement temporel strict
Pour garantir une évaluation sans fuite d'information (*data leakage*) et tester la capacité de généralisation des modèles sur une année hydrologique indépendante :
- **Période d'entraînement final (*Training refit*) :** 2016-01-08 au 2019-12-31 (4 années hydrologiques complètes).
- **Période de test scellée (*Holdout 2020*) :** 2020-01-01 au 2020-12-31. L'année 2020 est formellement scellée et n'a pas été utilisée pour le réglage des hyperparamètres.

### Partitionnement spatial par blocs réguliers
Pour tester la robustesse spatiale face aux dépendances spatiales, le fichier [`configs/modeling/splits.yaml`](../../configs/modeling/splits.yaml) définit un découpage en **5 blocs géographiques réguliers de $1{,}0^\circ \times 1{,}0^\circ$** (folds 0 à 4), interdisant tout découpage aléatoire pixel par pixel (*random pixel split forbidden*).

### Architectures Random Forest (spécifiées dans `configs/modeling/models.yaml`)
- **Configuration `RF_A` (utilisée pour SOURCE et TRANSFER) :**
  - Arbres : `n_estimators = 300`, profondeur maximale `max_depth = 12`, feuilles minimales `min_samples_leaf = 10`, `max_features = 0.7`.
  - *Justification scientifique :* Profondeur modérée pour régulariser les modèles face aux colinéarités fortes et optimiser la robustesse des explications TreeSHAP.
- **Configuration `RF_B` (utilisée pour VALUE) :**
  - Arbres : `n_estimators = 300`, profondeur maximale `max_depth = 16`, feuilles minimales `min_samples_leaf = 5`, `max_features = 0.7`.

### Régimes de support d'évaluation
- **Support natif (`native_support`) :** Modèles entraînés et évalués sur le support d'assimilation propre à chaque simulation.
- **Support apparié (`matched_support`) :** Modèles restreints à l'intersection temporelle et spatiale exacte des pixel-jours où CDF et NoCDF possèdent simultanément une innovation finie.

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
  $$\text{Skill}_{\text{MAE}} = 1 - \frac{\text{MAE}_{\text{RF}}}{\text{MAE}_{\text{baseline}}}$$
  Où la baseline est la médiane mensuelle locale d'entraînement (SOURCE, VALUE) ou la moyenne mensuelle (TRANSFER).

---

## 4. Matrice d'expériences prévues pour SOURCE [Proposé]

Afin de départager rigoureusement la pertinence des cibles et des prédicteurs, quatre expériences contrôlées sont préparées :
1. **Expérience A (Référence actuelle) :** Régression sur l'amplitude absolue $|\Delta\theta_1^a|$ avec 35 prédicteurs contextuels.
2. **Expérience B (Classification du signe) :** Prédiction du sens de la correction $\text{signe}(\Delta\theta_1^a)$ avec exclusion d'une bande morte $[-\epsilon, +\epsilon]$ ($\epsilon = 0{,}002\text{ m}^3\,\text{m}^{-3}$).
3. **Expérience C (Contextuel vs Mécanistique) :** Mesure du saut de prédictibilité apporté par l'innovation ($y - Hx^f$) et la variance de prévision ($HPH^T$).
4. **Expérience D (Sensibilité d'échelle) :** Régression sur l'amplitude normalisée par la capacité au champ $|\Delta\theta_1^a| / \theta_{\text{fc}}$.

---

## 5. Fonctionnement technique et ordre d'exécution

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

---

## 6. Validation, contrôle qualité et limites d'interprétation

1. **Interprétation du Skill Score :**
   Pour le modèle SOURCE NoCDF natif, le score de compétence $\text{Skill}_{\text{MAE}} = 15{,}4\%$ indique que la RF réduit l'erreur absolue moyenne de 15,4 % par rapport à la médiane mensuelle locale. Les 84,6 % d'erreur résiduelle rappellent que l'amplitude exacte de l'incrément reste largement imprévisible sans l'observation satellite.
2. **Adéquation statistique $\neq$ Vérité physique :**
   Les métriques mesurent strictement l'adéquation de la régression statistique face aux sorties numériques du modèle et du filtre. Elles ne constituent pas une validation de terrain.
3. **Dépendances spatiales résiduelles :**
   L'évaluation finale doit impérativement confronter la validation temporelle (2020) et la validation spatiale par blocs ($1^\circ \times 1^\circ$) pour éviter les faux succès dus à l'autocorrélation spatiale.

---

## 7. Statut des résultats et références internes

- **[Vérifié]** Modèles **DA-NoCDF (Support natif)** scellés et évalués sur 2020. Résultats de référence documentés dans [`docs/nocdf_native_rf_results.md`](../../docs/nocdf_native_rf_results.md) et exportables via `scripts/audits/export_nocdf_native_rf_metrics.py`.
- **[En attente]** Modèles **DA-CDF corrigée** : réentraînement après validation finale du protocole d'expériences.
- **Documentation associée :** Consulter [`docs/modeling/`](../../docs/modeling/) et [`docs/xai/06_source_xai.md`](../../docs/xai/06_source_xai.md).
