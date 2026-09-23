# Data Preprocessing

**Project:** SMAP-XAI Audit
**Author:** M. El Aabaribaoune (@um6p)
## Noah-MP / Surface Soil Moisture

### SOURCE
- **exact experiment root**: `/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/OPL_noirr_2016_2020/`
- **file pattern**: `output/YYYY-MM/SURFACEMODEL/YYYYMM/LIS_HIST_YYYYMMDD0000.d01.nc`
- **variable**: `SoilMoist_tavg`
- **layer**: layer 1 = 0–10 cm
- **unit**: m3 m-3

### PROCESSING
- filename timestamp - 1 day
- select layer 1
- standardize dimensions to time, lat, lon
- no numerical unit conversion
- no regridding
- no interpolation

### OUTPUT
- `data/interim/noahmp/opl/ssm/ssm_YYYY.nc` (2016–2020)
- `data/interim/noahmp/da_nocdf/ssm/ssm_YYYY.nc` (2016–2020)
- `data/interim/noahmp/da_cdf/ssm/ssm_YYYY.nc` (2016–2020)

### QC
- **TEMPORAL QC**:
  - first canonical date = 2016-01-01
  - last canonical date = 2020-12-31 (across the multi-year concatenated timeline)
  - number of timestamps = 366 (leap years) or 365 (standard years), summing to 1827 total valid days per experiment.
  - all timestamps unique = True
  - daily spacing exactly one day = True
  - missing calendar dates = 0
- **SPATIAL QC**:
  - dimensions = 121 x 181
  - latitude range = 30.0000 to 36.0000
  - longitude range = -10.0000 to -1.0000
  - grid spacing = 0.0500 (lat), 0.0500 (lon)
  - coordinate ordering = ('time', 'lat', 'lon')
  - same grid in all source files = True
- **VARIABLE QC**:
  - dtype = float32
  - NaN fraction = ~0.268070 (stable across space and time)
  - values < 0 = 0
  - values > 1 = 0

- **MISSING-DATA BEHAVIOR**:
  - Mask stability = spatially stable throughout the period
  - Number of pixels whose valid/missing status changes = 0
- **EQUALITY VALIDATION**:
  - Max absolute diff vs raw = 0.0
  - Mean absolute diff vs raw = 0.0
  - Unequal finite pixels = 0

### QUICKLOOKS
QC quicklooks were generated for comparative inspection across all three experiments. They are strictly preprocessing artifacts and reside in:
- `reports/qc/ssm/`

The SSM QC visual suite includes:
- Daily spatial-mean comparison time series across experiments.
- 2016–2020 temporal-mean maps for each experiment (using a common, discrete scale).
- DA-minus-OPL temporal-mean difference maps (using a symmetric, discrete scale centered at zero).
These common and discrete scales support direct visual comparison.

### STATUS
SSM preprocessing has now been successfully completed for all three experiments (OPL, DA-NoCDF, and DA-CDF) over the full 2016–2020 period. All years passed strict temporal and spatial validation checks.

## DAILY XAI DESIGN
The canonical temporal resolution of the SMAP-XAI analysis is daily.

The planned XAI sample is a valid land pixel-day.

No monthly aggregation is part of the current XAI design.

## Noah-MP / Soil Moisture Layer 2

### SOURCE
- **canonical variable**: `sm_layer2`
- **source variable**: `SoilMoist_tavg`
- **layer**: layer 2 = 10–40 cm

### PROCESSING
- source index 1
- filename timestamp - 1 day
- standardized time/lat/lon coordinates
- no numerical unit conversion
- no regridding
- no interpolation

### OUTPUT
- `data/interim/noahmp/<experiment>/sm_layer2/`

### COVERAGE
- OPL / DA-NoCDF / DA-CDF
- 2016–2020
- 1827 daily samples per experiment

### QC
- numerical validation passed
- raw-vs-interim numerical identity verified
- comparative quicklooks generated

### NOTES
- Layer 1 is NOT duplicated here because its canonical representation already exists as SSM.

## Noah-MP / Soil Moisture Layer 3

### SOURCE
- **canonical variable**: `sm_layer3`
- **source variable**: `SoilMoist_tavg`
- **layer**: layer 3 = 40–100 cm
- **unit**: m3 m-3
- **temporal support**: daily
- **role**: required for canonical RZSM 0–100 cm calculation

### PROCESSING
- source index 2
- filename timestamp - 1 day
- standardized time/lat/lon coordinates
- no numerical unit conversion
- no regridding
- no interpolation

### OUTPUT
- `data/interim/noahmp/<experiment>/sm_layer3/`

