# Random Forest Reference Pipeline

This document describes the planned workflow for the Random Forest (RF) modeling pipeline. 

**Note:** Random Forest is the first model family implemented end-to-end to establish the complete model-agnostic scientific pipeline. It is NOT being selected as "the best model." Predictive adequacy is a prerequisite, and explanation robustness across model families is the final objective. The pipeline will later be reused unchanged by XGBoost and MLP.

## RF-01: Infrastructure and Pilots
The goal of this phase is infrastructure validation. We will run conservative, bounded RF models (e.g., n_estimators=200, max_depth=16) on the primary development split (Train: 2016-2018, Val: 2019) to ensure that the model-agnostic architecture supports full end-to-end training and evaluation, strictly isolating 2020. 

## RF-02: Temporal CV and Tuning (Plan)
*To be executed in the next stage.*
We will perform an expanding-window CV:
- 2016 -> 2017
- 2016-2017 -> 2018
- 2016-2018 -> 2019

A small predeclared RF search will consider a limited set of hyperparameters (`n_estimators`, `max_depth`, `min_samples_leaf`, `max_features`, and optionally `max_samples`). No giant benchmark/grid will be used.

### Artifact Retention Policy
To prevent CV/tuning artifacts from consuming tens of GB, we enforce an explicit artifact retention policy via a configurable `save_model` flag:
- Metrics and metadata are retained for **every candidate** in the CV process.
- The `model.joblib` binary is **only retained** for:
  - Selected/frozen configurations.
  - Models explicitly required for later XAI analysis.
  - Explicitly requested debugging cases.
- **RF-01 Defaults:** `save_model: true` (Existing pilots are kept).
- **Future RF-02 Tuning Candidates:** `save_model: false`.
- **Selected Model Refit:** `save_model: true`.


## RF-03: Complete RF Matrix (Plan)
The full matrix will be executed after pilot validation and tuning.

**SOURCE:**
- da_cdf, da_nocdf
- context_only_feature_set

**TRANSFER:**
- da_cdf, da_nocdf
- delta_rzsm, delta_et, delta_surface_runoff, delta_baseflow
- Primary: source_context_feature_set
- Sensitivities: memory_augmented_feature_set, source_context_without_forcing_control

**VALUE:**
- da_cdf, da_nocdf
- Primary: value_context_feature_set
- Sensitivities: value_memory_augmented_feature_set, value_transfer_informed_feature_set

## RF-04: RF XAI Common Cohort Contract (Design)
The future XAI cohort must:
- Come from development validation support, primarily 2019.
- Be deterministic.
- Be independent of target magnitude/sign.
- Use date/location identifiers.
- Be exactly identical across RF/XGBoost/MLP for a given scientific problem.

Cross-model explanation robustness requires exactly the same XAI rows. Stratified samples will not be created.

### Future XAI Output Contract
The model-agnostic table schema will include:
- `model_family`
- `block`
- `experiment`
- `target`
- `feature_set`
- `sample_id`
- `feature`
- `feature_group`
- `shap_value`
- `feature_value`

Aggregated tables will contain `mean_abs_shap`, `signed_mean_shap`, `rank`, and `feature_group importance`.

## RF-05: Paper Postprocessing Contract (Design)
Future RF-05 figures will consume generic tables rather than RF-specific objects. Plotting inputs must carry `model_family` so XGBoost/MLP can later be added without redesign.

Planned paper outputs:
- Predictive skill relative to baseline
- Global predictor-group importance
- Top-predictor SHAP distributions
- SHAP dependence relationships
- Seasonal robustness
- Spatial robustness where justified
