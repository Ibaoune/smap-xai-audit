# Random Forest XAI Protocol (RF-04)

## 1. Development and Validation Setup
The entire Explainable AI (XAI) protocol is explicitly developed, balanced, and frozen using the canonical **2019 validation period**. 2020 remains sealed. This builds upon the [Random Forest Development Matrix](../../docs/modeling/06_random_forest_development_matrix.md).

The identical cohort-generation algorithm and explanation settings will be applied later to the final 2020 independent test set. No parameter or predictor-group definition may be changed after unsealing 2020.

## 2. Cohort Generation Principles
Cohorts are drawn strictly between `2019-01-01` and `2019-12-31`.

Sampling must be deterministic, target-independent, and reproducible. Stratification is only permitted by `month` and canonical `spatial_fold`. Target stratification (by target magnitude, sign, predicted value, SHAP value, or residual) is strictly forbidden to preserve the true distributional characteristics of the validation year.

**Cohort Sizes**:
- **Primary SHAP cohort**: 50,000 rows.
- **Permutation cohort**: 20,000 rows (a strict nested deterministic subset of the SHAP cohort).
- **Matched SOURCE Support**: Identical sample count and key sets for `da_cdf` and `da_nocdf` are required for direct attribution comparison.

## 3. Explanation Methodology

### TreeSHAP
- **Explainer Class**: `shap.TreeExplainer`
- **Feature Perturbation Mode**: `tree_path_dependent` (for RF models to avoid needing a background dataset).
- **Model Output Mode**: Raw margin/additive expected value.
- **Note**: Predictors may be highly correlated. SHAP allocations among correlated variables can be unstable. SHAP output does not represent causal attribution.

### Permutation Importance
Used as a model-agnostic robustness control. Scored via negative MAE using 5 deterministic repeats (`random_state=42`).

## 4. Output Summary Requirements
1. Absolute Grouped Importance (`sum(|SHAP_ij|)` over predictors in the group).
2. Normalized Group Contribution.
3. Predictor-level statistics: `mean_abs_shap`, `mean_signed_shap`, `median_shap`, `positive_shap_fraction`, `negative_shap_fraction`.

Final paper analyses will include dependency plots whose predictor features must be defined systematically before execution (e.g., top global SHAP predictors + pre-declared scientifically relevant predictors).
