# Cadre Méthodologique et Scientifique de l'Audit XAI : SOURCE, TRANSFER, VALUE

**Auteur :** M. El Aabaribaoune (@um6p)
**Référence du projet :** `smap-xai-audit`
**Dépôt :** `/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit`

---

## 1. Définitions épistémologiques et frontière d'interprétation

Afin d'éviter tout glissement conceptuel entre prédiction statistique et dynamique physique, le cadre méthodologique établit quatre définitions fondamentales :

- **Modélisation prédictive (*Predictive Modeling*) :** Ajustement d'un modèle statistique supervisé (Random Forest) pour minimiser une fonction de perte d'erreur face à une cible définie ($R^2$, MAE, RMSE).
- **Explication du modèle (*Model Explanation*) :** Quantification mathématique (via les valeurs de Shapley TreeSHAP) de la manière dont le modèle statistique utilise ses prédicteurs pour générer ses prédictions.
- **Interprétation scientifique (*Scientific Interpretation*) :** Confrontation et mise en perspective des profils d'attribution du modèle statistique avec la théorie hydrologique et la connaissance du domaine géophysique.
- **Inférence causale (*Causal Inference*) :** Estimation rigoureuse de l'impact physique réel direct produit par une intervention ou une perturbation dans le système continu.

> **Déclaration de limite explicite :**
> Les valeurs SHAP expliquent l'attribution prédictive au sein du modèle Random Forest ajusté. **Elles n'établissent pas de relations causales physiques.**
> En présence de colinéarités fortes (ex. humidité de surface et humidité racinaire) ou de contraintes d'observation, les attributions SHAP reflètent la structure des heuristiques apprises par les arbres et ne doivent pas être surinterprétées comme la preuve des lois d'écoulement du modèle Noah-MP.

---

## 2. État d'avancement des protocoles XAI

| Étape / Protocole | Statut | Périmètre couvert |
| :--- | :---: | :--- |
| **RF-04A Protocol & Cohorts** | **COMPLÉTÉ** | Conception de la cohorte représentative (50k univers, 10k compute, 5k permutation). |
| **SOURCE Development XAI** | **COMPLÉTÉ** | Développement initial et profils d'attribution 2019 ([`06_source_xai.md`](06_source_xai.md)). |
| **TRANSFER Development XAI** | **COMPLÉTÉ** | Développement initial et profils multi-cibles 2019 ([`07_transfer_xai.md`](07_transfer_xai.md)). |
| **VALUE Development XAI** | **COMPLÉTÉ** | Développement initial et concordance GLEAM 2019 ([`08_value_xai.md`](08_value_xai.md)). |
| **Spatiotemporal Robustness** | **COMPLÉTÉ** | Stabilité sur 5 folds spatiaux et contrastes saisonniers DJF vs JJA ([`09_xai_spatiotemporal_robustness.md`](09_xai_spatiotemporal_robustness.md)). |
| **Protocol Freeze** | **COMPLÉTÉ** | Gel des hyperparamètres et des règles de sélection des dépendances ([`10_rf_xai_protocol_freeze.md`](10_rf_xai_protocol_freeze.md)). |
| **Final 2020 Holdout XAI** | **SCELLÉ / VÉRIFIÉ** | Modèles DA-NoCDF (support natif) évalués sur le banc d'essai scellé 2020 ([`11_final_2020_xai.md`](11_final_2020_xai.md)). |
| **DA-CDF Corrigée XAI** | **EN ATTENTE** | À exécuter sur la simulation DA-CDF corrigée après régénération des tables de données. |

---

## 3. Table des matières documentaire de `docs/xai/`

