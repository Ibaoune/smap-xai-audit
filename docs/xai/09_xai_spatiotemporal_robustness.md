# XAI Spatiotemporal Robustness

## Overview
This document synthesizes the robustness and stability of the Random Forest predictive attributions across the three development stages (SOURCE, TRANSFER, and VALUE) during the 2019 period.

*All results reflect development observations only. The 2020 validation year remains completely SEALED.*

## 1. SOURCE Stability
- **Seasonal**: Group rankings remain broadly consistent across DJF and JJA. In matched comparisons, the ranking structure is stable between `cdf` and `nocdf`.
- **Spatial**: Fold-to-fold variability remains low, with core antecedent and context features retaining their primary predictive status globally.
- **Sensitivity**: Matched vs. native-support models display robust consistency, proving that the attribution structure does not artifactually arise from sampling footprints.

## 2. TRANSFER Stability
- **Seasonal**: Differences are observed for targets such as `delta_surface_runoff`, reflecting the seasonal dependence of precipitation and baseflow forcing characteristics. `delta_rzsm` and `delta_et` show stable group attribution.
- **Spatial**: Runoff targets exhibit higher spatial variability, corresponding to topographic and meteorological boundaries, whereas soil moisture targets are relatively uniform across the 5 spatial folds.

## 3. VALUE Stability
- **Seasonal**: `land_cover_or_vegetation` represents the dominant predictive group in both DJF and JJA for the `da_cdf` model.
- **Spatial**: Predictive attributions show minimal spatial standard deviation across all 5 folds for key state groups like `assimilation_diagnostics_or_history` and `antecedent_land_surface_fluxes`.

## 4. SHAP vs. Permutation Consistency
Permutation importance strongly correlates with TreeSHAP feature rankings across all stages:
- **SOURCE**: Strong alignment (ρ > 0.8).
- **TRANSFER**: Consistent across all four target cascades (ρ typically > 0.8).
- **VALUE**: Strong rank agreement (`da_cdf` ρ = 0.752, `da_nocdf` ρ = 0.832).

## 5. CDF vs NoCDF Similarity
- **SOURCE**: Broadly concordant ranking structure, with different relative group attribution magnitudes.
- **TRANSFER**: Explanatory structure varies substantially by response target, especially for runoff.
- **VALUE**: CDF/NoCDF explanations remain related (predictor ρ = 0.851, group ρ = 0.667) but show lower group-level concordance than SOURCE.

## Development Synthesis
**DEVELOPMENT 2019 ONLY. NOT FINAL PAPER RESULT.**

While overall predictive skill and fundamental mechanics are robust across spatial domains, specific attribution magnitudes shift predictably with targets (especially from RZSM to Runoff) and season. The CDF/NoCDF difference modulates these attributions but does not overwrite the baseline predictive logic learned by the Random Forests.
