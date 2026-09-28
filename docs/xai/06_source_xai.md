# SOURCE Development XAI (RF-04B) — COMPLETE

## Scientific Question
Given a pixel-day with a valid native EnKF innovation diagnostic, which environmental,
antecedent land-state, and assimilation-context predictors are **associated with** the magnitude
of the daily surface-soil-moisture analysis increment (`daily_absolute_increment`)?

## Models Explained
Exactly four frozen RF_A models (context_only_feature_set):

| # | Experiment | Support | Active predictors |
|---|---|---|---|
| 1 | `da_cdf` | `native` | 35 |
| 2 | `da_nocdf` | `native` | 35 |
| 3 | `da_cdf` | `matched` | 35 |
| 4 | `da_nocdf` | `matched` | 35 |

**Note on feature counts**: The global XAI feature-group registry (`feature_groups.yaml`)
contains **58 unique predictors** spanning all model families. The SOURCE
`context_only_feature_set` uses a **35-predictor subset** of that registry.
All 35 SOURCE predictors are correctly mapped to their scientific groups;
groups whose features are absent from SOURCE have zero importance.

## Cohort Sizes

| Level | Rows | Description |
|---|---|---|
| Cohort index (parquet) | 50,000 | Balanced pixel-day universe (month × fold, seed 42) |
| SHAP compute subset | **10,000** | Deterministic balanced sub-sample nested within 50k |
| Permutation subset | 5,000 | First 5,000 rows of 10k SHAP compute cohort |

SHAP values are **not** computed for all 50,000 cohort-index rows.

## Sample-Size Stability (Frozen at RF-04B Closure)
Representative model: `da_cdf` matched support.

| Comparison | Predictor rank ρ | Top-10 overlap | Group ρ | Max group diff |
|---|---|---|---|---|
| 5k vs 10k | 0.9989 | 10/10 | 1.0000 | 0.016 |

**Decision**: 10k compute size is frozen. Stable relative to 5k.

## Additivity QC

| Model | max |SHAP| error | median error |
|---|---|---|
| `da_cdf` native | 1.78e-15 | 1.04e-16 |
| `da_nocdf` native | 1.18e-15 | 8.33e-17 |
| `da_cdf` matched | 2.16e-15 | 9.63e-17 |
| `da_nocdf` matched | 1.53e-15 | 6.77e-17 |

## Global Predictor Results (Matched CDF — top 10)

| Rank | Feature | Group | mean\|SHAP\| | mean signed |
|---|---|---|---|---|
| 1 | `ssm_lag1` | antecedent_soil_moisture_state | 0.00717 | −0.00107 |
| 2 | `precip_lag1` | meteorological_forcing | 0.00125 | −0.000035 |
| 3 | `rzsm_lag1` | antecedent_soil_moisture_state | 0.000922 | −0.000193 |
| 4 | `precip_pre7d_sum` | meteorological_forcing | 0.000837 | −0.000068 |
| 5 | `doy_sin` | temporal_context | 0.000719 | +0.000512 |
| 6 | `land_cover_fraction_16` | land_cover_or_vegetation | 0.000585 | +0.000083 |
| 7 | `precip_pre3d_sum` | meteorological_forcing | 0.000407 | +0.000004 |
| 8 | `doy_cos` | temporal_context | 0.000404 | +0.000126 |
| 9 | `day_of_year` | temporal_context | 0.000247 | +0.000098 |
| 10 | `soil_texture_fraction_1` | soil_properties | 0.000209 | +0.000182 |

## Grouped Results

### Matched CDF group importance
| Group | % |
|---|---|
| antecedent_soil_moisture_state | 58.7% |
| meteorological_forcing | 20.3% |
| temporal_context | 10.9% |
| land_cover_or_vegetation | 5.2% |
| soil_properties | 3.8% |
| topography | 1.1% |

### Matched NoCDF group importance
| Group | % |
|---|---|
| antecedent_soil_moisture_state | 38.7% |
| meteorological_forcing | 24.5% |
| soil_properties | 12.2% |
| temporal_context | 11.7% |
| land_cover_or_vegetation | 10.3% |
| topography | 2.6% |

