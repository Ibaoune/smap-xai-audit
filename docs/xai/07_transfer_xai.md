# TRANSFER Development XAI (RF-04B) — COMPLETE

## Scientific Question
How does the DA-modified land trajectory propagate from the surface-soil-moisture assimilation
source into deeper soil moisture and land-surface flux responses?

Specifically: which environmental, antecedent land-state, and assimilation-context predictors
are **associated with** the RF-predicted DA-induced changes in RZSM, ET, surface runoff, and
baseflow on the identical finite-innovation pixel-days?

## Interpretation Boundary
All SHAP explanations describe the model's heuristic predictive attribution, not physical
causality.

Allowed:
> "Predictor group X contributes more to RF predictions of delta_ET than to delta_runoff."

Not allowed:
> "X physically causes propagation" or "CDF causes a stronger hydrological response."

Preferred terminology: *predictive attribution*, *explanatory structure*, *association*,
*model-attributed importance*, *response-specific explanatory pattern*.

## Models Explained — 8 Frozen RF_A Models

| # | Experiment | Target | Feature set | Active predictors |
|---|---|---|---|---|
| 1 | `da_cdf` | `delta_rzsm` | `source_context_feature_set` | 52 |
| 2 | `da_cdf` | `delta_et` | `source_context_feature_set` | 52 |
| 3 | `da_cdf` | `delta_surface_runoff` | `source_context_feature_set` | 52 |
| 4 | `da_cdf` | `delta_baseflow` | `source_context_feature_set` | 52 |
| 5 | `da_nocdf` | `delta_rzsm` | `source_context_feature_set` | 52 |
| 6 | `da_nocdf` | `delta_et` | `source_context_feature_set` | 52 |
| 7 | `da_nocdf` | `delta_surface_runoff` | `source_context_feature_set` | 52 |
| 8 | `da_nocdf` | `delta_baseflow` | `source_context_feature_set` | 52 |

**Feature count note**: The global XAI registry contains 58 unique predictors.
TRANSFER `source_context_feature_set` uses **52 active predictors**, a superset of the 35
SOURCE predictors. All 52 are correctly mapped to scientific groups.

## Common Cohort (Identical for All 8 Models)

| Level | Rows | Description |
|---|---|---|
| Cohort index (parquet) | 50,000 | `transfer_2019.parquet` — verified identical across all 8 |
| SHAP compute subset | 10,000 | Balanced month × spatial_fold sub-sample, seed 42 |
| Permutation subset | 5,000 | First 5k rows of 10k compute cohort |

**Cohort checksum (MD5, sorted date+y+x)**: `616d94379a06cbcefd1c32a3bc5acf6f`

RF-04A confirmed that the primary TRANSFER support is identical across all experiments and
targets — all 8 models use exactly the same pixel-day universe, enabling direct
target-to-target and CDF-vs-NoCDF comparisons without support boundary bias.

## TreeSHAP Configuration (Frozen)
`shap.TreeExplainer`, `feature_perturbation=tree_path_dependent`, `model_output=raw`

## Additivity QC

| Model | max \|error\| | median \|error\| |
|---|---|---|
| `da_cdf` `delta_rzsm` | 2.47e-15 | 8.54e-17 |
| `da_cdf` `delta_et` | 4.95e-14 | 1.23e-15 |
| `da_cdf` `delta_surface_runoff` | 2.33e-15 | 3.54e-18 |
| `da_cdf` `delta_baseflow` | 5.33e-15 | 4.24e-17 |
| `da_nocdf` `delta_rzsm` | 2.66e-15 | 1.70e-16 |
| `da_nocdf` `delta_et` | 4.77e-14 | 2.67e-15 |
| `da_nocdf` `delta_surface_runoff` | 7.77e-15 | 3.23e-17 |
| `da_nocdf` `delta_baseflow` | 4.93e-14 | 2.46e-16 |

All errors are at or near machine-epsilon level. ✅

## Group-Level Results — CDF (% normalized importance)

| Target | Antec. SM | Meteo. | Antec. LSM flux | Assimilation | Soil props. | Land cover | Topography | Temporal |
|---|---|---|---|---|---|---|---|---|
| ΔRZSM | 35.1 | 8.9 | 5.8 | **26.9** | 4.9 | 6.9 | 3.7 | 7.7 |
| ΔET | 16.0 | 9.0 | 14.5 | **29.7** | 16.5 | 3.7 | 1.7 | 8.9 |
| ΔRunoff | 1.6 | **22.3** | **35.9** | 7.4 | 1.8 | 12.2 | 6.5 | 5.0 |
| ΔBaseflow | 6.3 | 1.2 | **21.3** | **15.2** | 17.4 | 15.6 | 13.7 | 9.2 |

