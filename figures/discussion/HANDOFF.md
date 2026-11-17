# HANDOFF — Figure de discussion XAI pour J. Ahmad

## Emplacements
Racine du projet : `/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit`

| Quoi | Chemin (relatif à la racine) |
|---|---|
| Script (unique) | `scripts/figures/make_xai_figure_for_ahmad.py` |
| Figure | `figures/discussion/xai_figure_for_Ahmad.{png,pdf,svg}` |
| Valeurs panneau (b) | `figures/discussion/xai_figure_for_Ahmad_values.csv` |
| Notes (sources, hypothèses, caption) | `figures/discussion/xai_figure_for_Ahmad_notes.txt` |

Git : ces fichiers sont **non suivis** (branche `elaabar`), pas encore commités.

## Regénérer
```bash
cd /home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit
python3 scripts/figures/make_xai_figure_for_ahmad.py
```
Python : Anaconda 2020.11 (`python3`), matplotlib 3.3.2, pandas 2.0.3 (un warning numexpr peut s'afficher, sans effet).
Durée d'exécution : environ 15 à 60 s (lecture des parquets SHAP pour la vérification).

## Contenu de la figure
- **(a)** Schéma conceptuel : SMAP assimilation → SOURCE → TRANSFER → VALUE, avec un bandeau
  "Predictor families" (8 familles) et des flèches du bandeau vers chaque bloc.
- **(b)** Barres horizontales groupées CDF vs NoCDF : part de mean|SHAP| groupée (%) du modèle SOURCE,
  cible |δx|, hold-out 2020, **support matched** (n = 10 000), avec une colonne CDF − NoCDF (pp)
  et un encadré "Key reading".

## Entrées de données (lues par le script)
- `data/processed/modeling/xai/final_2020/summaries/tidy_group_summary.csv` → valeurs tracées
  (model_key `SOURCE_da_{cdf,nocdf}_daily_absolute_increment_matched_support`)
- `data/processed/modeling/xai/final_2020/shap/shap_SOURCE_*_matched_support_cohort.parquet`
  → recalcul de contrôle (colonnes `shap__<feature>`) ; écart actuel = 0.0000 pp
- `data/processed/modeling/xai/final_2020/summaries/source_matched_comparison_stats.json` → group ρ = 0.93
- `figures/manuscript/rf/rf_eval/Figure4_2020_holdout_metrics.csv` → R² SOURCE : CDF 0.58, NoCDF 0.24
- `configs/xai/feature_groups.yaml` → correspondance feature → famille (9 familles dans le registre)

## Résultats clés (CDF / NoCDF, %)
Antecedent SM 58.8 / 38.5 · Meteorology 19.9 / 26.7 · Soil 5.0 / 11.4 · Land cover 5.7 / 10.3 ·
Topography 1.0 / 3.5 · Temporal 9.6 / 9.6 · Fluxes et Assimilation history : absents du jeu SOURCE.

## Points de conception / pièges
- Les outils de lecture/écriture de fichiers de l'IDE peuvent être **bloqués hors du workspace NoahMP_Morocco** :
  passer par le shell (cat/sed/cp) ou écrire dans un dossier temporaire puis copier.
- Arial/Helvetica ne sont pas installées sur le cluster → **Nimbus Sans** (clone d'Helvetica). Le SVG est post-traité
  pour déclarer `Arial, Helvetica, Nimbus Sans`. Le PDF est en polices Type 3 (limitation matplotlib 3.3 avec les OTF).
- La mise en page est en **pouces absolus** (figure de 10 × 8.6 in) : le panneau (a) est un axe avec xlim(0,10)/ylim(0,3.6) ;
  le panneau (b) est positionné via `fx()/fy()` (conversion pouces → fraction de figure). Les blocs sont réglés par les
  constantes `BX`, `BW`, `BY0/BY1`, `PY0/PY1` ; l'axe des barres par `AXL, AXB, AXW, AXH` ; l'encadré "Key reading" par `KX`.
- Couleurs : CDF `#2F5D8C`, NoCDF `#D9893B` (teintes du manuscrit, désaturées).
- Les familles absentes de SOURCE sont affichées en gris "not in SOURCE predictor set†" (choix de conception, pas un résultat).

## Pistes d'amélioration ouvertes
1. Ajouter (ou non) la 9e famille `forcing_perturbation_controls` au bandeau (a) : nulle dans SOURCE,
   mais 9.3 % pour ΔQs en CDF.
2. Option : ajouter une variabilité par fold spatial dans (b) à partir de `final_2020/summaries/spatial_group_stability_2020.csv`
   (barres d'erreur min–max ou IQR).
3. Option : vue saisonnière DJF/JJA (`final_2020/summaries/seasonal_group_summary_2020.csv`).
4. Option : un mini-panneau (c) TRANSFER/VALUE pour montrer le rôle des familles absentes de SOURCE (`tidy_group_summary.csv`).
5. Le panneau (a) affiche "δx or |δx|" (demande de l'utilisateur) ; le modèle expliqué en (b) est |δx|.
6. Le jeu SOURCE context_only exclut volontairement innovation et forecast_variance de l'EnKF : point de discussion avec Ahmad.