- [`01_rf_xai_protocol.md`](01_rf_xai_protocol.md) : Spécification complète du protocole de gel Random Forest et TreeSHAP.
- [`02_xai_cohort_design.md`](02_xai_cohort_design.md) : Stratégie d'échantillonnage équilibré (mois $\times$ blocs spatiaux).
- [`03_feature_group_contract.md`](03_feature_group_contract.md) : Nomenclature et cartographie des 58 caractéristiques en 9 groupes scientifiques.
- [`04_rf_shap_method.md`](04_rf_shap_method.md) : Fondements mathématiques de l'algorithme TreeSHAP appliqué aux forêts d'arbres.
- [`05_permutation_importance.md`](05_permutation_importance.md) : Protocole d'évaluation de la robustesse par permutation de variables.
- [`06_source_xai.md`](06_source_xai.md) : Rapport d'explicabilité détaillé du bloc SOURCE (support natif et apparié).
- [`07_transfer_xai.md`](07_transfer_xai.md) : Rapport d'explicabilité détaillé du bloc TRANSFER (4 cibles hydrologiques).
- [`08_value_xai.md`](08_value_xai.md) : Rapport d'explicabilité détaillé du bloc VALUE (concordance d'ET face à GLEAM).
- [`09_xai_spatiotemporal_robustness.md`](09_xai_spatiotemporal_robustness.md) : Résultats des tests de sensibilité spatiale et saisonnière.
- [`10_rf_xai_protocol_freeze.md`](10_rf_xai_protocol_freeze.md) : Décision formelle de gel méthodologique.
- [`11_final_2020_xai.md`](11_final_2020_xai.md) : Évaluation et attribution scellées sur l'année de test 2020.
- [`12_paper_figures.md`](12_paper_figures.md) : Spécifications des prototypes de figures pour la publication.

---

## 4. Approche 1 : SOURCE (Caractérisation de la correction d'analyse)

### Motivation et question scientifique
- **Motivation :** L'incrément de surface $\Delta\theta_1 = \theta_1^a - \theta_1^f$ est la porte d'entrée de toute l'information satellitaire. Comprendre quand et pourquoi le filtre applique une forte correction permet d'identifier les conditions où le modèle Noah-MP diverge le plus des observations SMAP.
- **Question scientifique :**
  *Quelles conditions environnementales antécédentes et contextuelles (humidité initiale, pluie passée, propriétés texturales et couverture végétale) sont statistiquement associées à l'amplitude de l'incrément d'analyse de surface appliqué par l'EnKF ?*

### Définition mathématique de la cible
- **[Implémenté & Vérifié]** Amplitude journalière de l'incrément de surface :
  $$\text{target} = \text{daily\_absolute\_increment} = |\Delta\theta_1^a| = |\theta_1^a - \theta_1^f| \quad (\text{m}^3\,\text{m}^{-3})$$
  Calculée pour les pixel-jours où une observation SMAP valide est assimilée (`obs_freq == 1`).
- **[Proposé]** Décomposition duale : (1) Amplitude normalisée par la capacité au champ $|\Delta\theta_1| / \theta_{\text{fc}}$ pour neutraliser l'effet d'échelle texturale ; (2) Modèle de classification du signe $\text{signe}(\Delta\theta_1) \in \{-1, +1\}$ pour séparer les régimes d'assèchement et d'humidification du filtre.

### Choix et justification des prédicteurs
- **[Implémenté & Vérifié]** 35 prédicteurs dans le mode `context_only_feature_set` :
  - *Humidité antécédente ($t-1$) :* `ssm_lag1`, `rzsm_lag1`.
  - *Météorologie antécédente :* `precip_lag1`, `precip_pre3d_sum`, `precip_pre7d_sum`, `tair_lag1`, moyennes Tair 3j et 7j.
  - *Propriétés statiques :* `elevation`, 15 classes de végétation MODIS, 7 classes de texture de sol STATSGO.
  - *Contexte temporel :* Mois, jour de l'année, `doy_sin`, `doy_cos`.
  - *Exclusion volontaire :* `innovation` ($y - Hx^f$), `forecast_variance` ($HPH^T$) et `normalized_innovation` sont strictement exclues du modèle contextuel pour empêcher la régression d'inverser trivialement l'équation de Kalman $K = P H^T (H P H^T + R)^{-1}$.
- **[Proposé]** Ajout de l'indice de déficit hydrique de surface et du temps écoulé depuis le dernier événement pluvieux.

