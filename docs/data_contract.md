# SMAP-XAI Data Contract

**Project:** SMAP-XAI Audit
**Author:** M. El Aabaribaoune (@um6p)
## 1. Purpose
This data contract defines the standardized data representation expected by the SMAP-XAI preprocessing pipeline. It defines canonical variable names, units, temporal representation, spatial representation, required dimensions, missing-value handling, and alignment rules between the model, DA diagnostics, and observations. It describes what the preprocessing step must produce, separating raw/native data from standardized outputs.

## 2. Spatial Representation

The pipeline defines TWO spatial contexts.

### A. Model / DA Analysis Grid
- **Source**: Noah-MP native grid
- **Resolution**: 0.05 degree
- **Dimensions**: 121 x 181
- **Latitude**: 30.0 to 36.0
- **Longitude**: -10.0 to -1.0

Geographic latitude/longitude coordinates must be used in standardized outputs. The original Noah-MP grid must not be altered.
Used for: `ssm`, `soil_moisture_layer1` through `4`, `rzsm`, `et`, `surface_runoff`, `baseflow`, `increment`, `innovation`, `normalized_innovation`.

### B. ET Evaluation Grid
Use the GLEAM native 0.1-degree geographic grid subset covering the Noah-MP domain as the common ET evaluation grid. Harmonized ET-evaluation products must share this common 0.1-degree evaluation grid. The exact aggregation/reprojection algorithms will be documented in `docs/data_preprocessing.md`.

## 2.3 Static Physiographic Predictors
- `elevation` (source: `lis_input_NorthMor_5km.nc`, units: `m`, temporal representation: `static lat-lon`)
- `soil_texture` (source: `lis_input_NorthMor_5km.nc`, units: `1` (fraction), temporal representation: `static lat-lon`)
- `land_cover` (source: `lis_input_NorthMor_5km.nc`, units: `1` (fraction), temporal representation: `static lat-lon`)

## 3. Temporal Representations
Data sources will not be forced onto a single temporal frequency. The pipeline handles three distinct temporal representations.

### A. Daily land-model representation
For variables: SSM, RZSM components, ET, surface runoff, and baseflow.
- **Native Noah-MP interval**: 24 h
- **Target standardized dimension**: `time`
- **Target temporal resolution**: daily
`time` labels the beginning/calendar day of the represented 24-h interval.

### B. DA-event representation
For variables: increment and innovation.
- **Target standardized dimension**: `event_time`
Native event timestamps must be retained. Do not prematurely aggregate increments or innovations to daily values. A derived daily/event-day representation may be created later if required by the XAI experiments.

### C. MOD16 representation
MOD16 is kept on its native composite temporal support.
- **Target standardized dimension**: `composite_time`

## 4. Canonical Variables

| Canonical name | Source variable | Source | Units target | Temporal representation |
|----------------|-----------------|--------|--------------|-------------------------|
| `ssm` | SoilMoist_tavg layer 1 | Noah-MP | m3 m-3 | daily |
| `soil_moisture_layer1` | SoilMoist_tavg layer 1 | Noah-MP | m3 m-3 | daily |
| `soil_moisture_layer2` | SoilMoist_tavg layer 2 | Noah-MP | m3 m-3 | daily |
| `soil_moisture_layer3` | SoilMoist_tavg layer 3 | Noah-MP | m3 m-3 | daily |
| `soil_moisture_layer4` | SoilMoist_tavg layer 4 | Noah-MP | m3 m-3 | daily |
| `rzsm` | derived | Noah-MP | m3 m-3 | daily |
| `et` | Evap_tavg | Noah-MP | mm day-1 | daily |
| `surface_runoff` | Qs_tavg | Noah-MP | mm day-1 | daily |
| `baseflow` | Qsb_tavg | Noah-MP | mm day-1 | daily |
| `increment` | anlys_incr_Soil Moisture Layer X_01 | EnKF | m3 m-3 | event_time |
| `innovation` | innov_01 | EnKF | m3 m-3 | event_time |
| `et_gleam` | E | GLEAM v4.3a | mm day-1 | daily |
| `et_mod16` | ET_500m | MOD16A2GF C6.1 | mm per native composite | composite_time |
| `delta_rzsm` | derived | derived | m3 m-3 | daily |