### COVERAGE
- OPL / DA-NoCDF / DA-CDF
- 2016–2020
- 1827 daily samples per experiment

### QC
- numerical validation passed
- raw-vs-interim numerical identity strictly verified (max abs diff = 0.0)
- comparative quicklooks generated and stored at `reports/qc/sm_layer3/`

## Noah-MP / Soil Moisture Layer 4

### SOURCE
- **canonical variable**: `sm_layer4`
- **source variable**: `SoilMoist_tavg`
- **layer**: layer 4 = 100–200 cm
- **unit**: m3 m-3
- **temporal support**: daily
- **role**: retained as an independent deep-layer XAI predictor / diagnostic. NOT included in RZSM 0–100 cm.

### PROCESSING
- source index 3
- filename timestamp - 1 day
- standardized time/lat/lon coordinates
- no numerical unit conversion
- no regridding
- no interpolation

### OUTPUT
- `data/interim/noahmp/<experiment>/sm_layer4/`

### COVERAGE
- OPL / DA-NoCDF / DA-CDF
- 2016–2020
- 1827 daily samples per experiment

### QC
- numerical validation passed
- raw-vs-interim numerical identity strictly verified (max abs diff = 0.0)
- comparative quicklooks generated and stored at `reports/qc/sm_layer4/`

## Noah-MP / Root-Zone Soil Moisture (0–100 cm)

### SOURCE INPUTS
- standardized interim ssm
- standardized interim sm_layer2
- standardized interim sm_layer3

### DERIVATION
- `rzsm = 0.10*ssm + 0.30*sm_layer2 + 0.60*sm_layer3`

### RATIONALE
- thickness-weighted volumetric soil moisture over 0–100 cm

### EXCLUSION
- `sm_layer4` is excluded because it represents 100–200 cm

### OUTPUT
- `data/processed/daily_model/<experiment>/rzsm/`

### TEMPORAL SUPPORT
- daily

### COVERAGE
- OPL / DA-NoCDF / DA-CDF
- 2016–2020

### QC
- input alignment validated exactly
- independent formula verification mathematically validated
- physical convex-average check passed continuously
- temporal continuity strictly verified (1827 valid days)
- spatial consistency aligned strictly over the domain
- quicklooks generated (time series, mean maps, difference maps)

## Noah-MP / Total Precipitation

### SOURCE
- **source variable**: `TotalPrecip_tavg`
- **unit**: kg m-2 s-1
- **support**: 24-hour mean rate

### CANONICAL VARIABLE
- `precipitation`

### CONVERSION
- `precipitation = TotalPrecip_tavg * 86400`

### CANONICAL UNIT
- mm day-1

### TIME
- LIS_HIST timestamp - 1 day

### STORAGE
- **Decision**: All experiments originate from the identical MERRA2 + GPM IMERG forcing dataset. OPL is deterministic and unperturbed. DA runs use 20-member GMAO forcing perturbations. DA-NoCDF and DA-CDF precipitation outputs are mathematically identical to each other but differ from OPL specifically because of these stochastic forcing perturbations.
- **Canonical Predictor**: To ensure the XAI model learns from true environmental conditions rather than the DA internal random noise generator, canonical XAI precipitation utilizes exclusively OPL `TotalPrecip_tavg`. Only one standardized, shared precipitation dataset is stored.

### OUTPUT
- `data/interim/noahmp/forcing/precipitation/`

### COVERAGE
- 2016–2020
- 1827 daily samples

### QC
- cross-experiment equality rigorously verified (confirmed DA forcing perturbations vs OPL)
- unit-conversion identity mathematically confirmed
- range checks passed (no negative precipitation)
- annual accumulated precipitation computed properly
- spatial/temporal quicklooks generated

## Noah-MP / Near-Surface Air Temperature

### SOURCE
- **source variable**: `Tair_f_tavg`
- **unit**: K
- **support**: 24-hour mean temperature

### CANONICAL VARIABLE
- `air_temperature`

### CANONICAL UNIT
- K

### TIME
- LIS_HIST timestamp - 1 day

### STORAGE
- **Decision**: Analysis confirmed that near-surface air temperature is not stochastically perturbed in the DA experiments (unlike precipitation). However, owing to DA ensemble averaging (N=20 members) over identical values, infinitesimal floating-point arithmetic artifacts (~1e-5 K) are introduced in DA outputs. To strictly retain the unperturbed environmental forcing without arithmetic noise, the OPL representation is retained as the single canonical dataset.
- **Canonical Predictor**: Canonical XAI air temperature utilizes exclusively OPL `Tair_f_tavg`. Only one standardized, shared air temperature dataset is stored.

