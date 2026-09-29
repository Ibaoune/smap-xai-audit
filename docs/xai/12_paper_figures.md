# Final Manuscript Figure Registry

## Overview
This registry catalogs the finalized figures planned for the Random Forest modeling and XAI manuscript.

## Fig.1 Conceptual Framework
- **Scientific Question:** What is the overarching architecture and scientific purpose of the SMAP-XAI framework?
- **Planned Panels:** System diagram detailing SOURCE, TRANSFER, and VALUE experiments along with the CDF vs NoCDF assimilation flows.
- **Required Input Products:** Conceptual schematics (no empirical data).
- **Status:** PLANNED
- **Final-Output Filenames:** `fig1_conceptual_framework.png`, `fig1_conceptual_framework.pdf`

## Fig.2 Domain, Data, and Support
- **Scientific Question:** What are the physical and temporal scopes of the observational inputs, and how are the spatial canonical domains structured?
- **Planned Panels:** Map of Noah-MP and GLEAM domain overlap, station coordinates, spatial fold stratifications.
- **Required Input Products:** Canonical grid identifiers, spatial block mapping coordinates.
- **Status:** PLANNED
- **Final-Output Filenames:** `fig2_domain_support.png`, `fig2_domain_support.pdf`

## Fig.3 Assimilation Diagnostics
- **Scientific Question:** How does the raw EnKF assimilation update the base soil moisture states across the seasonal cycle before predictive modeling?
- **Planned Panels:** Seasonal means of increment size, innovation frequency, spatial increment distributions.
- **Required Input Products:** Canonical target distributions (`daily_absolute_increment`).
- **Status:** PLANNED
- **Final-Output Filenames:** `fig3_assimilation_diagnostics.png`, `fig3_assimilation_diagnostics.pdf`

## Fig.4 Predictive Robustness
- **Scientific Question:** To what degree of skill does the generalized Random Forest model reconstruct the core physical evaluation targets compared to the locked climatic baselines?
- **Planned Panels:** Skill improvements (MAE/RMSE) mapped out across the full primary matrix (SOURCE, TRANSFER, VALUE) with spatial/temporal uncertainty margins.
- **Required Input Products:** `rf03b_source_metrics.csv`, `rf03b_transfer_metrics.csv`, `rf03b_value_metrics.csv`.
- **Status:** PLANNED
- **Final-Output Filenames:** `fig4_predictive_robustness.png`, `fig4_predictive_robustness.pdf`

## Fig.5 SOURCE XAI
- **Scientific Question:** Which environmental, antecedent land-state, and assimilation-context
  predictors are associated with the predictive attribution of daily EnKF increments
  (`daily_absolute_increment`) across CDF and NoCDF configurations on identical pixel-days?
- **Interpretation note:** Results reflect a matched-support direct comparison (identical
  pixel-days for CDF and NoCDF). Do NOT write causal statements about assimilation.
- **Feature set:** `context_only_feature_set` — **35 active predictors** (subset of 58-predictor global registry)
- **SHAP compute subset:** 10,000 rows (frozen, stability-audited)
- **Required Input Products:** SOURCE 2019 XAI processed parquets and metadata summaries
- **Development Input Products:**
  - `matched_group_comparison.csv`
  - `tidy_predictor_summary.csv`
  - `dependence_features.json`
  - `seasonal_djf_group_da_cdf.csv`, `seasonal_jja_group_da_cdf.csv`
  - `spatial_fold_group_da_cdf.csv`
- **Current Panel Definitions:**
  - A. matched-support scientific-group importance: CDF vs NoCDF
  - B. top-15 predictor mean\|SHAP\| comparison (matched CDF vs NoCDF)
  - C. SHAP value distributions top-8 predictors (CDF and NoCDF side-by-side)
  - D. SHAP dependence plots — frozen top-4 predictors (CDF row / NoCDF row)
  - E. DJF vs JJA group importance (matched CDF)
  - F. Spatial-fold group importance stability (median ± IQR across 5 folds)
- **Plot Script:** `scripts/xai/05_plot_source_xai.py` (matplotlib only, no seaborn)
- **Status:** DEVELOPMENT PROTOTYPE
- **Development Filenames:**
  - `fig_source_a_group_importance.png` ✅
  - `fig_source_b_top_predictors.png` ✅
  - `fig_source_c_beeswarm.png` ✅
  - `fig_source_d_dependence.png` ✅
  - `fig_source_e_seasonal.png` ✅
  - `fig_source_f_spatial.png` ✅
- **Final-Output Filenames:** `fig5_source_xai.png`, `fig5_source_xai.pdf`

## Fig.6 TRANSFER XAI
- **Scientific Question:** How does the explanatory structure of RF predictions shift across the
  land-surface response chain (RZSM → ET → surface runoff → baseflow) under CDF and NoCDF?
