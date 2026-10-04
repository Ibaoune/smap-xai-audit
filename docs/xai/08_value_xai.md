# VALUE Development XAI (RF-04B) — COMPLETE

## Scientific Question

Under which environmental, land-state and assimilation-context conditions does the RF associate
the DA trajectory with lower or higher absolute ET disagreement relative to GLEAM than OPL?

Specifically: which predictors are associated with the magnitude and sign of `value_ae` across
pixel-days in the 2019 development period?

## Target Definition

```
value_ae = |ET_OPL − ET_GLEAM| − |ET_DA − ET_GLEAM|
```

- `value_ae > 0`: DA has **lower** absolute ET disagreement with GLEAM than OPL
  → RF predicts DA is relatively closer to the GLEAM reference on this pixel-day
- `value_ae < 0`: DA has **higher** absolute ET disagreement with GLEAM than OPL
  → RF predicts DA is relatively further from the GLEAM reference on this pixel-day

## GLEAM-as-Reference Caveat

GLEAM is used as an **external evaluation reference**, not as ground truth.
All statements about `value_ae` are conditional on GLEAM as the reference product.
SHAP explains the fitted RF prediction of `value_ae`, not physical ET truth.

## Interpretation Boundary

All SHAP explanations describe **predictive attribution within the RF**, not physical causality.

**SHAP sign convention for value_ae:**
- Positive SHAP contribution: pushes the RF prediction toward **higher value_ae**
  (associated with lower absolute DA-vs-GLEAM disagreement relative to OPL)
- Negative SHAP contribution: pushes the RF prediction toward **lower value_ae**
  (associated with smaller improvement or larger relative disagreement)

Allowed:
> "Feature X has high predictive attribution for value_ae."
> "High values of predictor Y are associated, within the RF, with positive contributions
>  to predicted value_ae."

Not allowed:
> "Feature X improves ET." / "DA is more accurate because feature X." /
> "GLEAM confirms truth." / "SHAP identifies the physical cause of improved ET."

## Models Explained — 2 Frozen RF_B Models

| # | Experiment | Target | Feature set | Active predictors |
|---|---|---|---|---|
| 1 | `da_cdf` | `value_ae` | `value_context_feature_set` | 52 |
| 2 | `da_nocdf` | `value_ae` | `value_context_feature_set` | 52 |

**RF_B configuration** (read from model artifacts, not assumed):
- `n_estimators=300`, `max_depth=16`, `min_samples_leaf=5`
- `max_features=0.7`, `bootstrap=True`, `random_state=42`

**Training period**: 2016-01-08 → 2018-12-31
**Development XAI period**: 2019 only — **2020 SEALED**

## Common VALUE Cohort

| Level | Rows | Description |
|---|---|---|
| Representative cohort (parquet) | 50,000 | `value_2019.parquet` — verified identical for both models |
| SHAP compute subset | 10,000 | Balanced month × spatial_fold sub-sample, seed 42 |
| Permutation subset | 5,000 | First 5k rows of 10k compute cohort |

**Canonical grid identifiers**: `gleam_y_index`, `gleam_x_index`
(GLEAM-native grid — **not** Noah-MP native grid)

**Cohort checksum (MD5, sorted date + gleam_y + gleam_x)**:
`fb68bb1122ffa6ee11490c122b239c7f`

## Active Feature Contract

**52 active predictors** — `value_context_feature_set`.
All 52 are mapped in `configs/xai/feature_groups.yaml`. Feature sets are identical for CDF and NoCDF.

### Forbidden Predictor Audit
The following are verified **absent** from the fitted feature set:
- `GLEAM_ET(t)` or any same-day GLEAM variable
- `ET_OPL(t)`, `ET_DA(t)` — same-day DA/OPL ET
- `value_ae(t)` or any lagged `value_ae`
- Same-day TRANSFER delta variables

**Result**: No forbidden predictor found. ✅

## TreeSHAP Configuration (Frozen)
`shap.TreeExplainer`, `feature_perturbation=tree_path_dependent`, `model_output=raw`

## Additivity QC

| Model | max \|error\| | median \|error\| |
|---|---|---|
| CDF | 6.01e-14 | 1.72e-15 |
| NoCDF | 6.23e-14 | 2.11e-15 |

## 2019 value_ae Target Distribution

The manuscript descriptive statistics for `value_ae` must use the **full 2019 validation distribution** (N=1,500,150) to ensure representative physical properties, rather than the subsetted XAI cohorts.

### 1. Full 2019 Validation Distribution (Manuscript Reference)

| Statistic | CDF | NoCDF |
|---|---|---|
| N | 1,500,150 | 1,500,150 |
| Mean | -0.0113 | 0.0163 |
| Median | -0.0245 | -0.0047 |
| Std Dev | 0.2216 | 0.2854 |
| P05 | -0.3275 | -0.3997 |
| P95 | 0.3416 | 0.4953 |
| Fraction > 0 | 42.05% | 48.98% |
| Fraction < 0 | 57.95% | 51.02% |
| Fraction == 0 | 0.00% | 0.00% |

