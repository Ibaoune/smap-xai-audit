# Random Forest Temporal Cross-Validation (RF-02)

This document describes the temporal cross-validation phase (RF-02) for the Random Forest pipeline. The goal is to identify a regularized configuration that learns useful predictive structure, remains stable across time, and improves on the statistical baseline.

## Scientific Objective & Constraints
- **Goal**: Explanation robustness. We are not performing leaderboard-style hyperparameter search.
- **2020 Data**: Strictly closed. No rows from 2020 are evaluated or used for tuning.
- **Artifact Retention**: `save_model: false` is used for all CV candidates to avoid storing multi-hundred-MB artifacts. Only metadata and metrics are retained.
- **Tree Count**: `n_estimators = 300` is fixed for RF-02. The CV primarily tests tree complexity, leaf regularization, and predictor subsampling.

## Candidate Configurations
Four predeclared configurations were evaluated:
- **RF_A**: max_depth=12, min_samples_leaf=10, max_features=0.7
- **RF_B**: max_depth=16, min_samples_leaf=5, max_features=0.7
- **RF_C**: max_depth=20, min_samples_leaf=5, max_features=0.7
- **RF_D**: max_depth=16, min_samples_leaf=10, max_features=1.0

## Temporal Folds (Expanding-Window)
- **fold_1**: Train 2016-01-08 to 2016-12-31, Val 2017-01-01 to 2017-12-31
- **fold_2**: Train 2016-01-08 to 2017-12-31, Val 2018-01-01 to 2018-12-31
- **fold_3**: Train 2016-01-08 to 2018-12-31, Val 2019-01-01 to 2019-12-31

## Selection Rule
The primary numerical criterion is the minimum unweighted mean of `fold_relative_error` across folds (`CV_relative_error`).
If two configurations have essentially equivalent CV performance (absolute difference <= 0.01), we prefer the less complex model (lower `max_depth`, larger `min_samples_leaf`).

## Selected Configurations
- **SOURCE** (`da_cdf`, `daily_absolute_increment`, `context_only_feature_set`):
  - Best CV Error: **RF_B** (0.3902), but **RF_A** (0.3908) is within 0.01.
  - Selected: **RF_A** (due to lower max_depth 12 vs 16).
- **VALUE** (`da_cdf`, `value_ae`, `value_context_feature_set`):
  - Best CV Error: **RF_C** (0.5247), but **RF_B** (0.5284) is within 0.01.
  - Selected: **RF_B** (due to lower max_depth 16 vs 20).
- **TRANSFER** (`da_cdf`, `delta_rzsm`, `source_context_feature_set`):
  - Best CV Error: **RF_A** (0.5524). **RF_B** (0.5601) is within 0.01 but is more complex.
  - Selected: **RF_A**.