- **Interpretation note:** Matched-support direct comparison (identical pixel-days for all 8 models).
  No causal attribution to assimilation. Wording must use *predictive attribution*/*association*.
- **Feature set:** `source_context_feature_set` — **52 active predictors** (subset of 58-predictor global registry)
- **SHAP compute subset:** 10,000 rows, common cohort (checksum: `616d94379a06cbcefd1c32a3bc5acf6f`)
- **Required Input Products:** TRANSFER 2019 XAI processed parquets and metadata summaries
- **Development Input Products:**
  - `group_matrix_cdf.csv`, `group_matrix_nocdf.csv`, `group_matrix_diff.csv`
  - `tidy_predictor_summary.csv`
  - `cross_target_pred_corr_cdf.csv`, `cross_target_group_corr_cdf.csv`
  - `cdf_nocdf_comparison.csv`, `cdf_nocdf_group_detail.csv`
  - `dependence_features.json` (top-3 per target, frozen)
- **Panel Definitions (DEVELOPMENT prototype):**
  - A. Group importance matrix (targets × groups): CDF panel + NoCDF panel
  - B. Top predictor mean|SHAP| by target (CDF + NoCDF)
  - C. Predictor-rank correlation across targets (4×4 heatmap)
  - D. SHAP distributions / top-predictor importance by target
  - E. Dependence plots — frozen top-3 predictors per target
  - F. DJF vs JJA group attribution by target
  - G. Spatial-fold group stability
- **Plot Script:** `scripts/xai/08_plot_transfer_xai.py` (matplotlib only)
- **Status:** DEVELOPMENT PROTOTYPE
- **Development Filenames:**
  - `fig_transfer_a_group_matrix.png` ✅
  - `fig_transfer_b_top_predictors.png` ✅
  - `fig_transfer_c_cross_target.png` ✅
  - `fig_transfer_d_distributions.png` ✅
  - `fig_transfer_e_dependence.png` ✅
  - `fig_transfer_f_seasonal.png` ✅
  - `fig_transfer_g_spatial.png` ✅
- **Final-Output Filenames:** `fig6_transfer_xai.png`, `fig6_transfer_xai.pdf`


## Fig.7 VALUE XAI
- **Scientific Question:** Under which environmental, land-state and assimilation-context
  conditions does the RF associate the DA trajectory with lower or higher absolute ET
  disagreement relative to GLEAM than OPL?
- **Interpretation notes:**
  - GLEAM is an external evaluation reference, NOT ground truth.
  - SHAP > 0 pushes predicted `value_ae` upward (lower abs. ET disagreement relative to OPL).
  - All results are predictive attribution, not causal statements about ET improvement.
  - CDF/NoCDF comparison on identical pixel-day support.
- **Target:** `value_ae = |ET_OPL − ET_GLEAM| − |ET_DA − ET_GLEAM|`
- **Feature set:** `value_context_feature_set` — **52 active predictors** (GLEAM-native grid)
- **SHAP compute subset:** 10,000 rows, common cohort (checksum: `fb68bb1122ffa6ee11490c122b239c7f`)
- **Required Input Products:** VALUE 2019 XAI processed parquets and metadata summaries
- **Development Input Products:**
  - `target_distribution.csv` — value_ae stats, CDF + NoCDF
  - `tidy_predictor_summary.csv`
  - `tidy_group_summary.csv`
  - `cdf_nocdf_comparison.csv`, `cdf_nocdf_group_detail.csv`
  - `dependence_features.json` (top-4 frozen)
  - `sign_split_summary.csv` (optional supplement)
- **Panel Definitions (DEVELOPMENT prototype):**
  - A. value_ae target distribution, CDF vs NoCDF
  - B. Scientific-group normalized importance, CDF vs NoCDF
  - C. Top-12 predictor mean|SHAP|, CDF vs NoCDF
  - D. SHAP value distributions, top-8 predictors (CDF)
  - E. Dependence plots — frozen top-4 predictors (CDF row / NoCDF row)
  - F. DJF vs JJA group attribution
  - G. Spatial-fold group stability (median ± IQR)
- **Plot Script:** `scripts/xai/11_plot_value_xai.py` (matplotlib only)
- **Status:** DEVELOPMENT PROTOTYPE
- **Development Filenames:**
  - `fig_value_a_distribution.png` ✅
  - `fig_value_b_group_importance.png` ✅
  - `fig_value_c_top_predictors.png` ✅
  - `fig_value_d_shap_distributions.png` ✅
  - `fig_value_e_dependence.png` ✅
  - `fig_value_f_seasonal.png` ✅
  - `fig_value_g_spatial.png` ✅
- **Final-Output Filenames:** `fig7_value_xai.png`, `fig7_value_xai.pdf`

## Fig.8 Optional Spatial Synthesis
- **Scientific Question:** Do the predictive heuristics demonstrate regional instability or physical clustering when evaluated over distinct climatic folds?
- **Planned Panels:** Map grids highlighting regional group-importance shifts or robust consensus predictors.
- **Required Input Products:** Aggregated metrics grouped by `spatial_fold`.
- **Status:** PLANNED
- **Final-Output Filenames:** `fig8_spatial_synthesis.png`, `fig8_spatial_synthesis.pdf`