### OUTPUT
- `data/interim/noahmp/forcing/air_temperature/`

### COVERAGE
- 2016–2020
- 1827 daily samples

### QC
- cross-experiment diagnostic (identity verification)
- raw-vs-interim identity (exact float32 precision match)
- range checks passed (Morocco domain normal limits verified in K and °C)
- mask checks passed (identically matches SSM and precipitation missing values)
- quicklooks generated (time series, mean maps)

## Noah-MP / Evapotranspiration

### PHYSICAL DEFINITION
- `Evap_tavg` represents total land-surface evapotranspiration. It aggregates bare soil evaporation, transpiration, canopy interception evaporation, and snow sublimation.

### SIGN CONVENTION
- Positive values denote upward water-mass flux from land to atmosphere. Negative values represent condensation/deposition (dew/frost) and are physically valid.

### SOURCE
- **source variable**: `Evap_tavg`
- **unit**: kg m-2 s-1

### CANONICAL VARIABLE
- `et`

### CANONICAL UNIT
- mm day-1

### CONVERSION
- `et = Evap_tavg * 86400`
- Values are strictly multiplied by seconds per day without absolute value or clipping, faithfully retaining physical dew formation.

### TIME
- LIS_HIST timestamp - 1 day

### STORAGE
- **Decision**: Unlike meteorological forcing, evapotranspiration is an experiment-dependent prognostic model response driven by assimilation logic. Therefore, it is extracted independently for each experiment.

### OUTPUT
- `data/interim/noahmp/opl/et/`
- `data/interim/noahmp/da_nocdf/et/`
- `data/interim/noahmp/da_cdf/et/`

### COVERAGE
- OPL, DA-NoCDF, DA-CDF
- 2016–2020 (1827 daily samples each)

### QC
- raw-vs-interim unit conversion check passed precisely.
- range/sign diagnostics executed (minor negative fraction validated as condensation).
- annual accumulated ET reported successfully by experiment.
- grid/mask perfectly aligns with SSM and RZSM missing values.
- cross-experiment diagnostics and quicklooks (DA - OPL differences) mapped and documented.
- **Note**: The banded spatial structure visible in some DA-minus-OPL ET quicklooks is present in the underlying daily standardized fields and is not introduced by preprocessing or plotting.

## Noah-MP / Surface Runoff

### PHYSICAL DEFINITION
- `Qs_tavg` represents explicitly surface runoff (overland flow). It fundamentally differs from subsurface runoff (baseflow, `Qsb_tavg`).

### SIGN CONVENTION
- Positive values indicate water mass leaving the land column via the surface. Negative values are generally non-physical for this flux in Noah-MP and do not occur.

### SOURCE
- **source variable**: `Qs_tavg`
- **unit**: kg m-2 s-1

### CANONICAL VARIABLE
- `surface_runoff`

### CANONICAL UNIT
- mm day-1

### CONVERSION
- `surface_runoff = Qs_tavg * 86400`

### TIME
- LIS_HIST timestamp - 1 day

### STORAGE
- **Decision**: Surface runoff is an experiment-dependent prognostic model response driven by assimilation and soil moisture state. Therefore, it is extracted independently for each experiment.

### OUTPUT
- `data/interim/noahmp/opl/surface_runoff/`
- `data/interim/noahmp/da_nocdf/surface_runoff/`
- `data/interim/noahmp/da_cdf/surface_runoff/`

### COVERAGE
- OPL, DA-NoCDF, DA-CDF
- 2016–2020 (1827 daily samples each)

### QC
- raw-vs-interim unit conversion precisely matched (float32 tolerance).
- zero diagnostics: correctly features a large fraction of zero runoff pixels (~38% in OPL, ~5% in DA runs).
- negative diagnostics: 0 negative values found, honoring physical constraints.
- annual accumulated surface runoff aggregated and reported as spatial means.
- cross-experiment difference maps created (`DA - OPL`) avoiding any physical interpretation of observational benefit. Note: Small magnitude spatial row-structures mirroring the ET banding were observed in difference metrics, verifying their origin in the underlying DA grid response.
- `delta_surface_runoff` will be created in future targets but was not derived here.

## Noah-MP / Baseflow

### PHYSICAL DEFINITION
- `Qsb_tavg` represents subsurface runoff amount. In standard Noah-MP terminology, this is baseflow or deep drainage leaving the bottom of the soil column or discharging laterally.

### RELATION TO Qs
- `Qsb_tavg` (subsurface runoff/baseflow) is strictly distinct from `Qs_tavg` (surface runoff). They represent independent hydrological fluxes.