## 4.1 Optional EnKF Diagnostics
Document as available optional standardized diagnostics:
- `daily_analysis_residual` (source: derived from `analysis_residual`, units: `m3 m-3`, temporal representation: `time` (daily, assimilation-conditional), role: `post-analysis diagnostic`)
- `daily_forecast_variance` (source: derived from `forecast_variance`, units: `(m3 m-3)^2`, temporal representation: `time` (daily, assimilation-conditional))
- `daily_normalized_innovation` (source: derived from `normalized_innovation`, units: `1`, temporal representation: `time` (daily, assimilation-conditional))
- `daily_innovation` (source: derived from `innovation`, units: `m3 m-3`, temporal representation: `time` (daily, assimilation-conditional))
- `daily_absolute_increment` (source: derived from `daily_signed_increment`, units: `m3 m-3`, temporal representation: `time` (daily))
- `daily_signed_increment` (source: derived from `increment_signed`, units: `m3 m-3`, temporal representation: `time` (daily))
- `observation_frequency` (source: derived from `isfinite(innovation)`, units: `1`, temporal representation: `time` (daily))
- `normalized_innovation` (source: `ninnov_01`, units: dimensionless)
- `forecast_variance` (source: `forecast_sigma_01`, units: `(m3 m-3)^2`)
- `analysis_residual` (source: `analysis_residual_01`, units: `m3 m-3`)
Keep `increment` and `innovation` as the core DA diagnostics.

## 5. Model Experiment Dimension
Standardized model data must distinguish between OPL, DA-NoCDF, and DA-CDF experiments.
Preferred canonical experiment labels:
- `opl`
- `da_nocdf`
- `da_cdf`

Experiment identity must not be encoded solely in filenames. Where practical, preprocessing outputs should expose the experiment as an explicit metadata element or dimension.

## 6. Canonical Flux Units
Raw Noah-MP flux variables (`Evap_tavg`, `Qs_tavg`, `Qsb_tavg`) are output in `kg m-2 s-1`.
- **Target standardized units**: `mm day-1`

## 7. RZSM
All four standardized soil-moisture layers must be kept.
Layer depths:
- **Layer 1**: 0–10 cm
- **Layer 2**: 10–40 cm
- **Layer 3**: 40–100 cm
- **Layer 4**: 100–200 cm

**Canonical:** `rzsm`
**Depth:** 0–100 cm
**Units:** `m3 m-3`
**Definition:**
`rzsm = 0.10 * soil_moisture_layer1 + 0.30 * soil_moisture_layer2 + 0.60 * soil_moisture_layer3`

Retain all native layers in standardized data.

## 8. GLEAM Contract
- **Source**: GLEAM v4.3a
- **Role**: Primary independent ET reference
- **Variable**: E
- **Native units**: mm day-1
- **Native frequency**: daily
- **Native grid**: 0.1 degree global lat/lon
- **Target standardized variable**: `et_gleam`
- **Target unit**: mm day-1
- **Target temporal representation**: daily
- **Spatial preprocessing**: Align to the common 0.1-degree ET evaluation grid.

## 9. MOD16 Contract
- **Product**: MOD16A2GF Collection 6.1
- **Role**: Second independent ET reference
- **Subdataset**: ET_500m
- **Scale factor**: 0.1
- **Native physical representation**: mm per composite
- **Native support**: 8-day composite
- **Projection**: MODIS Sinusoidal
- **Native resolution**: 500 m
- **Target standardized variable**: `et_mod16`
- **Target unit**: mm per native composite

Do not define it as daily. Preserve information describing each composite period.
- **Spatial preprocessing**: Align to the common 0.1-degree ET evaluation grid.
- **QC**: `ET_QC_500m` must be retained or translated into a usable quality mask.

## 10. In-Situ Station Contract
In-situ files are not yet active quantitative inputs. 
- **Agadir-Massira**: 2016–2020 coverage, inside model domain, variables/units not yet confirmed.
- **Chefchaouen**: 2016–2020 coverage, inside model domain, variables/units not yet confirmed.

Standardized station variables remain pending external metadata confirmation. Do not assign columns 4–6 to precipitation/Tmax/Tmin until confirmed. Historical CSV and stations outside the model domain are not active inputs for the current preprocessing pipeline.

## 11. Missing Values
Standardized floating-point missing values = `NaN`.
Do not retain source-specific transformation algorithms here. Source fill/sentinel values remain documented in `data_inventory.md`. Their conversion to `NaN` will be described in `data_preprocessing.md`.

## 12. Required standardized dimensions
- **Daily model/reference arrays**: `time`, `lat`, `lon`
- **Soil-moisture arrays**: `time`, `soil_layer`, `lat`, `lon`
- **DA diagnostics**: `event_time`, `lat`, `lon` (or `event_time`, `soil_layer`, `lat`, `lon` when retaining layer-specific diagnostics)
- **MOD16 standardized representation**: `composite_time`, `lat`, `lon`

## 13. Required Metadata
Every standardized variable must retain:
- Canonical variable name
- Physical units
- Source dataset
- Source variable
- Experiment (where applicable)
- Temporal support
- Processing history
- Missing-value convention

## 14. Unresolved Contract Items

Source-specific preprocessing algorithms and QC choices are documented separately in `docs/data_preprocessing.md`.
