# Permutation Importance Methodology

## Purpose
To mathematically outline and freeze a model-agnostic robustness control. This establishes baseline consistency checks for TreeSHAP importance outputs across the models.

## Scientific Question
If we actively corrupt a given variable distribution uniformly, what impact does this randomly permuted state independently enact on the overall skill metric?

## Frozen Inputs
- **Cohort Size:** 20,000 deterministically nested subset rows.
- **Library Module:** `sklearn.inspection.permutation_importance`
- **Metric Scoring Strategy:** `neg_mean_absolute_error`
- **Number of Permutation Shuffles (n_repeats):** 5
- **Deterministic Seed (random_state):** 42

## Contract Requirements
- The protocol explicitly measures the deterioration of the MAE loss configuration via independent structural perturbations.
- The pipeline mathematically ensures strict column alignment across all 58 predictors.
- During the RF-04A development testing protocol, the native SOURCE `da_cdf` permutation control successfully matched the dimensional structure of the predictive components exactly.

## Correlated Predictor Caution
Permutation importance, identically to SHAP, suffers instability under extensive physical correlation regimes since model reliance splits among highly comparable variables. Robustness must therefore be interpreted holistically.

## Status
- **Status:** COMPLETE
- Configuration dynamically checked and loaded from `configs/xai/rf_xai.yaml`.
- Code module defined at `src/smap_xai/xai/permutation.py`.