## Matched-Support Direct Comparison (Interpretation)
The matched cohort (`source_matched_2019.parquet`) uses **identical pixel-days for both
CDF and NoCDF**. This is a **matched-support direct comparison**, not a native-support
characterization.

> On identical matched pixel-days, CDF and NoCDF show highly concordant predictor and group
> rankings (predictor rank ρ = 0.951, group ρ = 0.948), while the relative distribution of
> predictive attribution differs between some scientific groups.

The difference in group importances (notably antecedent SM state: CDF 58.7% vs NoCDF 38.7%)
reflects a difference in the model's heuristic predictive utilization on identical support.
**Do not attribute this difference causally** to the CDF assimilation mechanism.

## Native-Support Characterization (Interpretation Boundary)
Native CDF and NoCDF analyses each characterize their respective experiment on its own
native finite-innovation support. **These may not be directly compared as CDF vs NoCDF
attribution differences** because they operate on different pixel-day sets.

## Native vs Matched Sensitivity
| Experiment | Predictor rank ρ | Top-10 overlap | Group ρ |
|---|---|---|---|
| `da_cdf` | 0.998 | 10/10 | 1.000 |
| `da_nocdf` | 0.941 | 8/10 | 0.931 |

Rankings are highly stable across support boundaries.

## Permutation Importance Agreement
| Model | SHAP vs Perm ρ | top-5 | top-10 |
|---|---|---|---|
| `da_cdf` native | 0.808 | 3/5 | 9/10 |
| `da_nocdf` native | 0.884 | 4/5 | 8/10 |
| `da_cdf` matched | 0.826 | 3/5 | 8/10 |
| `da_nocdf` matched | 0.902 | 5/5 | 9/10 |

Strong to very strong agreement. Minor top-5 differences are consistent with
permutation instability under correlated predictors.

## DJF/JJA Seasonal Analysis
Seasonal group importance computed from the matched-support 10k cohort.
Results stored in `seasonal_djf_group_da_cdf.csv`, `seasonal_jja_group_da_cdf.csv`
(and NoCDF equivalents).

## Spatial-Fold Stability
Per-fold group importance computed across all 5 canonical spatial folds on
the matched-support 10k cohort. Stored in `spatial_fold_group_da_cdf.csv`.

## Frozen Dependence-Plot Predictors (Selection Rule)
Selection rule: mean(mean_abs_shap_CDF, mean_abs_shap_NoCDF) on matched support,
ties by feature name ascending. Applied **before** inspecting plots.

**Frozen top-4**: `ssm_lag1`, `precip_lag1`, `rzsm_lag1`, `land_cover_fraction_16`

## Development Figures
All stored in `figures/development/source/` (Git-ignored).

| Figure | File | Status |
|---|---|---|
| FIG SOURCE-A: Group importance CDF vs NoCDF | `fig_source_a_group_importance.png` | ✅ Generated |
| FIG SOURCE-B: Top-15 predictor comparison | `fig_source_b_top_predictors.png` | ✅ Generated |
| FIG SOURCE-C: SHAP distributions top-8 | `fig_source_c_beeswarm.png` | ✅ Generated |
| FIG SOURCE-D: Dependence plots frozen top-4 | `fig_source_d_dependence.png` | ✅ Generated |
| FIG SOURCE-E: DJF vs JJA group importance | `fig_source_e_seasonal.png` | ✅ Generated |
| FIG SOURCE-F: Spatial-fold stability | `fig_source_f_spatial.png` | ✅ Generated |

## Plotting Environment
Figures use **matplotlib only**. Seaborn was pip-installed ad-hoc during RF-04B
development and removed from the plotting code at RF-04B closure.
`environment.yml` does NOT include seaborn.

## Limitations
- SHAP explains the RF model's heuristic predictive attribution, not physical causation.
- Correlated predictors (e.g. lagged soil moisture, lagged precipitation) share
  importance in ways that do not isolate independent physical effects.
- Native CDF and NoCDF results operate on different pixel-day sets and must not
  be compared as direct attribution differences.

## Status
**COMPLETE** — RF-04B SOURCE development XAI closed.