### 2. 50,000-row XAI Cohort (Representative Sample)
*Used as the background cohort for sampling.*
- **CDF**: Mean=-0.0103, Median=-0.0238, Std=0.2187, P05=-0.3218, P95=0.3419
- **NoCDF**: Mean=0.0161, Median=-0.0036, Std=0.2845, P05=-0.3970, P95=0.4901

### 3. 10,000-row TreeSHAP Subset
*Used explicitly for computing TreeSHAP explanations.*
- **CDF**: Mean=-0.0093, Median=-0.0231, Std=0.2229, P05=-0.3274, P95=0.3513
- **NoCDF**: Mean=0.0125, Median=-0.0045, Std=0.2869, P05=-0.4084, P95=0.4922

### 4. 5,000-row Permutation Subset
*Used for permutation feature importance.*

## Predictor-Level Results

See `tidy_predictor_summary.csv` for per-model, per-predictor statistics:
`mean_abs_shap`, `mean_signed_shap`, `median_shap`, `positive/negative_shap_fraction`,
`rank_mean_abs_shap`, `feature_group`.

## Group-Level Results

All nine groups shown. Sums verified to equal 1.000 for both models.

See `tidy_group_summary.csv` and:
- `cdf_nocdf_group_detail.csv` — per-group CDF/NoCDF/diff table

## CDF-vs-NoCDF Comparison

Both VALUE models use identical pixel-day support. Attribution differences are descriptive;
they are not causally attributed to CDF matching.

See `cdf_nocdf_comparison.csv` for predictor rank ρ, top-5/top-10 overlap, and group ρ.

## Permutation Importance Robustness

5k-row permutation (neg_mean_absolute_error, 5 repeats, seed 42).
Where SHAP-vs-permutation rank ρ is low, the discrepancy is compatible with known sensitivity
to correlated predictors, but its origin is not established here.

## Seasonal Analysis (DJF / JJA)

From the frozen 10k compute cohort (no resampling):
- `seasonal_djf_group_<exp>.csv` / `seasonal_jja_group_<exp>.csv`
- `seasonal_djf_predictor_<exp>.csv` / `seasonal_jja_predictor_<exp>.csv`
- `seasonal_target_<exp>.csv` — value_ae distribution by season

DJF and JJA are not labelled wet/dry without evidence.

## Spatial-Fold Stability

- `spatial_fold_group_<exp>.csv` — per-fold group importance (folds 0–4)
- `spatial_stability_<exp>.csv` — mean, std, min, max across 5 folds

## Sign-Based Descriptive Summary

Using the **same frozen SHAP cohort** (not a new cohort), rows where `value_ae > 0`
and `value_ae < 0` are described separately in `sign_split_summary.csv`.

This is **descriptive only** — it is not a model split, not classification,
and not used for predictor or model selection.

## Frozen Dependence-Plot Predictors (Top-4)

Selection rule: top-4 by `mean(mean_abs_shap_CDF, mean_abs_shap_NoCDF)` on identical support,
ties by feature name ascending. **Frozen — do not change.**

See `dependence_features.json`.

## Development Figures

| Figure | File | Content |
|---|---|---|
| VALUE-A | `fig_value_a_distribution.png` | value_ae target distribution, CDF vs NoCDF |
| VALUE-B | `fig_value_b_group_importance.png` | Scientific-group importance, CDF vs NoCDF |
| VALUE-C | `fig_value_c_top_predictors.png` | Top-12 predictor mean\|SHAP\|, CDF vs NoCDF |
| VALUE-D | `fig_value_d_shap_distributions.png` | SHAP distributions, top-8 predictors (CDF) |
| VALUE-E | `fig_value_e_dependence.png` | Dependence plots, frozen top-4 predictors |
| VALUE-F | `fig_value_f_seasonal.png` | DJF vs JJA group attribution |
| VALUE-G | `fig_value_g_spatial.png` | Spatial-fold stability (median ± IQR) |

All in `figures/development/value/` (git-ignored). Plotting script: `scripts/xai/11_plot_value_xai.py`
(matplotlib only — no seaborn).

## Limitations

- SHAP explains the fitted RF prediction of `value_ae`, not physical ET improvement.
- GLEAM is an external reference product with its own biases and coverage limitations.
  Statements about `value_ae` are conditional on GLEAM as the reference.
- The `value_context_feature_set` excludes same-day ET and GLEAM variables by design;
  attribution reflects ante cedent and contextual predictors only.
- Common support ensures CDF/NoCDF comparison is not confounded by coverage differences,
  but differences remain descriptive.
- Sign-based descriptive summaries (§positive/negative value_ae) are post-hoc groupings
  of the frozen SHAP cohort; they are not used for model or predictor selection.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/xai/09_run_value_xai.py` | SHAP + permutation computation (one experiment per call) |
| `scripts/xai/10_summarize_value_xai.py` | Summaries, comparisons, seasonal, spatial, sign split |
| `scripts/xai/11_plot_value_xai.py` | Development figures (matplotlib only) |
| `scripts/qc/xai/04_audit_value_xai.py` | 14-point closure audit |

## Status
**COMPLETE** — RF-04B VALUE development XAI closed.
