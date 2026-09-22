# SMAP-XAI Data Contract

## 1. Purpose
This data contract defines the standardized data representation expected by the SMAP-XAI preprocessing pipeline. It defines canonical variable names, units, temporal representation, spatial representation, required dimensions, missing-value handling, and alignment rules between the model, DA diagnostics, and observations. It describes what the preprocessing step must produce, separating raw/native data from standardized outputs and outlining decisions that remain unresolved.

## 2. Analysis Grid
The Noah-MP grid is defined as the main model-analysis grid.
- **Resolution**: 0.05 degree
- **Dimensions**: latitude = 121, longitude = 181
- **Latitude**: 30.0 to 36.0
- **Longitude**: -10.0 to -1.0

Geographic latitude/longitude coordinates must be used in standardized outputs. The original Noah-MP grid must not be altered.

## 3. Temporal Representations
Data sources will not be forced onto a single temporal frequency. The pipeline handles three distinct temporal representations.

### A. Daily land-model representation
For variables: SSM, RZSM components, ET, surface runoff, and baseflow.
- **Native Noah-MP interval**: 24 h
- **Target standardized dimension**: `time`
- **Target temporal resolution**: daily
*Important Note:* The LIS HIST timestamp represents the **end of the averaging interval**. The canonical date for daily standardization is the beginning/date of the represented daily interval. Therefore, when parsing filenames, raw timestamp `T` (e.g., `2016-01-02 00:00`) maps to canonical date `T - 1 day` (e.g., `2016-01-01`).

### B. DA-event representation
For variables: increment and innovation.
- **Target standardized dimension**: `event_time`
Native event timestamps must be retained. Do not prematurely aggregate increments or innovations to daily values. A derived daily/event-day representation may be created later if required by the XAI experiments.

### C. MOD16 representation
MOD16 is kept on its native composite temporal support.
- **Target standardized dimension**: `composite_time`
Do not create artificial daily MOD16 observations. Model and GLEAM data will be aggregated over the exact MOD16 composite windows when comparison is required.

## 4. Canonical Variables

| Canonical name | Source variable | Source | Units target | Temporal representation |
|----------------|-----------------|--------|--------------|-------------------------|
| `ssm` | SoilMoist_tavg layer 1 | Noah-MP | m3 m-3 | daily |
| `soil_moisture_layer1` | SoilMoist_tavg layer 1 | Noah-MP | m3 m-3 | daily |
| `soil_moisture_layer2` | SoilMoist_tavg layer 2 | Noah-MP | m3 m-3 | daily |
| `soil_moisture_layer3` | SoilMoist_tavg layer 3 | Noah-MP | m3 m-3 | daily |
| `soil_moisture_layer4` | SoilMoist_tavg layer 4 | Noah-MP | m3 m-3 | daily |
| `rzsm` | derived | Noah-MP | m3 m-3 | daily (definition pending) |
| `et` | Evap_tavg | Noah-MP | mm day-1 | daily |
| `surface_runoff` | Qs_tavg | Noah-MP | mm day-1 | daily |
| `baseflow` | Qsb_tavg | Noah-MP | mm day-1 | daily |
| `increment` | anlys_incr_Soil Moisture Layer X_01 | EnKF | m3 m-3 | event_time |
| `innovation` | innov_01 | EnKF | m3 m-3 | event_time |

## 5. Model Experiment Dimension
Standardized model data must distinguish between OPL, DA-NoCDF, and DA-CDF experiments.
Preferred canonical experiment labels:
- `opl`
- `da_nocdf`
- `da_cdf`

Experiment identity must not be encoded solely in filenames. Where practical, preprocessing outputs should expose the experiment as an explicit metadata element or dimension.

## 6. Flux Unit Conversion
Raw Noah-MP flux variables (`Evap_tavg`, `Qs_tavg`, `Qsb_tavg`) are output in `kg m-2 s-1`.
- **Target standardized units**: `mm day-1`
For a verified 24-h averaging interval, the conversion is:
`target = raw * 86400`
*(Based on the equivalence: 1 kg m-2 water = 1 mm water depth).*

## 7. RZSM
All four standardized soil-moisture layers must be kept.
Layer depths:
- **Layer 1**: 0–10 cm
- **Layer 2**: 10–40 cm
- **Layer 3**: 40–100 cm
- **Layer 4**: 100–200 cm

`rzsm_definition` = pending scientific decision
Do not define the final RZSM product yet. The preprocessing implementation must make RZSM depth weighting configurable rather than hard-coded.

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
- **Spatial preprocessing**: Align/regrid to the Noah-MP 0.05-degree analysis grid. The exact regridding method is a preprocessing-method decision and is not defined here.

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

Do not define it as daily. Preserve information describing each composite period.
- **For model comparison**: Aggregate Noah-MP daily ET over exact MOD16 composite windows.
- **For cross-reference comparison**: Aggregate GLEAM daily ET over the same windows.
- **Spatial preprocessing**: Reproject and aggregate MOD16 to the Noah-MP analysis grid.
- **QC**: `ET_QC_500m` must be retained or translated into a usable quality mask (exact QC acceptance rule remains a later decision).

## 10. In-Situ Station Contract
In-situ files are not yet active quantitative inputs. 
- **Agadir-Massira**: 2016–2020 coverage, inside model domain, variables/units not yet confirmed.
- **Chefchaouen**: 2016–2020 coverage, inside model domain, variables/units not yet confirmed.

Standardized station variables remain pending external metadata confirmation. Do not assign columns 4–6 to precipitation/Tmax/Tmin until confirmed. Historical CSV and stations outside the model domain are not active inputs for the current preprocessing pipeline.

## 11. Missing Values
Standardized numeric outputs should use `NaN` for missing floating-point values. Raw source sentinel values (e.g., MOD16 FillValue = `32767`, station TXT sentinel = `-99.9`) must be converted to `NaN` during source-specific preprocessing. Do not apply this transformation yet.

## 12. Standard Output Dimensions
Recommended array dimensions for standardized outputs:
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
These unresolved items will not block the creation of the data contract.

| Item |
|------|
| 2. Final RZSM depth/weighting definition |
| 3. GLEAM-to-Noah-MP regridding method |
| 4. MOD16 spatial aggregation/reprojection method |
| 5. MOD16 QC acceptance rule |
| 6. Exact identities/units of individual station TXT columns |