### SIGN CONVENTION
- Positive values indicate water mass leaving the soil column via the subsurface. Negative values are unphysical and do not occur.

### SOURCE
- **source variable**: `Qsb_tavg`
- **unit**: kg m-2 s-1

### CANONICAL VARIABLE
- `baseflow`

### CANONICAL UNIT
- mm day-1

### CONVERSION
- `baseflow = Qsb_tavg * 86400`

### TIME
- LIS_HIST timestamp - 1 day

### STORAGE
- **Decision**: Baseflow is an experiment-dependent prognostic model response driven by assimilation and soil moisture state. Therefore, it is extracted independently for each experiment.

### OUTPUT
- `data/interim/noahmp/opl/baseflow/`
- `data/interim/noahmp/da_nocdf/baseflow/`
- `data/interim/noahmp/da_cdf/baseflow/`

### COVERAGE
- OPL, DA-NoCDF, DA-CDF
- 2016–2020 (1827 daily samples each)

### QC
- raw-vs-interim unit conversion matched exactly (max absolute diff 0.0).
- negative diagnostics: 0 negative values found, honoring physical constraints.
- zero diagnostics: correctly features 0 absolute zero pixels, as baseflow is a continuous slow-draining process (unlike intermittent surface runoff).
- annual accumulated baseflow aggregated and reported.
- mask equality verified perfectly with SSM, RZSM, ET, and Surface Runoff.
- `delta_baseflow` will be created in future targets but was not derived here. Note: Small magnitude spatial row-structures were observed in difference metrics (similar to ET and surface runoff), confirming the raw DA response origin.

### Known DA numerical structure

- row-wise structures occur in some DA-minus-OPL flux fields;
- they are already present in raw LIS output;
- preprocessing does not create or remove them;
- no smoothing/filtering is applied;
- detailed investigation is documented in:

    docs/model_diagnostics.md

## EnKF / Signed Analysis Increment — Soil Moisture Layer 1

**SOURCE**:
`LIS_DA_EnKF_YYYYMMDDHHMM_incr.a01.d01.nc`

**RAW VARIABLE**:
`anlys_incr_Soil Moisture Layer 1_01`

**PHYSICAL DEFINITION**:
`analysis - forecast` (increment = $x_a - x_f$)

**SIGN**:
- Positive = wetter analysis (model was too dry)
- Negative = drier analysis (model was too wet)

**LAYER**:
0–10 cm (Noah-MP Layer 1)

**UNIT**:
$m^3/m^3$ (volumetric water content)

**TEMPORAL SUPPORT**:
Assimilation event (instantaneous)

**EVENT COUNTS**:
- **DA-CDF**: 4,411 total events (2016: 872, 2017: 867, 2018: 912, 2019: 838, 2020: 922)
- **DA-NoCDF**: 4,619 total events (2016: 944, 2017: 945, 2018: 929, 2019: 860, 2020: 941)
- *2019 Observation Gap*: A known SMAP observation outage occurred from 19 June to 23 July 2019 after the satellite entered safe mode. This explains the pronounced June-July 2019 reduction in available assimilation events.

**TIME**:
Exact event-time semantics based on the filename timestamp (`YYYYMMDDHHMM`). Does NOT apply the daily `filename_time - 1 day` convention used for LIS_HIST.

**OBSERVATION TYPE**:
The `_01` suffix refers precisely to the `SMAP NASA SPL3SMP_E` observation stream as configured in LIS DA parameters.

**MISSING/ZERO**:
- **Missing (`NaN`)**: Inherited from `-9999.0`, strictly corresponding to masked/non-land grid cells.
- **Zero (`0.0`)**: Raw zero increments are preserved. Many zeros correspond to land pixels not updated at that event (e.g., outside the SMAP swath or failing QC). Zero must not automatically be interpreted as an exact physical analysis correction of zero. Future XAI construction must use an observation/update mask (`assimilation_update_mask`) to distinguish actual assimilation support, which will be constructed during innovation preprocessing using the strongest available assimilation-use diagnostic. (Note: `increment_signed != 0` serves as a `nonzero_increment_mask` useful for current QC).

**STORAGE**:
`data/interim/enkf/<experiment>/increment_signed/increment_signed_<YYYY>.nc`

**XAI ROLE**:
Primary Source target describing where and how strongly SMAP assimilation modifies the modeled surface soil-moisture state. (Note: absolute increment will be derived later).

**ROW-WISE STRUCTURE**:
No obvious row-wise structure is visible in the signed analysis increment maps. This is consistent with, but does not independently prove, the perturbation-variance mechanism documented in `model_diagnostics.md`.
