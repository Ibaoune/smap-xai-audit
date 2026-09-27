# VALUE Development XAI (RF-04D)

## Purpose
To execute the frozen XAI protocol against the VALUE predictive matrix to determine independent benchmark consistency.

## Scientific Question
Which temporal and contextual mechanics predict independent performance deviations (`value_ae`) against the GLEAM evaporative fraction benchmarks?

## Frozen Inputs
- Frozen `da_cdf` and `da_nocdf` VALUE RF models (RF_B).
- The verified single-support `value_2019.parquet` shared GLEAM-grid cohort.
- Predefined scientific feature groups.
- Frozen TreeSHAP and permutation parameters.

## Planned Outputs
- Predictor-level mean |SHAP|.
- Scientific-group SHAP importance for benchmark differences.
- Dependence relationships characterizing predictive error spaces.
- Permutation-importance validation.

## Status
- **Status:** PLANNED
