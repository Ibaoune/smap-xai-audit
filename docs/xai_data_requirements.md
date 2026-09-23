# SMAP-XAI Data Requirements Specification

**Project:** SMAP-XAI Audit
**Author:** M. El Aabaribaoune (@um6p)

## 1. Purpose

This document defines:
- XAI prediction targets;
- predictor families;
- exact required variables;
- source datasets;
- derived quantities;
- temporal/spatial support;
- required vs optional predictors;
- current readiness status.

This document serves as the scientific requirements specification that answers: **WHAT DATA DOES THE XAI ANALYSIS REQUIRE?** It does NOT describe preprocessing algorithms.

## 2. Common Source Variables

| Canonical variable | Scientific meaning | Source | Native variable | Native support | XAI role | Status |
|---|---|---|---|---|---|---|
| `ssm_opl` | OPL surface soil moisture | Noah-MP OPL | `SoilMoist_tavg` layer 1 | daily | predictor | ready |
| `sm_layer1_opl` | OPL native soil-moisture layer 1 | Noah-MP OPL | `SoilMoist_tavg` layer 1 | daily | predictor/vertical diag | ready |
| `sm_layer2_opl` | OPL native soil-moisture layer 2 | Noah-MP OPL | `SoilMoist_tavg` layer 2 | daily | predictor/vertical diag | ready |
| `sm_layer3_opl` | OPL native soil-moisture layer 3 | Noah-MP OPL | `SoilMoist_tavg` layer 3 | daily | predictor/vertical diag | ready |
| `sm_layer4_opl` | OPL native soil-moisture layer 4 | Noah-MP OPL | `SoilMoist_tavg` layer 4 | daily | predictor/vertical diag | ready |
| `rzsm_opl` | OPL root-zone soil moisture 0–100 cm | derived from OPL layers 1–3 | N/A | daily | predictor / drought basis | ready to derive |
| `precipitation` | total atmospheric precipitation forcing | OPL LIS HIST | `TotalPrecip_tavg` | daily 24-h tavg | predictor | ready |
| `air_temperature` | near-surface air temperature forcing | OPL LIS HIST | `Tair_f_tavg` | daily 24-h tavg | predictor | ready |
| `et_opl` | OPL evapotranspiration | Noah-MP OPL | `Evap_tavg` | daily | predictor | ready |
| `surface_runoff_opl` | OPL surface runoff | Noah-MP OPL | `Qs_tavg` | daily | predictor | ready |
| `baseflow_opl` | OPL baseflow | Noah-MP OPL | `Qsb_tavg` | daily | predictor | ready |
| `elevation` | static elevation | lis_input_NorthMor_5km.nc | `ELEVFGRD` | static | predictor | ready |
| `soil_texture` | fractional soil texture | lis_input_NorthMor_5km.nc | `TEXTURE` | static | predictor | ready |
| `land_cover` | fractional land cover | lis_input_NorthMor_5km.nc | `LANDCOVER` | static | predictor | ready |
| `irrigation_fraction` | irrigated area fraction | lis_input_NorthMor_5km.nc | `IRRIGFRAC` | static | N/A (current) | constant zero |

### Land State Definitions
*   `rzsm_opl = 0.10 * sm_layer1_opl + 0.30 * sm_layer2_opl + 0.60 * sm_layer3_opl`

### Meteorology Note
`precipitation` is derived from `TotalPrecip_tavg`, explicitly documented as `TotalPrecip_tavg = Rainf_tavg + Snowf_tavg`. `TotalPrecip_tavg` is selected instead of `Rainf_tavg` because it represents the full atmospheric precipitation forcing available to the land surface model.

### Static Surface Note
*   `soil_texture`: Native representation is a 16-class fractional field.
*   `land_cover`: Native representation is a 20-class MODIS-IGBP fractional field.
*   `irrigation_fraction`: Has no variance in the current noirr experiments and must therefore NOT be used as a predictive feature in the current XAI models. It is kept documented for future irrigation-enabled experiments.

## 3. Assimilation Information

*   **`daily_signed_increment`**
    *   **Source**: EnKF `anlys_incr_Soil Moisture Layer X_01`
    *   **Definition**: analysis - forecast
    *   **Units**: m3 m-3
    *   **Support**: daily pixel-day
    *   **Status**: ready
*   **`daily_absolute_increment`**
    *   **Source**: derived from `daily_signed_increment`
    *   **Definition**: `abs(daily_signed_increment)`
    *   **Units**: m3 m-3
    *   **Support**: daily pixel-day
    *   **Status**: ready
*   **`innovation`**
    *   **Source**: `innov_01`
    *   **Definition**: observation - forecast
    *   **Units**: m3 m-3
    *   **Role**: DA diagnostic
    *   **Native support**: event_time
*   **`normalized_innovation`**
    *   **Source**: `ninnov_01`
    *   **Units**: dimensionless
    *   **Role**: optional DA diagnostic
*   **`observation_frequency`**
    *   **Derived from**: EnKF/SMAP assimilation-event occurrence
    *   **Role**: predictor
    *   **Status**: ready (daily calendar UTC, based on finite innovation)

## 4. XAI-Source

**Scientific question**: What controls the generation of the SMAP correction?

**Targets**:
*   `daily_signed_increment`
*   `daily_absolute_increment`

**Separate models**:
*   DA-NoCDF
*   DA-CDF

