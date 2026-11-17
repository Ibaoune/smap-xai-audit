# Spécification et Protocole Scientifique du Bloc SOURCE (`docs/xai/06_source_xai.md`)

**Auteur :** M. El Aabaribaoune (@um6p)  
**Branche active :** `elaabar`  
**Statut :** Protocole révisé — Phase de préparation expérimentale (aucun entraînement actif).

---

> [!WARNING]
> **Avertissement méthodologique sur les résultats historiques DA-CDF :**  
> Les attributions SHAP historiques de la simulation DA-CDF issues de la phase RF-04B antérieure au 27 octobre 2026 reposent sur une fonction de transfert CDF calculée sur une grille géographique discordante. Elles sont **formellement invalidées** (voir [`docs/invalidated_legacy_cdf_results.md`](../invalidated_legacy_cdf_results.md)). Seules les métriques et attributions de la simulation **DA-NoCDF native** constituent des résultats historiquement vérifiés. Les analyses comparatives avec la DA-CDF seront réexécutées sur la simulation corrigée.

---

## 1. Contrat scientifique SOURCE consolidé

### A. Motivation et question scientifique
- **Motivation :** L'incrément de surface en couche 1 ($0\text{--}10\text{ cm}$) constitue le point d'injection initial de l'information satellitaire SMAP dans Noah-MP. Analyser les conditions préexistantes associées à ces ajustements permet d'auditer la réceptivité environnementale du modèle avant toute propagation dans le profil racinaire.
- **Question scientifique :**  
  *Dans quelle mesure le contexte environnemental antécédent et statique (état hydrique initial, forçage météorologique passé, texture de sol, couverture végétale et calendrier saisonnier) permet-il d'anticiper l'intensité des mises à jour appliquées par le filtre EnKF, en l'absence de l'observation satellitaire elle-même ?*

### B. Définition mathématique exacte de la cible
- **[Implémenté & Vérifié]** Amplitude absolue de l'incrément journalier d'analyse :
  $$\text{target} = \text{daily\_absolute\_increment} = |\Delta\theta_1^a| = |\theta_1^a - \theta_1^f| \quad (\text{m}^3\,\text{m}^{-3})$$
- **Distinction opérationnelle des grandeurs EnKF :**
  1. *Innovation finie ($y - Hx^f \in \mathbb{R}$) :* Écart brut entre la mesure SMAP valide et la prévision moyenne d'ensemble.
  2. *Observation acceptée par le filtre :* Observation ayant passé avec succès les tests de contrôle qualité internes de LIS EnKF (absence de gel, pluie non saturante).
  3. *Incrément appliqué ($\Delta\theta_1^a = K(y - Hx^f)$) :* Correction effective calculée via le gain de Kalman $K$. Sur le domaine NorthMor ($0{,}05^\circ \approx 5\text{ km}$), chaque pixel continental ne reçoit au plus qu'une observation acceptée par jour civil UTC (`observation_frequency` $\in \{0, 1\}$).
