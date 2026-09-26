# SMAP-XAI Transfer Target Audit

## Scope
This document provides a cross-target audit of the complete XAI Transfer block (`delta_rzsm`, `delta_et`, `delta_surface_runoff`, `delta_baseflow`). The purpose is to evaluate the support identity, numerical characteristics, cross-target associations, and temporal persistence of the DA-minus-OPL responses without attempting to merge variables of differing physical units.

## Canonical Transfer Targets
1. **`delta_rzsm`**: state response (m³ m⁻³) - daily 24-h-mean DA-minus-OPL 0-100 cm RZSM difference.
2. **`delta_et`**: flux response (mm/day) - Evap_tavg * 86400.
3. **`delta_surface_runoff`**: flux response (mm/day) - Qs_tavg * 86400.
4. **`delta_baseflow`**: flux response (mm/day) - Qsb_tavg * 86400.

## Support Identity
All four targets share exactly the same finite daily valid-model support.
*   **Time count**: 1827 days
*   **Valid pixel count**: 16,030 pixels
*   **Finite pixel-days**: 29,286,810 per experiment
*   **Missing valid-land count**: 0
*   **Coordinate mismatch counts**: 0

## Distribution / Scale Comparison
The four targets have distinct units, variances, and zero-structures. Flux targets (ET, runoff, baseflow) have exact zero and near-zero structures that vary considerably by component, while `delta_rzsm` represents a continuous state response. Raw magnitudes are not combined across RZSM and flux targets.

## CDF-vs-NoCDF Support Structure
Assimilation support overlap differs strictly between DA-CDF and DA-NoCDF. Based on exactly aligned daily `observation_frequency == 1` masking:
*   A. Neither assimilates (~CDF & ~NoCDF): 74.32% (21,764,715)
*   B. Both assimilate (CDF & NoCDF): 8.34% (2,441,779)
*   C. CDF-only (CDF & ~NoCDF): 0.05% (14,454)
*   D. NoCDF-only (~CDF & NoCDF): 17.30% (5,065,862)

## Assimilation-Support Dependence
Target distributions differ between same-day assimilation and no-assimilation support. For example, `delta_rzsm` median absolute responses are higher on days when both experiments assimilate (~0.013–0.015) than on days when neither assimilates (~0.004–0.012).

## Cross-Target Associations
Correlations (Pearson, Spearman) among targets characterize descriptive associations.
*   Associations compare responses descriptively; they must not be interpreted as direct partition causality.
*   Associations remain moderate to weak in most pairs, reflecting distinct physical processes. 

## Temporal Persistence
Aggregated temporal persistence is higher for `delta_rzsm` and `delta_baseflow`, intermediate for `delta_et`, and lower for `delta_surface_runoff` under the common daily-spatial autocorrelation diagnostic.
These autocorrelations are descriptive properties of spatially aggregated target series and are not physical response timescales.
Lag-1 through lag-7 autocorrelation (using daily spatial means) indicates:
*   `delta_rzsm` and `delta_baseflow` possess high temporal persistence (lag-1 > 0.99).
*   `delta_surface_runoff` decays rapidly (lag-1 ~ 0.40–0.48).
*   `delta_et` persistence is intermediate (lag-1 ~ 0.93–0.97).

## Seasonal Structure
All targets demonstrate year-round responses. Seasonal magnitude differences exist (e.g., DA-CDF `delta_surface_runoff` mean absolute is higher in MAM and DJF than in JJA) but no artificial zero-support adjustments are required.

## 2019 SMAP Outage
During the 2019 SMAP observation outage (19 June - 23 July), DA-minus-OPL differences remain present during the documented period with zero assimilated SMAP observations. For instance, `delta_rzsm` maintains an absolute median of ~0.008 (CDF) and ~0.012 (NoCDF) despite the lack of instantaneous updates, reflecting persistent system memory.

## Row-Wise Numerical Structure
The even/odd row contrast is a descriptive parity diagnostic and should not by itself be interpreted as evidence for or against the previously diagnosed implementation-dependent row-wise pattern.
*   `delta_et`, `delta_surface_runoff`, and `delta_baseflow` have row-dependent numerical structure already established from the raw DA flux diagnostics and documented in docs/preprocessing/model_diagnostics.md.
*   The previous target-specific spatial QC did not show an obvious rigid row-wise pattern dominating the long-term `delta_rzsm` maps. The unified even/odd parity diagnostic is reported descriptively and is not used as an artifact classifier.

## Extreme-Response Concentration
Large absolute responses (top 1% and 5%) are heavily concentrated in specific temporal events and geographic pixels.
*   For `delta_surface_runoff` (DA-CDF), the top 10 large-response dates account for ~11.97% of the total absolute response.
*   For `delta_baseflow` (DA-NoCDF), the top 1% of valid pixels account for ~27.77% of the total absolute response.

## Timing / Leakage Considerations

| Variable | Role | Temporal Semantics | Available when obs_freq=0? | Pre/Post-analysis / Static | Leakage/Timing Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `elevation` | static predictor | static | yes | static | static/context safe |
| `soil_texture_fraction` | static predictor | static | yes | static | static/context safe |
| `land_cover_fraction` | static predictor | static | yes | static | static/context safe |
| `precipitation` | forcing | daily mean | yes | pre-analysis candidate | pre-analysis candidate |
| `tair` | forcing | daily mean | yes | pre-analysis candidate | pre-analysis candidate |
| `ssm` | background | daily mean | yes | model-output | timing requires explicit lag definition |
| `rzsm` | background | daily mean | yes | model-output | timing requires explicit lag definition |
| `observation_frequency`| diagnostic | daily event flag | yes | pre-analysis candidate | pre-analysis candidate |
| `innovation` | DA diagnostic | event time | no | pre-analysis candidate | pre-analysis candidate |
| `normalized_innovation`| DA diagnostic | event time | no | pre-analysis candidate | pre-analysis candidate |
| `forecast_variance` | DA diagnostic | event time | no | pre-analysis candidate | pre-analysis candidate |
| `daily_signed_increment`| DA diagnostic | daily sum | no | post-analysis | post-analysis leakage risk |
| `daily_absolute_increment`| DA diagnostic| daily sum | no | post-analysis | post-analysis leakage risk |
| `analysis_residual` | DA diagnostic | event time | no | post-analysis | post-analysis leakage risk |
| `delta_rzsm` | target | daily mean | yes | model-output | target/response |
| `delta_et` | target | daily mean | yes | model-output | target/response |
| `delta_surface_runoff` | target | daily mean | yes | model-output | target/response |
| `delta_baseflow` | target | daily mean | yes | model-output | target/response |

## Implications for Final Modeling Dataset Design
The four targets have strongly different units, variance, zero structure, tail behavior, and temporal persistence. Therefore final model design must NOT automatically:
1. Use one shared target scaling.
2. Compare RMSE numerically across targets.
3. Pool targets into one loss without normalization/design.

The final modeling dataset requires an explicit decision between building models over *all valid pixel-days* versus *assimilation-conditional samples*. For daily aggregated forecasting, explicit lag definition is critical to prevent data leakage from post-analysis features into the prediction of daily-mean responses.
