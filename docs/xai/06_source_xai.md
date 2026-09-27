# SOURCE Development XAI (RF-04B)

## Purpose
To execute the frozen XAI protocol against the SOURCE predictive matrix and extract scientifically interpretable metrics while keeping the 2020 dataset entirely sealed.

## Scientific Question
Given a pixel-day with a valid native EnKF innovation diagnostic, which environmental, antecedent land-state, and assimilation-context predictors are associated with the magnitude of the daily surface-soil-moisture analysis increment?

## Models Explained
Exactly four frozen models (RF_A configurations):
1. SOURCE `da_cdf` native support
2. SOURCE `da_nocdf` native support
3. SOURCE `da_cdf` matched support
4. SOURCE `da_nocdf` matched support

## Frozen Inputs
- Frozen `da_cdf` and `da_nocdf` SOURCE RF models (RF_A).
- Native 2019 cohorts (`source_cdf_native_2019.parquet`, `source_nocdf_native_2019.parquet`, 50k rows).
- Matched 2019 cohort (`source_matched_2019.parquet`, 50k rows) for direct attribution comparisons.
- Predefined scientific feature groups.
- Frozen TreeSHAP and permutation parameters.

## Execution QC and Integrity
- **Cohort checksums and identical keys**: Matched support cohorts were verified to be identical between CDF and NoCDF.
- **TreeSHAP Additivity**: Perfect numerical reconstruction achieved (max absolute error < 1e-4).
- **Feature Ordering**: Exactly 58 features evaluated in the exact fitted order.

## Global Predictor Results
Rankings evaluated using Mean |SHAP| and signed fractions. (Metrics stored dynamically in generated summaries).

## Grouped Results
Normalized group importance aggregates feature attribution by scientific groupings.

## Matched-Support Comparison
Direct comparison of `da_cdf` vs `da_nocdf` on the exact same pixel-day support yields rank correlations and overlap metrics indicating structural shifts in heuristic feature reliance without support-boundary bias.

## Native-vs-Matched Sensitivity
Comparisons within each experiment quantify sensitivity to the observation-support boundaries.

## Permutation-Importance Agreement
Nested 20,000-row subsets cross-validated TreeSHAP values, yielding strong Spearman correlations against standard `neg_mean_absolute_error` structural corruptions.

## Spatiotemporal Stability
- **DJF vs JJA Analysis**: Extracted from matched support outputs to characterize explanatory heterogeneity across the seasons.
- **Spatial-Fold Analysis**: Demonstrated stability boundaries across the 5 canonical spatial folds.

## Generated Development Figures
- `fig_source_a_group_importance.png`: Scientific-group normalized SHAP importance.
- `fig_source_b_top_predictors.png`: Top predictor mean_abs_shap comparisons.
- `fig_source_e_seasonal.png`: DJF vs JJA group importance.
- `fig_source_f_spatial.png`: Spatial-fold group importance stability.
*(Note: Dependence plots and beeswarms were generated dynamically in the development workspace).*

## Limitations
- **Descriptive Attribution**: SHAP values explain the model's heuristic predictive utilization, not absolute causal physical processes.
- **Correlated Predictors**: Shifts in rank among highly correlated meteorological variables indicate shared information rather than singular isolation.

## Status
- **Status:** COMPLETE
