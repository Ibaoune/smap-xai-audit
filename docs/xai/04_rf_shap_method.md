# Random Forest SHAP Methodology

## Purpose
To mathematically outline and freeze the specific implementation mechanics and configurations of the Shapley Additive Explanations (SHAP) algorithm selected to describe the behavior of the frozen Random Forest models.

## Scientific Question
How do inputs strictly combine to form the final predictive target margin of the established predictive models?

## Frozen Inputs
- **Explainer Class:** `shap.TreeExplainer`
- **Feature Perturbation Mode:** `tree_path_dependent`
- **Model Output Mode:** `raw` (additive expected value)
- **Library Version:** 0.51.0

## Contract Requirements
- The protocol evaluates raw additive SHAP values for each individual predictor in exactly the feature order in which the Random Forest trees were originally fit.
- The pipeline mathematically ensures strict additivity: `prediction ~= expected_value + sum(SHAP)`.
- During the RF-04A development testing protocol, the native SOURCE da_cdf target explicitly achieved near-perfect numerical reconstruction (`max_abs_error = 1.35e-15`).

## Correlated Predictor Caution
SHAP values represent a mathematical distribution of predictive variance along decision boundaries; they explicitly **do not** prove physical causality. Specifically, in highly correlated inputs (e.g. antecedent states vs lag states), the exact distribution of variance may lack singular causal interpretability. The pipeline primarily emphasizes grouped physical aggregations and model-agnostic consistency.

## Status
- **Status:** COMPLETE
- Configuration dynamically checked and loaded from `configs/xai/rf_xai.yaml`.
- Code module defined at `src/smap_xai/xai/shap_rf.py`.
