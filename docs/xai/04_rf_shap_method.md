# RF SHAP Methodology

## Purpose
To mathematically specify and freeze the SHAP implementation used to explain the frozen
Random Forest models during the 2019 development period.

## Scientific Question
How does the Random Forest model distribute predictive credit among inputs
to produce its specific predictions for `daily_absolute_increment`?

## Frozen Configuration

| Parameter | Value |
|---|---|
| Explainer class | `shap.TreeExplainer` |
| feature_perturbation | `tree_path_dependent` |
| model_output | `raw` |
| Library version | SHAP 0.51.0 |

## Cohort Sizes

| Level | Size | Purpose |
|---|---|---|
| Cohort index (parquet) | 50,000 rows | Stored balanced pixel-day universe |
| SHAP compute subset | **10,000 rows** | SHAP actually computed here |
| Permutation subset | 5,000 rows | Nested within 10k SHAP subset |

SHAP values are **not** computed for all 50,000 cohort-index rows.
The 10k compute subset is a deterministic balanced sub-sample (month × spatial_fold, seed 42)
sorted by date, y_index, x_index.

## Sample-Size Stability (RF-04B Closure Audit)

Representative model: SOURCE `da_cdf` matched support.

| Comparison | Predictor rank ρ | Top-10 overlap | Group ρ | Max group diff (norm.) |
|---|---|---|---|---|
| 5,000 vs 10,000 rows | **0.9989** | **10/10** | **1.0000** | 0.016 |

**Conclusion**: 10k rows produce rankings and group importances that are highly stable relative
to 5k. The 10k compute size is **frozen**. Do not change without a documented technical failure.

## Additivity Contract
For every model, the following is verified on the entire compute subset:

```
|prediction − (expected_value + Σ SHAP_i)| < 1e-4  (all rows)
```

RF-04B additivity results (all four SOURCE models):

| Model | max |error| | median |error| |
|---|---|---|
| da_cdf native | 1.78e-15 | 1.04e-16 |
| da_nocdf native | 1.18e-15 | 8.33e-17 |
| da_cdf matched | 2.16e-15 | 9.63e-17 |
| da_nocdf matched | 1.53e-15 | 6.77e-17 |

All errors are at machine-epsilon level, confirming perfect numerical additivity.

## Interpretation Constraints

- SHAP allocates the model's **predictive variance** among inputs.
- It does **not** quantify physical causality.
- In the presence of correlated predictors (e.g. lagged soil moisture states),
  importance may be distributed across correlated variables without implication
  of independent physical effects.
- Descriptive language only: "associated with", "predictive attribution",
  "model-attributed importance". Never "causes" or "controls".

## Status
**COMPLETE** — protocol frozen at RF-04B closure.
