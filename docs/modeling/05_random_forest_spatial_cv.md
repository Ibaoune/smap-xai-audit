# Random Forest Spatial Cross-Validation (RF-03A)

This document describes the spatial robustness phase (RF-03A) for the Random Forest pipeline. The goal is to evaluate the spatial stability of the selected, provisional configurations across 5 non-overlapping, 1-degree canonical spatial blocks.

## Scientific Objective & Constraints
- **Goal**: Evaluate out-of-sample spatial generalization.
- **2020 Data**: Strictly closed. Exclusively uses development years 2016-01-08 to 2019-12-31.
- **Artifact Retention**: `save_model: false` is used for all spatial-CV models.
- **Tuning**: Zero. The exact temporal configurations from RF-02 must be used.

## Configuration Matrix
Spatial robustness is evaluated strictly for the selected representative problems:
- **SOURCE**: `da_cdf`, `daily_absolute_increment`, `context_only_feature_set` | Configuration: **RF_A**
- **TRANSFER**: `da_cdf`, `delta_rzsm`, `source_context_feature_set` | Configuration: **RF_A**
- **VALUE**: `da_cdf`, `value_ae`, `value_context_feature_set` | Configuration: **RF_B**

## Methodology
- **Folds**: Exactly 5 canonical spatial folds (`fold_0` to `fold_4`).
- **Data Splitting**: For each fold $k$, the model trains on the four remaining folds and is evaluated on one held-out spatial fold composed of multiple 1-degree blocks. Folds must not be row-rebalanced.
- **Baselines**: Baseline skill reference must dynamically match the specific held-out spatial fold (e.g. `monthly_train_median` on `spatial_fold_0`).
- **Aggregation**: Metrics are aggregated across the 5 evaluation folds using unweighted means.
- **XAI Exclusion**: Do NOT compute feature importance or SHAP during RF-03A.

## Planned Post-Spatial Phase (RF-03B)
Upon successful completion of spatial robustness validation, the full Primary Matrix will execute using BOTH support grids for true comparability, keeping the tuned model specifications frozen.
