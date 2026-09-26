# Modeling Dataset Contract

**Author:** M. El Aabaribaoune

This document formally specifies the canonical machine learning datasets constructed for Explainable AI (XAI) analysis in the SMAP-XAI project.

## Block 1 — SOURCE

### Scientific question
Given a pixel-day with a valid native EnKF innovation diagnostic for this experiment, what controls the magnitude of the corresponding daily SSM increment?

### Sample unit
The SOURCE table is DAILY.
One sample is: pixel × calendar day.

### Canonical Support Rule (`observation_frequency`)
Canonical SOURCE training population strictly retains only rows where `observation_frequency == 1` and `innovation` is finite.

**Exact Definition:**
- `observation_frequency == 1` means: the corresponding daily pixel contains a finite native EnKF innovation diagnostic for that experiment.
- `observation_frequency == 0` means: no finite native EnKF innovation diagnostic was mapped to that pixel-day.

`observation_frequency` is DERIVED by this project from native EnKF diagnostics. It is not a raw SMAP availability flag, not a native LIS variable named `observation_frequency`, and not proof by itself that a non-zero analysis increment occurred.

**Why it is used for sample selection:**
In the derived daily increment products, pixel-days without a finite innovation diagnostic have `daily_absolute_increment = 0` by construction. Including the full daily domain would therefore make the SOURCE regression largely reflect the presence/absence of an assimilation diagnostic rather than the magnitude of the correction when such a diagnostic exists. The scientific question is conditional: Given a pixel-day with a valid native EnKF innovation diagnostic for this experiment, what controls the magnitude of the corresponding daily SSM increment?

### Target
**Primary:** `daily_absolute_increment` (m3 m-3). Represents the magnitude of the L1 soil-moisture analysis increment.
**Secondary Diagnostic:** `daily_signed_increment`.

### Experiment separation
Built and stored independently for `DA-CDF` and `DA-NoCDF`. Experiment identity is provided as metadata, and experiments are NOT concatenated into a single model.

### Predictor groups
1. **TARGET**: `daily_absolute_increment`
2. **SECONDARY_TARGET_DIAGNOSTIC**: `daily_signed_increment`
3. **ENKF_MECHANISTIC_PRIMARY**: `innovation`, `forecast_variance`
4. **ENKF_MECHANISTIC_ALTERNATIVE**: `normalized_innovation` (`normalized_innovation` is a redundant alternative representation because it is deterministically derived from innovation, forecast variance, and observation-error information. It is pre-analysis information and is NOT target leakage.)
5. **ANTECEDENT_STATE**: `ssm_lag1`, `rzsm_lag1` (Lagged state variables)
6. **ANTECEDENT_METEOROLOGY**: `precip_lag1`, `precip_pre3d_sum`, `precip_pre7d_sum`, `tair_lag1`, `tair_pre3d_mean`, `tair_pre7d_mean`
7. **STATIC**: `elevation`, 16 `soil_texture_fraction_*`, 20 `land_cover_fraction_*`
8. **TEMPORAL_CONTEXT**: `month`, `day_of_year`, `doy_sin`, `doy_cos` (Native EnKF event hour exists in the native-event products but is not currently propagated into the canonical daily SOURCE products; it is therefore omitted from the current canonical dataset rather than inferred.)
9. **METADATA_NOT_PRIMARY_FEATURES**: `date`, `year`, `lat`, `lon`, `y_index`, `x_index`, `experiment`, `observation_frequency`

### Timing rules
Assimilation events occur within the UTC day. Therefore, NO same-day DA daily state or flux variables are used as SOURCE predictors, as they may contain the post-analysis trajectory. All state/forcing context uses strict lagged (antecedent) values derived prior to the event (day $t-1$ or earlier). LIS HIST daily products use the validated daily convention without shifting.

### Leakage exclusions
The following variables are strictly forbidden to prevent data leakage:
- `daily_absolute_increment` and `daily_signed_increment` (`daily_signed_increment` is a secondary diagnostic and forbidden as a predictor when target is `daily_absolute_increment`)
- `analysis_residual`
- Any post-analysis diagnostics or derived variables.
- Block 2 Transfer targets (`delta_rzsm`, `delta_et`, `delta_surface_runoff`, `delta_baseflow`)
- Block 3 Value target (`value_ae`, GLEAM ET)
- Same-day DA soil-moisture states.

### Spatial support
Canonical Noah-MP valid-land grid over the North-Morocco domain.

### Temporal support
Calendar years 2016 through 2020. 2016-01-01 (and a few days following) may be excluded from analysis rows due to insufficient lag history (up to 7 days).

### Dataset schema
Defined strictly by the columns implemented in `scripts/datasets/01_build_source_dataset.py`.

### Storage format
Partitioned Parquet (`year=YYYY`) format.

### QC requirements
A robust QC suite runs via `scripts/qc/datasets/01_audit_source_dataset.py` to ensure duplicate freedom, structural closure, support constraint (`observation_frequency == 1`), zero/near-zero variance tracking, and missingness accountability.

### Optional Future Occurrence Question
A separate future question could study the probability/availability of an assimilation update using the full daily support. That would be a different classification/support problem and is NOT part of the current SOURCE magnitude model. Do not build that dataset now.