**Core predictors**:
`ssm_opl`, `rzsm_opl`, `sm_layer2_opl`, `sm_layer3_opl`, `precipitation`, `air_temperature`, `observation_frequency`, `elevation`, `soil_texture`, `land_cover`, `season` / `month`, `drought_state`

**Optional predictors**:
`forcing_discrepancies` at collocated stations only.

**Explicit exclusions when increment is target**:
`innovation`, `normalized_innovation`, the `increment` itself as a predictor, and downstream DA responses. This avoids mechanically reconstructing the EnKF update.

## 5. XAI-Transfer

**Scientific question**: What determines whether assimilated information survives downstream?

**Targets for each DA experiment**:
*   `delta_rzsm` = `rzsm_DA` - `rzsm_OPL`
*   `delta_et` = `et_DA` - `et_OPL`
*   `delta_surface_runoff` = `surface_runoff_DA` - `surface_runoff_OPL`
*   `delta_baseflow` = `baseflow_DA` - `baseflow_OPL`

**Predictor Configurations**:

A. **Environmental model**:
`ssm_opl`, `rzsm_opl`, soil-moisture layers, `precipitation`, `air_temperature`, `et_opl`, `surface_runoff_opl`, `baseflow_opl`, `elevation`, `soil_texture`, `land_cover`, `season`, `drought_state`

B. **Pathway-informed model**:
All environmental predictors + `increment_signed` and/or `increment_absolute`

**Diagnostic quantity**:
`delta_skill_increment` = `skill_pathway` - `skill_environment`
*(ML implementation details are excluded from this document).*

## 6. XAI-Value

**Scientific question**: When does the assimilation-induced response improve agreement with independent ET observations?

**Independent ET references**:
*   GLEAM v4.3a
*   MOD16A2GF Collection 6.1
*(Legacy WaPOR requirement is replaced).*

**Targets**:
*   `et_gain_gleam` = `abs(et_opl - et_gleam) - abs(et_da - et_gleam)`
*   `et_gain_mod16` = `abs(et_opl - et_mod16) - abs(et_da - et_mod16)`
*(Comparisons performed on their appropriate harmonized temporal and spatial support).*

*   **Positive gain**: assimilation improves agreement
*   **Negative gain**: assimilation degrades agreement

**Predictors**:
`increment_signed`, `increment_absolute`, `delta_rzsm`, `ssm_opl`, `rzsm_opl`, `precipitation`, `air_temperature`, `et_opl`, `elevation`, `soil_texture`, `land_cover`, `season`, `drought_state`

**Optional Predictors**: station-derived forcing discrepancies.

## 7. ET Reference Robustness

**Conceptual classifications**:
*   **`robust_improvement`**: `et_gain_gleam > 0` and `et_gain_mod16 > 0`
*   **`robust_degradation`**: `et_gain_gleam < 0` and `et_gain_mod16 < 0`
*   **`reference_dependent`**: signs differ between the two ET references

This classification is valid only where the two references have been harmonized to comparable spatial and temporal support.

## 8. Drought-Conditioned XAI

**Required derived variable**: `drought_state` / `drought_phase`
**Source basis**: OPL-derived hydroclimatic state (primarily OPL RZSM)
**Planned phases**: onset, intensification, persistence, recovery
**Status**: definition pending scientific specification

The preprocessing pipeline must retain sufficient OPL RZSM information to allow this classification later. Thresholds are not defined here.

## 9. Seasonal / Calendar Variables

**Derived predictors**: `year`, `month`, `season`
These are derivable from canonical time coordinates. Do not store redundant raw copies unless required by downstream tabular dataset generation.

## 10. Station-Based Forcing Discrepancies

**Status**: optional / pending metadata confirmation
**Potential stations**: Agadir-Massira, Chefchaouen
**Potential derived predictors**: `precipitation_discrepancy`, `temperature_discrepancy`

Use only for collocated station-grid analyses. Do NOT spatially propagate station discrepancies across the entire domain. Do not activate them in the main gridded XAI dataset yet.

## 11. Temporal Support

Do NOT impose monthly aggregation in source/interim preprocessing.

Native standardized supports must remain:
*   **Noah-MP**: daily
*   **EnKF**: event_time
*   **GLEAM**: daily
*   **MOD16**: native composite
*   **static predictors**: static

The current XAI sample is a valid land pixel-day. No monthly aggregation is part of the current XAI design. (Historical note: earlier drafts considered a pixel-month analysis, but the architecture and current convention are now strictly daily).

## 12. Validation Support Variables

Ensure later XAI datasets can derive:
*   `year` (for temporal holdout)
*   `spatial_block_id` (for spatial GroupKFold)
Do not generate blocks here.

## 13. Readiness Matrix

| Requirement | Status |
|-------------|--------|
| OPL soil state | Ready |
| OPL flux baseline | Ready |
| Total precipitation | Ready |
| Air temperature | Ready |
| Elevation | Ready |
| Soil texture fractions | Ready |
| Land-cover fractions | Ready |
| Irrigation fraction | Available but constant zero; exclude from current XAI |
| EnKF increment | Ready |
| EnKF innovation | Ready |
| Observation frequency | Derivable |
| GLEAM ET | Ready |
| MOD16 ET | Ready |
| RZSM | Derivable |
| DA response targets | Derivable |
| ET gain targets | Derivable |
| Season/month | Derivable |
| Drought phase | Definition pending |
| Station forcing discrepancies | Optional / pending station metadata |