### Construction du dataset et supports
- **[Implémenté & Vérifié]** Généré par `01_build_source_dataset.py`.
- **Support natif :** Restreint aux pixel-jours où l'innovation de l'expérience est finie et non masquée ($N \approx 5{,}88 \times 10^6$ en NoCDF train, $1{,}60 \times 10^6$ en test 2020).
- **Support apparié :** Restreint à l'intersection des innovations finies CDF et NoCDF.

### Modèles, baselines et résultats
- **[Implémenté & Vérifié]** Random Forest `RF_A` (300 arbres, profondeur 12, `min_samples_leaf` = 10, `max_features` = 0.7).
- **Baseline :** Médiane mensuelle d'entraînement.
- **Résultats NoCDF natif (Holdout 2020) :** $R^2 = 0{,}247$, $r = 0{,}497$, $\text{MAE} = 0{,}0081\text{ m}^3\,\text{m}^{-3}$, Skill MAE = 15,4 %.
- **Attribution SHAP vérifiée :** Forte dominance de l'humidité antécédente `ssm_lag1` (58,7 % de l'importance totale en CDF historique, 38,7 % en NoCDF).

### Signification et limites de l'attribution SHAP
- *Limite épistémologique :* En l'absence de l'innovation, le modèle RF prédit la susceptibilité statistique du sol : les sols secs en été s'écartent davantage de la climatologie SMAP. SHAP met en évidence la réceptivité du sol et non le mécanisme interne du filtre.

### Contribution au storytelling du papier
- Démontre que la dynamique des corrections EnKF est fortement modulée par l'état hydrique antécédent et la saisonnalité plutôt que par le seul forçage pluviométrique immédiat.

---

## 5. Approche 2 : TRANSFER (Émulation de la réponse dynamique de la colonne)

### Motivation et question scientifique
- **Motivation :** L'assimilation ne modifie directement que la couche 1 (0–10 cm). L'impact hydrologique dépend entièrement de la façon dont les équations de Noah-MP transfèrent cette eau vers la zone racinaire et modifient les flux d'énergie de surface.
- **Question scientifique :**
  *Dans quelle mesure une perturbation d'humidité injectée en surface est-elle statistiquement prédictive des modifications de l'humidité racinaire et des flux couplés d'évapotranspiration, de ruissellement et de drainage ?*

### Définition mathématique des cibles
- **[Implémenté & Vérifié]** Quatre cibles différentielles journalières $(\text{DA} - \text{OPL})$ :
  $$\Delta \text{RZSM}_t = \text{RZSM}_t^{\text{DA}} - \text{RZSM}_t^{\text{OPL}} \quad (\text{m}^3\,\text{m}^{-3})$$
  $$\Delta \text{ET}_t = \text{ET}_t^{\text{DA}} - \text{ET}_t^{\text{OPL}} \quad (\text{mm}\,\text{d}^{-1})$$
  $$\Delta \text{Runoff}_t = Q_{s,t}^{\text{DA}} - Q_{s,t}^{\text{OPL}} \quad (\text{mm}\,\text{d}^{-1})$$
  $$\Delta \text{Baseflow}_t = Q_{sb,t}^{\text{DA}} - Q_{sb,t}^{\text{OPL}} \quad (\text{mm}\,\text{d}^{-1})$$
- **[Proposé]** Dérivation des taux de transfert nets instantanés :
  $$\delta(\Delta\text{RZSM}_t) = \Delta\text{RZSM}_t - \Delta\text{RZSM}_{t-1}$$
  afin de neutraliser l'autocorrélation temporelle cumulative et d'isoler la réponse impulsionnelle de la journée.

