# Feature Group Contract

## Purpose
To document the deterministic grouping of fitted predictors into cohesive physical/scientific groups for the purpose of XAI visualization and importance attribution.

## Scientific Question
How does the Random Forest model attribute predictive skill among domain-specific physical processes across the different experiments?

## Frozen Inputs
Exactly 58 fitted unique predictors derived during the RF-03B modeling sequence across the entire target matrix.

## Feature Mapping
No features are orphaned. All 58 fitted predictors map strictly and unambiguously into exactly 1 of the following 9 proposed scientific groups.

### assimilation_diagnostics_or_history (13)
- `source_absolute_increment_pre3d_sum`
- `source_absolute_increment_pre7d_sum`
- `source_absolute_increment_t`
- `source_signed_increment_pre3d_sum`
- `source_signed_increment_pre7d_sum`
- `source_signed_increment_t`
- `finite_innovation_count_pre3d`
- `finite_innovation_count_pre7d`
- `finite_innovation_fraction_pre3d_mean`
- `finite_innovation_fraction_pre7d_mean`
- `finite_innovation_fraction_t`
- `days_since_finite_innovation_7d`
- `observation_frequency`

### antecedent_soil_moisture_state (4)
- `rzsm_lag1`
- `rzsm_opl_lag1`
- `ssm_lag1`
- `ssm_opl_lag1`

### meteorological_forcing (8)
- `precip_t`
- `precip_lag1`
- `precip_pre3d_sum`
- `precip_pre7d_sum`
- `tair_t`
- `tair_lag1`
- `tair_pre3d_mean`
- `tair_pre7d_mean`

### antecedent_land_surface_fluxes (3)
- `baseflow_opl_lag1`
- `et_opl_lag1`
- `surface_runoff_opl_lag1`

### soil_properties (7)
- `soil_texture_fraction_1`
- `soil_texture_fraction_12`
- `soil_texture_fraction_3`
- `soil_texture_fraction_4`
- `soil_texture_fraction_6`
- `soil_texture_fraction_7`
- `soil_texture_fraction_9`

### land_cover_or_vegetation (15)
- `land_cover_fraction_1`
- `land_cover_fraction_10`
- `land_cover_fraction_11`
- `land_cover_fraction_12`
- `land_cover_fraction_13`
- `land_cover_fraction_14`
- `land_cover_fraction_16`
- `land_cover_fraction_2`
- `land_cover_fraction_3`
- `land_cover_fraction_4`
- `land_cover_fraction_5`
- `land_cover_fraction_6`
- `land_cover_fraction_7`
- `land_cover_fraction_8`
- `land_cover_fraction_9`

### topography (1)
- `elevation`

### forcing_perturbation_controls (3)
- `delta_precip_forcing_t`
- `delta_precip_forcing_pre3d_sum`
- `delta_precip_forcing_pre7d_sum`

### temporal_context (4)
- `month`
- `day_of_year`
- `doy_cos`
- `doy_sin`

## Output Grouping Metrics
We explicitly compute absolute and normalized grouped importance from the global `mean(|SHAP|)` outputs for these exact mappings.

## Status
- **Status:** COMPLETE
- Configuration dynamically checked and loaded from `configs/xai/feature_groups.yaml`.
