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