### Choix et justification des prédicteurs
- **[Implémenté & Vérifié]** 52 prédicteurs dans `source_context_feature_set` :
  - *Source d'assimilation :* `source_signed_increment_t`, cumuls 3j et 7j, fréquence d'observation passée.
  - *Contexte environnemental ($t-1$) :* Forçage pluie/température, flux OPL antécédents (`et_opl_lag1`, `baseflow_opl_lag1`, etc.).
  - *Contrôle de forçage :* `delta_precip_forcing_t` (écart de pluie induit par les perturbations d'ensemble LIS).
  - *Statiques et temporels :* Classes de sol, végétation et calendrier.
- **[Proposé]** Retrait de `delta_precip_forcing` (qui agit comme une fuite du générateur d'ensemble) et ajout explicite de la conductivité hydraulique saturée.

### Construction du dataset et supports
- **[Implémenté & Vérifié]** Généré par `02_build_transfer_dataset.py`.
- **Support continu :** Les 16 030 pixels continentaux sur les 1 827 jours ($N \approx 23{,}3 \times 10^6$ lignes en train, $5{,}87 \times 10^6$ en test 2020).

### Modèles, baselines et résultats
- **[Implémenté & Vérifié]** Random Forest `RF_A` (300 arbres, profondeur 12).
- **Baseline :** Moyenne mensuelle d'entraînement.
- **Résultats NoCDF natif (Holdout 2020) :**
  - $\Delta\text{RZSM}$ : $R^2 = 0{,}475$, $r = 0{,}709$, Skill MAE = 33,0 %.
  - $\Delta\text{ET}$ : $R^2 = 0{,}567$, $r = 0{,}760$, Skill MAE = 41,2 %.
  - $\Delta\text{Runoff}$ : $R^2 = 0{,}465$, $r = 0{,}723$, Skill MAE = 55,0 %.
  - $\Delta\text{Baseflow}$ : $R^2 = 0{,}329$, $r = 0{,}601$, Skill MAE = 49,8 %.
- **Attribution SHAP vérifiée :**
  - $\Delta\text{RZSM}$ dominé par l'humidité antécédente (40,1 %) et l'assimilation (10,0 %).
  - $\Delta\text{ET}$ dominé par les flux OPL antécédents (29,8 %) et l'assimilation (20,0 %).
  - $\Delta\text{Runoff}$ dominé par la pluie (30,0 %), la végétation (20,6 %) et le forçage perturbé LIS (2,2 % en NoCDF, 7,5 % en CDF historique).

### Signification et limites de l'attribution SHAP
- *Limite d'autocorrélation :* L'état racinaire ayant une mémoire de plusieurs semaines, le modèle RF utilise les flux OPL antécédents et les propriétés du sol comme proxy de l'état accumulé plutôt que de quantifier la physique du front d'infiltration.

### Contribution au storytelling du papier
- Révèle le contraste entre la dynamique rapide des flux de surface ($\Delta\text{ET}$, $\Delta\text{Runoff}$) fortement couplés au forçage immédiat, et la dynamique lente et intégrative du profil racinaire ($\Delta\text{RZSM}$) et du drainage profond ($\Delta\text{Baseflow}$).

---

## 6. Approche 3 : VALUE (Concordance avec une référence satellite indépendante)

### Motivation et question scientifique
- **Motivation :** L'assimilation modifie les flux, mais améliore-t-elle leur concordance avec des observations externes ? L'évaluation face à un jeu satellite tiers et indépendant (GLEAM v4.3a) permet d'auditer la valeur ajoutée du produit SMAP.
- **Question scientifique :**
  *Sous quelles conditions environnementales, spatiales et météorologiques l'assimilation SMAP réduit-elle (ou augmente-t-elle) l'écart d'évapotranspiration par rapport à la référence indépendante GLEAM v4.3a ?*

### Définition mathématique de la cible
- **[Implémenté & Vérifié]** Gain d'erreur absolue :
  $$\text{value\_ae} = |\text{ET}_{\text{OPL}} - \text{ET}_{\text{GLEAM}}| - |\text{ET}_{\text{DA}} - \text{ET}_{\text{GLEAM}}| \quad (\text{mm}\,\text{d}^{-1})$$
  - $\text{value\_ae} > 0$ : Gain de concordance (la DA rapproche Noah-MP de GLEAM).
  - $\text{value\_ae} < 0$ : Désaccord accru (la DA éloigne Noah-MP de GLEAM).
- **[Proposé]** Formulation normalisée par rapport à l'écart-type saisonnier de GLEAM, et stratification par régimes écohydrologiques (régime limité par l'eau vs limité par l'énergie).

### Choix et justification des prédicteurs
- **[Implémenté & Vérifié]** 52 prédicteurs dans `value_context_feature_set` projetés sur la maille $0{,}25^\circ$ :
  - Incréments agrégés, fraction de surface assimilée (`finite_innovation_fraction_t`).
  - Flux OPL antécédents, forçages atmosphériques rééchantillonnés, texture et couvert végétal agrégés.
  - *Interdictions strictes :* Aucune donnée GLEAM contemporaine, aucun flux DA contemporain, pas de `value_ae_lag1` (pour éviter toute fuite d'évaluation).

### Construction du dataset et supports
- **[Implémenté & Vérifié]** Généré par `03_build_value_dataset.py`.
- **Support :** 4 110 mailles de la grille GLEAM ($0{,}25^\circ$) sur 1 827 jours ($N \approx 5{,}98 \times 10^6$ lignes en train, $1{,}50 \times 10^6$ en test 2020).

### Modèles, baselines et résultats
- **[Implémenté & Vérifié]** Random Forest `RF_B` (300 arbres, profondeur 16, `min_samples_leaf` = 5, `max_features` = 0.7).
- **Baseline :** Médiane mensuelle d'entraînement.
- **Résultats NoCDF natif (Holdout 2020) :** $R^2 = 0{,}311$, $r = 0{,}568$, $\text{MAE} = 0{,}148\text{ mm}\,\text{d}^{-1}$, Skill MAE = 22,2 %.
- **Distribution observée (2019) :** La médiane de `value_ae` est légèrement négative ($-0{,}024\text{ mm}\,\text{d}^{-1}$ en CDF historique, $-0{,}005$ en NoCDF) ; 58 % des points présentent une dégradation relative en CDF historique et 51 % en NoCDF.

### Signification et limites de l'attribution SHAP
- *Limite de la référence externe :* GLEAM v4.3a est elle-même une modélisation diagnostique forcée par satellite. Une amélioration face à GLEAM peut traduire une convergence structurelle (paramétrisation commune de l'évaporation) plutôt qu'une vérité physique de terrain absolue.
- *Sensibilité du hinge en zéro :* La métrique $|e_{\text{OPL}}| - |e_{\text{DA}}|$ oscille fortement autour de zéro pour les faibles flux hivernaux.

### Contribution au storytelling du papier
- Fournit une cartographie explicative des contextes où l'assimilation apporte un gain avéré (plaines semi-arides, régimes d'eau limitée) et des zones où elle risque de dégrader les bilans énergétiques (zones humides, orographie complexe).

---

## 7. Synthèse comparative des trois approches

| Dimension | SOURCE | TRANSFER | VALUE |
| :--- | :--- | :--- | :--- |
| **Phénomène modélisé** | Décision locale du filtre EnKF | Réponse interne de Noah-MP | Confrontation à GLEAM v4.3a |
| **Cible principale** | $|\Delta\theta_1^a|$ ($\text{m}^3\,\text{m}^{-3}$) | $\Delta\text{RZSM}$, $\Delta\text{ET}$, $\Delta Q_s$, $\Delta Q_{sb}$ | $\text{value\_ae}$ ($\text{mm}\,\text{d}^{-1}$) |
| **Prédicteurs actifs** | 35 (`context_only`) | 52 (`source_context`) | 52 (`value_context`) |
| **Résolution spatiale** | $121 \times 181$ (/usr/bin/bash{,}05^\circ pprox 5	ext{ km}$) | $121 \times 181$ (/usr/bin/bash{,}05^\circ pprox 5	ext{ km}$) | $0{,}25^\circ$ ($\approx 25\text{ km}$) |
| **Architecture modèle** | RF_A (prof. 12, leaf 10) | RF_A (prof. 12, leaf 10) | RF_B (prof. 16, leaf 5) |
| **Statut implémenté** | Entièrement codé (scripts 01, 03, 04, 05) | Entièrement codé (scripts 02, 06, 07, 08) | Entièrement codé (scripts 03, 09, 10, 11) |
| **Statut vérifié** | Validé sur NoCDF natif (2020) | Validé sur NoCDF natif (2020) | Validé sur NoCDF natif (2020) |
| **Statut proposé** | Normalisation par $\theta_{\text{fc}}$ | Cibles en flux nets instantanés $\delta(\Delta)$ | Métrique relative pondérée par l'ET |
