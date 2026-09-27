# SOURCE Development XAI (RF-04B)

## Purpose
To execute the frozen XAI protocol against the SOURCE predictive matrix and extract scientifically interpretable metrics.

## Scientific Question
Which physical state drivers and assimilation mechanics determine the absolute soil moisture update trajectory within the Noah-MP framework across 2019?

## Frozen Inputs
- Frozen `da_cdf` and `da_nocdf` SOURCE RF models (RF_A).
- Native 2019 cohorts (`source_cdf_native_2019.parquet`, `source_nocdf_native_2019.parquet`).
- Matched 2019 cohort (`source_matched_2019.parquet`) for direct attribution comparisons.
- Predefined scientific feature groups.
- Frozen TreeSHAP and permutation parameters.

## Planned Outputs
- Predictor-level mean |SHAP|.
- Scientific-group SHAP importance (absolute and normalized).
- Top predictors SHAP beeswarm visualizations.
- Explanatory dependence logic for physically dominant drivers.
- Permutation-importance tabular controls.

## Status
- **Status:** PLANNED