## Group-Level Results — NoCDF (% normalized importance)

| Target | Antec. SM | Meteo. | Antec. LSM flux | Assimilation | Soil props. | Land cover | Topography | Temporal |
|---|---|---|---|---|---|---|---|---|
| ΔRZSM | **40.1** | 3.0 | 10.8 | 10.0 | 9.8 | 13.9 | 5.8 | 6.5 |
| ΔET | 13.4 | 14.8 | **29.8** | 20.0 | 7.0 | 7.2 | 1.4 | 6.5 |
| ΔRunoff | 6.8 | **30.0** | 7.7 | 10.0 | 16.1 | **20.6** | 2.1 | 4.6 |
| ΔBaseflow | 11.3 | 2.9 | 13.9 | 14.8 | **23.3** | **23.5** | 4.0 | 6.2 |

## Cross-Target Predictor Rank Correlations

### CDF
| | ΔRZSM | ΔET | ΔRunoff | ΔBaseflow |
|---|---|---|---|---|
| **ΔRZSM** | 1.000 | 0.845 | 0.493 | 0.708 |
| **ΔET** | 0.845 | 1.000 | 0.579 | 0.521 |
| **ΔRunoff** | 0.493 | 0.579 | 1.000 | 0.457 |
| **ΔBaseflow** | 0.708 | 0.521 | 0.457 | 1.000 |

### NoCDF
| | ΔRZSM | ΔET | ΔRunoff | ΔBaseflow |
|---|---|---|---|---|
| **ΔRZSM** | 1.000 | 0.822 | 0.594 | 0.865 |
| **ΔET** | 0.822 | 1.000 | 0.631 | 0.722 |
| **ΔRunoff** | 0.594 | 0.631 | 1.000 | 0.678 |
| **ΔBaseflow** | 0.865 | 0.722 | 0.678 | 1.000 |

Surface runoff shows the most distinct explanatory structure (ρ ≤ 0.579 to all others in CDF).

## CDF-vs-NoCDF Comparison By Target (Identical Support)

| Target | Predictor rank ρ | top-5 | top-10 | Group ρ |
|---|---|---|---|---|
| ΔRZSM | 0.914 | 3/5 | 6/10 | 0.533 |
| ΔET | 0.896 | 3/5 | 6/10 | 0.700 |
| ΔRunoff | 0.664 | 2/5 | 3/10 | 0.350 |
| ΔBaseflow | 0.828 | 2/5 | 5/10 | 0.817 |

Surface runoff shows the most divergent CDF/NoCDF attribution pattern.
All results are descriptive — identical support ensures no coverage confounding.

## Permutation Importance vs SHAP Agreement

| Model | SHAP vs Perm ρ | top-5 | top-10 |
|---|---|---|---|
| `da_cdf` ΔRZSM | 0.160 | 3/5 | 7/10 |
| `da_cdf` ΔET | 0.710 | 4/5 | 8/10 |
| `da_cdf` ΔRunoff | 0.594 | 4/5 | 9/10 |
| `da_cdf` ΔBaseflow | 0.533 | 4/5 | 8/10 |
| `da_nocdf` ΔRZSM | 0.534 | 4/5 | 7/10 |
| `da_nocdf` ΔET | 0.910 | 3/5 | 8/10 |
| `da_nocdf` ΔRunoff | 0.785 | 3/5 | 8/10 |
| `da_nocdf` ΔBaseflow | 0.683 | 4/5 | 8/10 |

Note: `da_cdf` ΔRZSM shows low predictor-rank ρ (0.160) with reasonable top-10 overlap (7/10).
This reflects known permutation instability under strongly correlated lagged predictors,
which is especially pronounced for RZSM where soil-moisture state variables are dominant.

## Frozen Dependence-Plot Predictors (Top-3 Per Target)

| Target | Predictor 1 | Predictor 2 | Predictor 3 |
|---|---|---|---|
| ΔRZSM | `rzsm_opl_lag1` | `ssm_opl_lag1` | `baseflow_opl_lag1` |
| ΔET | `et_opl_lag1` | `ssm_opl_lag1` | `source_signed_increment_pre7d_sum` |
| ΔRunoff | `precip_t` | `land_cover_fraction_16` | `soil_texture_fraction_6` |
| ΔBaseflow | `baseflow_opl_lag1` | `land_cover_fraction_16` | `rzsm_opl_lag1` |

