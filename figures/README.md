# Figures du projet SMAP-XAI Audit

Ce répertoire centralise les sorties graphiques produites pour l'analyse de l'assimilation SMAP / Noah-MP, l'évaluation des modèles d'apprentissage et leur explicabilité (XAI).

## Organisation scientifique cible

Les figures sont progressivement classées par thématique scientifique, indépendamment de la structure d'un manuscrit ou d'une phase de calcul :

- **`assimilation/`** : diagnostics EnKF directs (innovations SMAP, incréments d'analyse, support spatio-temporel d'échantillonnage, analyses texturales).
- **`water_balance/`** : comptabilité volumique des incréments d'assimilation en couche de surface (ajustements positifs/négatifs en équivalent eau) et diagnostics hydriques associés.
- **`validation/`** : confrontations physiques directes aux observations satellitaires indépendantes (ex. ASCAT, GLEAM v4.3a).
- **`modeling/`** : protocoles d'entraînement, validation croisée temporelle/spatiale et métriques de performance ($R^2$, RMSE) des modèles Random Forest et baselines.
- **`xai/`** : profils d'attribution (valeurs SHAP, importances par permutation), dépendances partielles et robustesse spatio-temporelle des explications.

## Répertoires existants et transition

Les dossiers actuels (`main/`, `supplement/`, `manuscript/`, `audit/`, `discussion/`) conservent temporairement leur contenu pour préserver l'historique de travail. Leur migration vers les catégories scientifiques cibles s'effectue de manière progressive et concertée.

## Précautions de provenance scientifique

- **Sorties DA-CDF historiques :** Les figures conditionnées par l'ancienne simulation DA-CDF (ou fondées sur un échantillon apparié dépendant de celle-ci) sont documentées comme scientifiquement invalides suite à la détection d'une discordance de domaine spatial. Elles ne doivent pas être utilisées comme résultats définitifs. Consulter [`docs/invalidated_legacy_cdf_results.md`](../docs/invalidated_legacy_cdf_results.md) pour le détail du périmètre concerné.
- **Règle de traçabilité :** Toute figure conservée ou réorganisée doit être explicitement documentée avec son script producteur, ses fichiers de données sources exacts et l'expérience de modélisation associée (OPL, DA-NoCDF, etc.).
