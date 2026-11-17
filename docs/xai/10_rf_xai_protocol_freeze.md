# Global Random Forest XAI Protocol Freeze

## Overview
This document serves as the absolute methodological freeze point prior to evaluating the SEALED 2020 validation year. All models, feature sets, target variables, parameters, cohorts, and interpretation guidelines listed below are immutable.

## 1. Immutable Model Definitions
- **SOURCE Stage**: `RF_A`
- **TRANSFER Stage**: `RF_A`
- **VALUE Stage**: `RF_B`

## 2. Immutable Feature Sets
- **SOURCE**: `context_only_feature_set`
- **TRANSFER**: `source_context_feature_set`
- **VALUE**: `value_context_feature_set`

## 3. Immutable Targets
- **SOURCE**: `daily_absolute_increment`
- **TRANSFER**: Four delta targets (`delta_rzsm`, `delta_et`, `delta_surface_runoff`, `delta_baseflow`)
- **VALUE**: `value_ae`

## 4. Immutable XAI Parameters
- **Representative cohort**: 50,000
- **SHAP compute subset**: 10,000
- **Permutation subset**: 5,000
- **Seed**: 42
- **Sampling method**: Month × spatial-fold balancing, target-independent sampling.
- **Explainer**: `shap.TreeExplainer`
- **Perturbation**: `tree_path_dependent`
- **Model output**: `raw`

## 5. Immutable Grouping
- **Checksum**: Exact checksum of `configs/xai/feature_groups.yaml` (to be verified by QC).

## 6. Immutable Figure Logic
- **Fig.5 / Fig.6 / Fig.7**: Exact panel definitions established during the development prototyping phase (Panels A through G as defined in `docs/xai/12_paper_figures.md`).

## 7. Immutable Dependence Rules
- **SOURCE**: Frozen top-4 predictors.
- **TRANSFER**: Frozen target-specific top-3 predictors.
- **VALUE**: Frozen top-4 predictors.

## 8. Immutable Spatiotemporal Splitting
- **Seasonal**: DJF (Dec-Jan-Feb) and JJA (Jun-Jul-Aug).
- **Spatial**: Canonical 5 folds.

## 9. Immutable Comparisons
- **SOURCE**: Matched footprint for direct CDF vs NoCDF comparison.
- **TRANSFER**: Common evaluation support across models.
- **VALUE**: Common evaluation support across models.

## 10. Immutable Interpretation Rules
- **SHAP Meaning**: SHAP represents **predictive attribution** within the Random Forest.
- **Causality**: No causal claims regarding physical mechanisms.
- **GLEAM**: GLEAM represents an **external evaluation reference**, not absolute ground truth.

## 11. Development Scientific Synthesis
**DEVELOPMENT 2019 ONLY. NOT FINAL PAPER RESULT.**

- **SOURCE**: Broadly concordant CDF/NoCDF ranking structure, with different relative group attribution.
- **TRANSFER**: Explanatory structure varies substantially by response target, especially runoff.
- **VALUE**: CDF/NoCDF explanations remain related but show lower group-level concordance than SOURCE.

*Note: No modeling or methodological tuning may be conducted based on this synthesis. The 2020 validation year remains SEALED.*