Selection rule: top-3 by `mean(mean_abs_shap_CDF, mean_abs_shap_NoCDF)` on identical support,
ties by feature name ascending. **Do not change.**


See `tidy_predictor_summary.csv` for per-model, per-predictor statistics:
`mean_abs_shap`, `mean_signed_shap`, `median_shap`, `positive/negative_shap_fraction`,
`rank_mean_abs_shap`, `feature_group`.

## Group-Level Results
See `tidy_group_summary.csv` and group importance matrices:
- `group_matrix_cdf.csv` — targets × groups, CDF
- `group_matrix_nocdf.csv` — targets × groups, NoCDF
- `group_matrix_diff.csv` — CDF minus NoCDF per group × target
- `cdf_nocdf_group_detail.csv` — per-target, per-group CDF/NoCDF/diff

## Target-to-Target Comparison
Pairwise Spearman rank correlation matrices at predictor and group level for CDF and NoCDF:
- `cross_target_pred_corr_cdf.csv` — 4×4 predictor-rank ρ
- `cross_target_pred_corr_nocdf.csv`
- `cross_target_group_corr_cdf.csv` — 4×4 group importance ρ
- `cross_target_group_corr_nocdf.csv`

## CDF-vs-NoCDF Comparison By Target
See `cdf_nocdf_comparison.csv` for per-target:
predictor rank ρ, top-5/top-10 overlap, group importance ρ.

Results reflect a **matched-support direct comparison** — both experiments use identical
pixel-days. Attribution differences are descriptive; do not attribute causally to CDF matching.

## Permutation Importance Robustness
5k-row permutation (neg_mean_absolute_error, 5 repeats, seed 42) compared with SHAP rankings.
Results in `tidy_predictor_summary.csv` (SHAP) and `permutation_*.json` files.

## Seasonal Analysis (DJF / JJA)
From the frozen 10k compute cohort (no resampling):
- `seasonal_djf_group_<exp>_<tgt>.csv` / `seasonal_jja_group_<exp>_<tgt>.csv`
- `seasonal_djf_predictor_<exp>_<tgt>.csv` / `seasonal_jja_predictor_<exp>_<tgt>.csv`

16 files total (2 experiments × 4 targets × 2 seasons).

## Spatial-Fold Stability
- `spatial_fold_group_<exp>_<tgt>.csv` — per-fold group importance
- `spatial_stability_<exp>_<tgt>.csv` — mean, std, min, max across 5 folds

8 stability summary files total.

## Frozen Dependence-Plot Predictors
Selection rule: top-3 by `mean(mean_abs_shap_CDF, mean_abs_shap_NoCDF)` on identical
support, ties by feature name ascending. Applied before inspecting plots.

See `dependence_features.json` for the frozen target-specific selections.

## Development Figures

| Figure | File | Content |
|---|---|---|
| TRANSFER-A | `fig_transfer_a_group_matrix.png` | Group importance matrix (targets × groups), CDF / NoCDF / diff |
| TRANSFER-B | `fig_transfer_b_top_predictors.png` | Top-10 predictor mean\|SHAP\| by target |
| TRANSFER-C | `fig_transfer_c_cross_target.png` | Predictor-rank ρ across targets |
| TRANSFER-D | `fig_transfer_d_distributions.png` | SHAP distributions top-6 by target |
| TRANSFER-E | `fig_transfer_e_dependence.png` | Dependence plots frozen top-3 per target |
| TRANSFER-F | `fig_transfer_f_seasonal.png` | DJF vs JJA group attribution |
| TRANSFER-G | `fig_transfer_g_spatial.png` | Spatial-fold stability |

All in `figures/development/transfer/` (git-ignored).

## Plotting Environment
matplotlib only — no seaborn dependency.

## Limitations
- SHAP explains the fitted RF predictions, not physical signal propagation.
- The assimilation-diagnostics feature group contains lagged DA-increment features;
  their importance does not imply that the DA mechanism caused the downstream response.
- Common support ensures that CDF/NoCDF target differences are not confounded by
  observation coverage, but differences remain descriptive.

## Status
**COMPLETE** — RF-04B TRANSFER development XAI closed.