- **[Proposé]** Formulation normalisée optionnelle : $|\Delta\theta_1^a| / \theta_{\text{fc}}$ (analyse de sensibilité à l'échelle de capacité au champ).

### C. Définition des prédicteurs (35 variables contextuelles)
- **[Implémenté & Vérifié]** Mode `context_only_feature_set` :
  - *États hydriques antécédents ($t-1$) :* `ssm_lag1`, `rzsm_lag1`.
  - *Météorologie antécédente ($t-1$ à $t-7$) :* `precip_lag1`, `precip_pre3d_sum`, `precip_pre7d_sum`, `tair_lag1`, `tair_pre3d_mean`, `tair_pre7d_mean`.
  - *Propriétés statiques géophysiques :* `elevation`, 15 classes de couvert végétal MODIS, 7 fractions texturales STATSGO.
  - *Contexte temporel :* `month`, `day_of_year`, composantes harmoniques `doy_sin`, `doy_cos`.
- **Règle d'exclusion anti-tautologique :**  
  Les variables d'assimilation directes (`innovation`, `forecast_variance`, `normalized_innovation`) sont délibérément exclues du modèle contextuel pour empêcher la régression d'inverser trivialement la matrice de Kalman, ce qui étoufferait les facteurs environnementaux.

### D. Portée et limites épistémologiques
1. **Ce que SOURCE démontre :** La susceptibilité statistique et la réceptivité du paysage aux corrections EnKF.
2. **Ce que SOURCE ne démontre pas :** Il ne prouve pas de causalité physique directe (les corrélations fortes avec l'humidité antécédente sont partiellement portées par la saisonnalité climatique méditerranéenne).
3. **Dépendances spatio-temporelles :** Malgré le décalage temporel ($t-1$), la forte autocorrélation spatiale des champs météorologiques et hydrologiques réduit le nombre effectif de degrés de liberté.

---

## 2. Matrice des quatre expériences contrôlées

| Expérience | Question scientifique | Cible | Prédicteurs | Support de données | Baselines | Métriques | Validation spatio-temporelle |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A. Amplitude absolue (Référence)** | Dans quelle mesure le contexte antécédent prédit-il l'amplitude de mise à jour EnKF ? | $|\Delta\theta_1^a|$ ($\text{m}^3\,\text{m}^{-3}$) | 35 variables contextuelles (`context_only`) | Pixel-jours avec `obs_freq == 1` | Médiane mensuelle par pixel, Régression Ridge linéaire | $R^2$, Pearson $r$, MAE, RMSE, Skill MAE | Train 2016–2019, Test 2020 scellé, Block-CV 5 folds ($1^\circ \times 1^\circ$) |
| **B. Signe de l'incrément (Direction)** | Le contexte environnemental permet-il d'anticiper le sens de la correction (humidification vs assèchement) ? | $Y \in \{0, 1\}$ ($1 \text{ si } \Delta\theta_1^a > +\epsilon$, $0 \text{ si } \Delta\theta_1^a < -\epsilon$) | Mêmes 35 variables contextuelles | Pixel-jours avec $\|\Delta\theta_1^a\| > \epsilon$ ($\epsilon = 0{,}002\text{ m}^3\,\text{m}^{-3}$) | Fréquence majoritaire, Mode mensuel par pixel, Régression logistique | Accuracy, F1 pondéré, AUC-ROC, Brier Score | Train 2016–2019, Test 2020 scellé, Block-CV 5 folds ($1^\circ \times 1^\circ$) |
| **C. Contextuel vs Mécanistique** | Quel est le saut de prédictibilité apporté par la connaissance de l'innovation et de l'incertitude du filtre ? | $|\Delta\theta_1^a|$ | Mêmes 35 variables + `innovation` ($y - Hx^f$) + `forecast_variance` ($HPH^T$) | Pixel-jours avec `obs_freq == 1` | Modèle contextuel (Exp. A), Régression linéaire sur l'innovation | $\Delta R^2$, $\Delta\text{MAE}$, divergence de rangs SHAP | Train 2016–2019, Test 2020 scellé, Block-CV 5 folds ($1^\circ \times 1^\circ$) |
| **D. Amplitude normalisée (Sensibilité)** | La modulation de l'incrément par la texture est-elle un artefact d'échelle de la capacité au champ ? | $|\Delta\theta_1^a| / \theta_{\text{fc}}$ (sans unité) | Mêmes 35 variables contextuelles | Pixel-jours avec `obs_freq == 1` | Médiane mensuelle normalisée, Régression Ridge | $R^2$, Pearson $r$, MAE normalisée, rangs SHAP | Train 2016–2019, Test 2020 scellé, Block-CV 5 folds ($1^\circ \times 1^\circ$) |

---

## 3. Justification détaillée des choix méthodologiques

### Justification de la bande morte $[-\epsilon, +\epsilon]$ pour le Signe (Expérience B)
L'incrément EnKF est calculé à partir d'un ensemble de 12 membres et d'observations satellitaires entachées d'un bruit radiométrique ($\sigma_{\text{SMAP}} \approx 0{,}04\text{ m}^3\,\text{m}^{-3}$).  
Les variations infinitésimales ($|\Delta\theta| < 0{,}002\text{ m}^3\,\text{m}^{-3}$) représentent du bruit d'échantillonnage de l'ensemble et non une direction physique d'ajustement. L'exclusion de cette zone morte est indispensable pour éviter d'entraîner le classifieur sur du bruit aléatoire.

### Portée et limites du modèle mécanistique (Expérience C)
L'intégration de l'innovation $d = y - Hx^f$ permet de vérifier si la Random Forest apprend fidèlement l'opérateur de Kalman $K$. Cependant, une performance élevée ne doit pas être interprétée comme la preuve d'un émulateur physique complet, car la Random Forest tend à linéariser la relation $\Delta\theta \approx K \cdot d$ sans reproduire explicitement les covariances d'erreur d'état de LIS.

### Limite de la normalisation par la capacité au champ (Expérience D)
Normaliser par $\theta_{\text{fc}}$ ajuste l'échelle volumique, mais n'élimine pas l'influence de la texture de sol : la conductivité hydraulique saturée ($K_{\text{sat}}$) et l'indice de distribution des pores continuent de régir la vitesse d'infiltration et l'évaporation dans Noah-MP.

---

## 4. Résultats historiquement vérifiés (DA-NoCDF native — Holdout 2020)

Les seules métriques formellement vérifiées et scellées sous le commit `bb777c91889d76ecab02067520c9a9f948f3563e` pour le modèle de référence SOURCE (`RF_A`, support natif NoCDF) sont :

| Métrique | Valeur vérifiée | Interprétation rigoureuse |
| :--- | :---: | :--- |
| **$N_{\text{train}}$ (2016–2019)** | 5 881 531 | Échantillons d'apprentissage continus sur 4 années. |
| **$N_{\text{test}}$ (2020)** | 1 596 590 | Échantillons de test scellés sur 1 année indépendante. |
| **$R^2$** | **0,247** | Environ 25 % de la variance de magnitude est expliquée par la RF. |
| **Pearson $r$** | **0,497** | Corrélation linéaire modérée entre incrément réel et prédit. |
| **MAE** | **$0{,}0081\text{ m}^3\,\text{m}^{-3}$** | Erreur absolue moyenne sur le domaine. |
| **RMSE** | **$0{,}0132\text{ m}^3\,\text{m}^{-3}$** | Erreur quadratique moyenne. |
| **Biais moyen** | **$-0{,}00018\text{ m}^3\,\text{m}^{-3}$** | Biais moyen d'estimation quasi nul. |
| **Skill MAE (vs Médiane mensuelle)** | **15,4 %** | La RF réduit l'erreur de 15,4 % par rapport à la médiane mensuelle locale. |

*Note sur le Skill MAE :* Ce gain de 15,4 % démontre que la RF apporte une information météorologique et environnementale supérieure à la simple climatologie locale, mais les 84,6 % d'erreur résiduelle rappellent qu'une fraction majeure de la variabilité instantanée de l'incrément demeure imprévisible sans l'innovation satellite.

---

## 5. Protocole de comparaison NoCDF vs DA-CDF corrigée

1. **Double régime d'évaluation :**
   - *Support natif :* Caractérise le comportement intrinsèque de chaque chaîne d'assimilation sur sa couverture réelle.
   - *Support apparié :* Évalue les deux modèles sur l'intersection temporelle et spatiale exacte des pixel-jours finis pour comparer loyalement les profils d'attribution TreeSHAP.
2. **Validation par blocs spatiaux réguliers :**
   - Utilisation des 5 blocs géographiques de $1{,}0^\circ \times 1{,}0^\circ$ déclarés dans [`configs/modeling/splits.yaml`](../../configs/modeling/splits.yaml) (et non des bassins hydrographiques ad-hoc) pour quantifier la stabilité des classements SHAP.
3. **Interdiction de surinterprétation causale :**
   - Les écarts d'attribution SHAP entre NoCDF et CDF corrigée reflètent des différences dans l'exploitation statistique des prédicteurs par les modèles, et non une mesure causale de la modification de la dynamique physique.