### Open Methodological Note
The substantially different finite-innovation support between DA-CDF and DA-NoCDF is documented but its exact upstream cause (observation preprocessing, QC, CDF-matching availability, or another experiment-specific condition) has not yet been isolated. It must not be attributed to CDF matching without a dedicated support audit.

### Matched-Support Modeling Implication
Primary SOURCE modeling uses experiment-specific conditional samples (each experiment uses its own finite-innovation support). However, any DIRECT CDF-vs-NoCDF model or XAI comparison should include a matched-support sensitivity analysis restricted to `BOTH` (shared pixel-days where both branches successfully generated a finite innovation). Otherwise, differences in model behavior or XAI attributions may reflect the different sampled locations/times rather than strictly the differences between the assimilation algorithms. This matched subset can be obtained dynamically by inner-joining `date` + `y_index` + `x_index` between the two canonical SOURCE tables.

## Block 2 — TRANSFER

### Scientific question
How does the DA-modified land trajectory propagate from the surface-soil-moisture assimilation source into deeper soil moisture and land-surface flux responses?

### Sample unit
One valid-land canonical Noah-MP pixel × one calendar day × one DA experiment. The support is the complete daily land support (16,030 valid-land pixels), without filtering to `observation_frequency == 1`, because Transfer responses persist between finite-innovation events.

### Target
Canonical signed Transfer targets: `delta_rzsm`, `delta_et`, `delta_surface_runoff`, `delta_baseflow` (where delta is `DA - OPL`). These are model-response targets, not errors or observational skill metrics.

### Experiment separation
Built and stored independently for `DA-CDF` and `DA-NoCDF`. ONE Transfer table per experiment containing all four targets. Experiments are NOT concatenated into a single model.

### Predictor groups
- **assimilation_source_current**: `source_signed_increment_t`, `observation_frequency`
- **assimilation_source_current_alternative**: `source_absolute_increment_t`
- **assimilation_source_history**: `source_signed_increment_pre3d_sum`, `source_signed_increment_pre7d_sum`, `source_absolute_increment_pre3d_sum`, `source_absolute_increment_pre7d_sum`, `finite_innovation_count_pre3d`, `finite_innovation_count_pre7d`, `days_since_finite_innovation_7d`
- **environmental_context**: `precip_t`, `tair_t`, `precip_lag1`, `precip_pre3d_sum`, `precip_pre7d_sum`, `tair_lag1`, `tair_pre3d_mean`, `tair_pre7d_mean`, `ssm_opl_lag1`, `rzsm_opl_lag1`, `et_opl_lag1`, `surface_runoff_opl_lag1`, `baseflow_opl_lag1`
- **forcing_perturbation_control**: `delta_precip_forcing_t`, `delta_precip_forcing_pre3d_sum`, `delta_precip_forcing_pre7d_sum` (Note: `delta_tair_forcing_t` is excluded as DA-minus-OPL air temperature differences are ~1e-5 K arithmetic noise. Precipitation differences are non-zero and require control.)
- **trajectory_memory**: `delta_ssm_lag1`, `delta_rzsm_lag1`, `delta_et_lag1`, `delta_surface_runoff_lag1`, `delta_baseflow_lag1`
- **static**: `elevation`, 16 `soil_texture_fraction_*`, 20 `land_cover_fraction_*`
- **temporal_context**: `month`, `day_of_year`, `doy_sin`, `doy_cos`
- **metadata**: `date`, `year`, `lat`, `lon`, `y_index`, `x_index`, `experiment`

### Leakage exclusions
The following variables are strictly forbidden to prevent data leakage:
- Same-day Transfer targets (except the specific selected target for modeling)
- Same-day DA/OPL RZSM, ET, surface runoff, baseflow
- `value_ae`, `GLEAM ET`, `analysis_residual`

### Raw HIST Temporal Convention
The canonical Noah-MP daily date convention uses `canonical_date = LIS_HIST timestamp - 1 day` because HIST `_tavg` files are END-of-period labeled. For example, canonical date `2018-05-10` maps strictly to `LIS_HIST_201805110000.d01.nc`.

### Meteorological timing
Unlike SOURCE, same-day meteorological forcing (`precip_t`, `tair_t`) is allowed because TRANSFER is an explanatory contemporaneous daily-response problem, not a day-ahead forecast problem.

### Modeling Modes
- **source_context_feature_set**: Primary forcing-controlled feature mode. Predicts Transfer response given current/recent assimilation source, environmental context, and forcing perturbation controls. Excludes trajectory-memory features.
- **source_context_without_forcing_control**: Sensitivity mode identical to `source_context_feature_set` but excluding the 3 `forcing_perturbation_control` variables. Allows quantifying if conclusions are robust to explicit control of DA forcing perturbations.
- **memory_augmented_feature_set**: Extends `source_context_feature_set` with allowed target-specific lagged Transfer memory (e.g., `delta_ssm_lag1` and `delta_rzsm_lag1` for `delta_rzsm` target).

### Forcing-Control Interpretation
The forcing-perturbation variables are nuisance controls included to separate experiment-specific meteorological forcing differences from the SSM-assimilation source signal. They must not be interpreted as part of the SMAP assimilation mechanism.

### Storage format
Partitioned Parquet (`year=YYYY/part-MM.parquet`) format.

## Block 3 — VALUE
*Pending Step 32C*
