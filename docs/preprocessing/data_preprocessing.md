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

    docs/preprocessing/model_diagnostics.md

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

## EnKF / Innovation — SMAP Surface Soil Moisture

**SOURCE**:
`LIS_DA_EnKF_YYYYMMDDHHMM_innov.a01.d01.nc`

**RAW VARIABLE**:
`innov_01`

**PHYSICAL DEFINITION**:
`observation - forecast equivalent` ($y - H(x_f)$). This exact mathematical definition is explicitly confirmed in the Noah-MP EnKF source code (`enkf_Mod.F90`: `innov = Observations(i)%value - sum(Obs_pred(i,:))/real(LIS_rc%nensem(n))`).

**SIGN**:
- Positive: Observation representation is wetter than the forecast equivalent.
- Negative: Observation representation is drier than the forecast equivalent.

**LAYER**:
0–10 cm (Noah-MP Layer 1, implicit for `_01` SMAP surface soil moisture)

**UNIT**:
$m^3/m^3$ (volumetric water content)

**TEMPORAL SUPPORT**:
Assimilation event (instantaneous, `YYYYMMDDHHMM`).

**OBSERVATION TYPE**:
The `_01` suffix refers to the `SMAP NASA SPL3SMP_E` observation stream.
- **DA-CDF**: The observation representation entering $y$ is the CDF-matched SMAP observation, which has been rescaled to the model's native climatology.
- **DA-NoCDF**: The observation representation entering $y$ is the non-CDF-matched observation representation used by that experiment.
Therefore, CDF matching strictly modifies the observation used in the innovation calculation. DA-CDF innovation is NOT directly comparable to NoCDF innovation as a skill score since they operate in different observation spaces.

**EVENT COUNTS**:
- **DA-CDF**: 4,411 total events (Matches DA-CDF signed increment precisely: 4,411 increment events. Intersection: 4,411. Innovation-only: 0. Increment-only: 0).
- **DA-NoCDF**: 4,619 total events (Matches DA-NoCDF signed increment precisely: 4,619 increment events. Intersection: 4,619. Innovation-only: 0. Increment-only: 0).
- *2019 Observation Gap*: Consistent with the increment behavior, the documented SMAP observation outage from 19 June to 23 July 2019 is correctly reproduced in the innovation availability.

**RAW-TO-INTERIM IDENTITY**:
Verification of 3 representative 2016 events confirmed:
- Max absolute difference: 0.0
- Mean absolute difference: 0.0
- Unequal finite pixels: 0
- Missing-mask differences: 0

**MISSING/ZERO/REJECTED SEMANTICS**:
Based on `enkf_Mod.F90` logic (`if(Observations(i)%assim) then ... else ... LIS_rc%udef`):
- **Valid and assimilated**: Finite innovation value is computed and written.
- **Rejected by DA QC**: Written as missing (`LIS_rc%udef`, translated to `-9999.0` then `NaN`).
- **No observation exists**: Written as missing.
- **Point is masked/non-land**: Written as missing.
- **Exactly zero**: Represents a mathematically exact zero innovation (meaning the observation perfectly matched the forecast equivalent).

**FINAL ASSIMILATION-SUPPORT MASK**:
Because the source code confirms a finite innovation is written *only* after the observation passes all DA QC and is actually assimilated (`Observations(i)%assim`), we formally define:
`assimilation_update_mask = isfinite(innovation)`

**INCREMENT CROSS-CHECK**:
Validating the `assimilation_update_mask` against 2016 increment files:
- **DA-CDF 2016**:
  - finite innov + nonzero inc: 345,488
  - finite innov + zero inc: 0
  - missing innov + zero inc: 13,632,672
  - missing innov + nonzero inc: 0
- **DA-NoCDF 2016**:
  - finite innov + nonzero inc: 1,515,413
  - finite innov + zero inc: 0
  - missing innov + zero inc: 13,616,907
  - missing innov + nonzero inc: 0
This demonstrates that finite innovation perfectly controls where an assimilation update occurs.

**INNOVATION STATISTICS**:
- **DA-CDF**:
  - min: -0.2913, max: 0.2305, mean: -0.0131, median: -0.0061, std: 0.0362
  - p05: -0.0869, p25: -0.0265, p75: 0.0087, p95: 0.0302
  - fractions: 60.5% negative, 0.0% exactly zero, 39.5% positive
- **DA-NoCDF**:
  - min: -0.2538, max: 0.3343, mean: -0.0061, median: -0.0053, std: 0.0371
  - p05: -0.0659, p25: -0.0263, p75: 0.0124, p95: 0.0516
  - fractions: 57.9% negative, 0.0% exactly zero, 42.1% positive
- **CDF vs NoCDF Interpretation**: DA-CDF innovation is slightly more concentrated around zero, while DA-NoCDF has broader tails. However, this does NOT mean smaller innovation is "better" or "more accurate", because they use completely different observation representations.

**INNOVATION VS INCREMENT NUMERICS**:
- **DA-CDF**: Pearson: 0.916, Spearman: 0.977, same sign: 100.0%, opposite sign: 0.0%, exact-zero inc: 0.0%
- **DA-NoCDF**: Pearson: 0.954, Spearman: 0.983, same sign: 100.0%, opposite sign: 0.0%, exact-zero inc: 0.0%

**ROW-WISE STRUCTURE**:
Innovation maps show no obvious row-wise structure. This supports (but does not independently prove) that the striping artifact originates downstream in the perturbation/propagation steps rather than the observation space.

**XAI ROLE**:
Primary indicator of the direction and magnitude of the incoming observational signal, and the definitive source for the true `assimilation_update_mask`.

## EnKF / Forecast Uncertainty

**SOURCE**:
`LIS_DA_EnKF_YYYYMMDDHHMM_innov.a01.d01.nc`

**RAW VARIABLE**:
`forecast_sigma_01`

**EXACT DEFINITION**:
Despite the "sigma" naming convention in the NetCDF output, source-code inspection (`enkf_Mod.F90` line 434) rigorously confirms that this variable stores the **forecast error variance in observation space** ($HPH^T$), NOT standard deviation. The code calculates `row_variance(1,LIS_rc%nensem(n),Obs_pred(i,:),std_innov(1))` and saves it directly to `enkf_struc(n,k)%forecast_var(i)`.

**CANONICAL VARIABLE**:
`forecast_variance` (the raw variable name `forecast_sigma_01` is preserved as a metadata attribute to prevent future confusion).

**UNIT**:
$(m^3 m^{-3})^2$

**TIME**:
Assimilation event (instantaneous, `YYYYMMDDHHMM`).

**SUPPORT**:
Finite values strictly align with `assimilation_update_mask`.
- Intersection of finite variance and finite innovation: 2,456,233 (DA-CDF)
- Finite variance + missing innovation: 0
- Missing variance + finite innovation: 0
- Therefore, the assimilation-support masks are identical.

**OBSERVATION TYPE**:
SMAP NASA SPL3SMP_E (`_01`).

**OBSERVATION ERROR DEFINITION ($R$)**:
The observation error standard deviation is configured as a spatially constant value in `smap_pertattribs.txt`: `std = 0.04` $m^3/m^3$.
Thus, the observation error variance $R$ is a constant $0.0016$ $(m^3 m^{-3})^2$.
Both DA-CDF and DA-NoCDF use the exact same $R$ definition.

**XAI ROLE**:
Describes the model uncertainty in observation space before the update. Essential for calculating normalized innovation and understanding dynamic observation weighting.

**STATISTICS**:
Since the quantity represents a variance, values must be strictly nonnegative.
- **DA-CDF**: min: `0.0`, mean: `0.00196`, max: `0.0141`, p95: `0.00397`. Negative values: `0`.
- **DA-NoCDF**: min: `0.0`, mean: `0.00224`, max: `0.0189`, p95: `0.00423`. Negative values: `0`.
- The cross-experiment comparison shows that DA-NoCDF exhibits slightly higher ensemble spread (forecast variance) on average than DA-CDF. This variance depends entirely on assimilation feedbacks through the state integration; neither should be intrinsically considered "better".

**RELATION TO INNOVATION**:
For QC purposes, the correlation between absolute innovation and forecast variance was computed. The correlation is extremely weak (DA-CDF Spearman: 0.121, DA-NoCDF Spearman: 0.019), indicating that the magnitude of the model-observation mismatch is not strongly coupled to the model's internal ensemble spread at the time of observation.

## EnKF / Normalized Innovation

**SOURCE**:
`LIS_DA_EnKF_YYYYMMDDHHMM_innov.a01.d01.nc`

**RAW VARIABLE**:
`ninnov_01`

**DEFINITION**:
Normalized innovation represents the raw observation-model mismatch scaled by the total expected theoretical uncertainty. It is rigorously confirmed from source code (`enkf_Mod.F90` line 439) and independent numerical reconstruction to be exactly:
`normalized_innovation = innovation / sqrt(forecast_variance + R)`

**UNITS**:
Dimensionless (`1`). Both the numerator (innovation) and the denominator (standard deviation of total innovation variance) have units of $m^3/m^3$, canceling out perfectly.

**R VALUE**:
The observation error variance $R$ is confirmed to be $0.0016$ $(m^3 m^{-3})^2$, derived from the `std = 0.04` parameter in `smap_pertattribs.txt`. Because $R > 0$, the denominator is unconditionally strictly positive, guaranteeing numerical safety against divide-by-zero errors.

**SUPPORT**:
Finite values strictly align with `assimilation_update_mask`. There are exactly 0 mismatches between finite normalized innovation, finite raw innovation, and finite forecast variance across all 197 million combined 2016-2020 event-grid positions.

**TIME**:
Assimilation event (instantaneous, `YYYYMMDDHHMM`).

**CDF VS NoCDF**:
- **DA-CDF**: mean: `-0.218`, median: `-0.105`, std: `0.666`. Exceedance |ninnov| > 2: `2.6%`.
- **DA-NoCDF**: mean: `-0.093`, median: `-0.087`, std: `0.639`. Exceedance |ninnov| > 2: `1.5%`.
*Note*: The normalized innovation distributions are roughly centered near zero with variance $< 1$, typical for conservative DA configurations. Because DA-CDF normalizes against CDF-matched observations while DA-NoCDF normalizes against the non-CDF-matched observation representation used by that experiment, they evaluate fundamentally different representation spaces. A smaller normalized innovation variance does *not* intrinsically imply better assimilation skill.

**MISSING SEMANTICS**:
- Missing `normalized_innovation` strictly corresponds to missing `innovation` (no observation assimilated).
- `normalized_innovation = 0` strictly corresponds to `innovation = 0`.

**RECONSTRUCTION VALIDATION**:
Independent mathematical reconstruction of the normalized innovation field using the extracted interim `innovation`, `forecast_variance`, and the constant $R = 0.0016$ reproduced the raw LIS outputs with a worst-case full-period error of exactly `0.000e+00`.

**XAI ROLE**:
Normalized innovation serves as a critical XAI-Source diagnostic. While raw innovation measures the absolute magnitude of the observation-model mismatch, normalized innovation measures that mismatch *relative to the expected combined model and observation uncertainty*. This normalization is central to interpreting dynamic EnKF observation weighting.

## EnKF / Analysis Residual

**SOURCE**:
`LIS_DA_EnKF_YYYYMMDDHHMM_innov.a01.d01.nc`

**RAW VARIABLE**:
`analysis_residual_01`

**DEFINITION**:
The remaining mismatch in observation space *after* the assimilation step. It is derived from the final EnKF analysis ensemble:
`analysis_residual = observation - analysis_equivalent = y - H(x_a)`
Source-code inspection (`enkf_Mod.F90` line 541) confirms this is calculated by subtracting the mean of the updated ensemble observation-predictions from the unperturbed observation value.

**SIGN**:
- `> 0`: Assimilated observation is wetter than the analysis equivalent.
- `< 0`: Assimilated observation is drier than the analysis equivalent.
*(Note: For DA-CDF, $y$ is the CDF-matched observation. For DA-NoCDF, $y$ is the non-CDF-matched observation representation used by that experiment.)*

**UNITS**:
$m^3 m^{-3}$

**TIME**:
Assimilation event (instantaneous, `YYYYMMDDHHMM`).

**SUPPORT**:
Finite values strictly align with `assimilation_update_mask`. There are 0 mismatches between missing analysis residual and missing innovation across 2016-2020.

**CDF VS NoCDF & BEFORE/AFTER MISMATCH QC**:
- **DA-CDF**:
  - `mean |innovation|`: 0.0258
  - `mean |analysis_residual|`: 0.0132
  - **96.4%** of assimilated observations showed a reduced absolute mismatch after DA.
- **DA-NoCDF**:
  - `mean |innovation|`: 0.0270
  - `mean |analysis_residual|`: 0.0126
  - **98.4%** of assimilated observations showed a reduced absolute mismatch after DA.
*Note: The DA-NoCDF residual lives in the non-CDF-matched observation representation used by that experiment. Direct magnitude comparison against DA-CDF must account for this.*

**RELATION TO INNOVATION**:
The analysis residual is highly correlated with the pre-assimilation innovation (Spearman: `0.978` for DA-CDF, `0.984` for DA-NoCDF). Larger initial mismatches predictably leave larger remaining residuals. Conditioning by normalized innovation magnitude confirms this: for $|ninnov| \ge 2$, the median mismatch reduction is large ($\sim 0.04$ $m^3/m^3$), but larger initial normalized mismatches tend to retain larger absolute residuals after assimilation.

**RELATION TO INCREMENT**:
The assumption `analysis_residual == innovation - increment_signed` (which implies $H(x_a) - H(x_f) == x_{a,1} - x_{f,1}$) is **approximately valid but theoretically inexact**. Numerical tests over 2016-2020 show a mean absolute error of $\sim 4.5 \times 10^{-4}$ $m^3/m^3$, but a maximum absolute error up to $\sim 0.1$ $m^3/m^3$. The identity analysis_residual = innovation - Layer-1 increment is not exact in these outputs. The observation-space update H(x_a)-H(x_f) must therefore not be assumed identical to the stored Layer-1 state increment. The exact diagnostic/operator pathway should be traced before attributing the discrepancy to a specific mechanism.

**ZERO/MISSING SEMANTICS**:
- Missing values mean no observation was assimilated, identical to `innovation`.
- Exactly zero residuals (perfect analysis-observation agreement) are vanishingly rare ($\approx 0.0\%$) due to floating-point precision and EnKF variance maintenance. Missing values must *never* be replaced with zero.

**XAI ROLE**:
Analysis residual completes the XAI-Source diagnostic pathway:
1. `innovation`: Mismatch before assimilation.
2. `normalized_innovation`: Mismatch relative to expected uncertainty.
3. `increment`: Resulting model-state correction.
4. `analysis_residual`: Mismatch remaining after assimilation.

## EnKF / Daily Observation Frequency

**SOURCE**:
Derived from event-based EnKF innovation output.

**DERIVATION**:
Observation frequency is the number of assimilation events with a valid assimilated observation at the model grid cell falling within a UTC calendar day.
`observation_frequency(d, p) = sum(isfinite(innovation(event, p)))` over all events in day `d`.

**DAILY TIME INTERVAL**:
Full 1827-day sequence from `2016-01-01` to `2020-12-31`. Day $D$ corresponds precisely to the half-open interval $[D \text{ 00:00 UTC}, D+1 \text{ 00:00 UTC})$. Event times are mapped natively without applying any artificial LIS_HIST "-1 day" shift. This accurately models the physical timeframe of the assimilated observation and natively matches the canonical Noah-MP model day boundaries (which run 00:00 to 00:00 UTC).

**ASSIMILATION MASK & COUNT CONSERVATION**:
The valid assimilation support is defined rigorously as `isfinite(innovation)`. Across both DA-CDF and DA-NoCDF over all 5 years, the domain-total daily aggregated counts match the domain-total event-based finite counts perfectly (e.g., DA-CDF 2016: 345,488 valid event pixels = 345,488 aggregated daily valid pixels; difference exactly 0).

**LAND MASK**:
An independent, static land mask (derived from the valid canonical model SSM support) was applied to the daily arrays. Therefore:
- Valid land pixels with no assimilated observation during the day are explicitly `0`.
- Pixels outside the canonical land mask remain `NaN`.

**MISSING & ZERO SEMANTICS**:
- `observation_frequency = 0`: valid land, no assimilated observation that day.
- `observation_frequency = NaN`: outside canonical valid-land/model support.
The verified daily multiplicity result is `maximum observation_frequency = 1` for both experiments over 2016-2020. This confirms no valid land pixel receives more than one assimilated SMAP observation within the same UTC calendar day in these experiments. An important consequence is that future event-to-daily conversion of EnKF diagnostics does not require combining multiple valid events at a single pixel-day for this dataset.

**CDF VS NoCDF**:
- **DA-CDF**: Mean land coverage fraction per day is `8.4%`. 91.6% of valid land pixel-days have 0 observations.
- **DA-NoCDF**: Mean land coverage fraction per day is `25.6%`. 74.4% of valid land pixel-days have 0 observations.
DA-CDF exhibits substantially lower assimilation support than DA-NoCDF. This is consistent with differences introduced by the CDF-matching and associated DA/QC pathway, but the precise reason for individual rejected observations has not yet been isolated.

**2019 OUTAGE BEHAVIOR**:
The metric perfectly isolates the documented SMAP observation outage from 19 June to 23 July 2019. During the outage (19 June - 23 July 2019), the mean daily total of assimilated observations fell to exactly `0.0`. Before and after the outage, domain totals averaged $\sim 1,200 - 3,500$ depending on the experiment. These `0`s are valid zero-update days, not missing data.

**XAI ROLE**:
Observation frequency is the foundational support mask for all daily EnKF diagnostics. It enables an XAI model to robustly differentiate between:
- "No assimilation occurred here today" (`frequency = 0`)
- "An assimilation occurred here today" (`frequency = 1`)
This provides the discrete logical switch for XAI attribution, preventing models from interpreting 0-valued increments (no update) as a perfect 0-error state.

**STORAGE**:
`data/processed/daily_enkf/da_[no]cdf/observation_frequency/observation_frequency_YYYY.nc`

## EnKF / Daily Signed Analysis Increment

**SOURCE**:
Derived from the native event-based `increment_signed` NetCDF output, using `observation_frequency` to establish strict assimilation support.

**DERIVATION**:
- `daily_signed_increment(d, p)`: the unique valid native `increment_signed` assigned during UTC calendar day `d`.
- **MAX DAILY MULTIPLICITY = 1**: Verified exactly across all 2016-2020 valid land pixel-days. No single pixel received $>1$ valid update per day.
- **ZERO SEMANTICS**: If `observation_frequency == 0`, `daily_signed_increment = 0.0`. This precisely encodes "no DA correction occurred during that pixel-day". It must not be conflated with numerical NaN.
- **LAND MASK**: `NaN` is strictly reserved for grid cells outside the canonical valid-land/model support.

**TIME MAPPING**:
Native assimilation `event_time`s were cleanly floored to the UTC calendar day `[D 00:00 UTC, D+1 00:00 UTC)`. No time-shifting, averaging, or summing was necessary due to the unit multiplicity.

**VALUE CONSERVATION**:
The derivation preserves total update magnitudes exactly. The domain-total sum of all native valid event increments identically matches the sum of the daily pixel-day increments (e.g., DA-CDF 2016 absolute difference: $1.36 \times 10^{-12}$, reflecting only IEEE 754 float32 precision limits). The number of assigned daily updates matches the number of valid event innovations exactly.

**CDF VS NoCDF**:
Because `DA-CDF` has a fraction of valid pixel-days $\approx 8.4\%$ compared to `DA-NoCDF` $\approx 25.6\%$, the distribution unconditional on observation requires care.
- **Unconditional Mean**: Over all valid land days (including 0s for no-update), the net daily effect is near zero (DA-CDF: $-6.0 \times 10^{-4}$ m3/m3, DA-NoCDF: $-9.7 \times 10^{-4}$ m3/m3).
- **Conditional Mean**: Over assimilated pixel-days only, the DA correction is much larger and strongly skewed to drying (DA-CDF: $-7.2 \times 10^{-3}$ m3/m3, DA-NoCDF: $-3.8 \times 10^{-3}$ m3/m3).

**UNCONDITIONAL VS CONDITIONAL STATISTICS**:
The daily dataset represents a sparse time-series at each pixel. Descriptive statistics or aggregation must explicitly specify whether they include $0.0$ no-update days (`observation_frequency == 0`) or condition strictly on assimilated days (`observation_frequency == 1`).

**XAI ROLE**:
This is the foundational XAI-Source target variable representing the absolute state correction applied by EnKF.
- `> 0`: EnKF made Layer-1 soil moisture wetter.
- `< 0`: EnKF made Layer-1 soil moisture drier.
- `= 0` (where `observation_frequency == 0`): No finite native EnKF innovation diagnostic was mapped to this pixel-day.

**STORAGE**:
`data/processed/daily_enkf/da_[no]cdf/daily_signed_increment/daily_signed_increment_YYYY.nc`

## EnKF / Daily Absolute Analysis Increment

**SOURCE**:
Derived directly from the processed `daily_signed_increment`.

**DERIVATION**:
`daily_absolute_increment = abs(daily_signed_increment)`.
No thresholding, clipping, or standardizing is applied.

**UNITS**:
m3 m-3

**ZERO SEMANTICS**:
Because the dataset strictly possesses 0 zero-valued valid event increments, `daily_absolute_increment == 0` exactly corresponds to no assimilation on valid land.

**LAND MASK**:
`NaN` remains strictly reserved for grid cells outside the canonical valid-land/model support.

**TIME SUPPORT**:
Full daily time axis spanning 1,827 days from `2016-01-01` to `2020-12-31`. Day $D$ corresponds to the UTC calendar day.

**UNCONDITIONAL STATISTICS**:
Because the majority of valid land pixel-days receive no update (0.0), unconditional statistics describe the *domain-average daily correction magnitude including no-update pixel-days*.
- **DA-CDF**: Mean $\approx 0.0011$ m3 m-3 (91.6% zero)
- **DA-NoCDF**: Mean $\approx 0.0037$ m3 m-3 (74.4% zero)

**CONDITIONAL STATISTICS**:
When restricted to assimilated pixel-days only (`observation_frequency == 1`), the magnitude describes the correction size *conditional on an actual DA event*.
- **DA-CDF**: Mean $\approx 0.0129$ m3 m-3, median $\approx 0.0079$
- **DA-NoCDF**: Mean $\approx 0.0145$ m3 m-3, median $\approx 0.0100$
Interestingly, while DA-CDF's signed mean strongly skews negative (drying), its absolute correction magnitude is slightly smaller overall than DA-NoCDF's. DA-CDF shows a larger contrast between drying and wetting correction magnitudes than DA-NoCDF in these experiments.

**CDF VS NoCDF**:
DA-NoCDF possesses both a much wider assimilation support and slightly larger typical absolute updates conditionally. DA-NoCDF has a larger unconditional mean absolute increment because the unconditional statistic combines assimilation frequency and update magnitude. Differences in magnitude should not be used to conclude which assimilation is "better" without referencing independent state validation.

**XAI-SOURCE ROLE**:
Candidate PRIMARY TARGET for XAI models asking: "How strongly does SMAP assimilation modify surface soil moisture?"

**FUTURE SAMPLING STRATEGIES**:
Two distinct ML modeling approaches are possible for the modeling dataset:
- **Strategy A (All pixel-days)**: Uses the unconditional distribution. Explains where/when DA activity and magnitude occur jointly.
- **Strategy B (Assimilated pixel-days only)**: Uses the conditional distribution. Explains correction magnitude given an actual DA event.
The final XAI design may utilize both as complementary analyses.

**STORAGE**:
`data/processed/daily_enkf/da_[no]cdf/daily_absolute_increment/daily_absolute_increment_YYYY.nc`

## EnKF / Daily Innovation

**SOURCE**:
Derived directly from the validated native event-based `innovation`.

**DEFINITION**:
`assimilated observation minus forecast observation equivalent` ($y - H(x_f)$).

**SIGN**:
- `> 0`: Assimilated observation is wetter than the model forecast equivalent.
- `< 0`: Assimilated observation is drier than the model forecast equivalent.
- `= 0`: Exact observation-forecast agreement (rare but theoretically possible; exactly 0 for DA-CDF and 1 for DA-NoCDF in this dataset).

**UNITS**:
m3 m-3

**EVENT-TO-DAY MAPPING**:
Each valid event is uniquely mapped to its UTC calendar day without averaging or temporal shifting. Because maximum multiplicity is 1, no events overwrite each other.

**NO-ASSIMILATION = NaN**:
Unlike the increments, no-assimilation days are strictly `NaN`. Innovation does not exist when no observation was assimilated.

**LAND-MASK SEMANTICS**:
`NaN` exists for two distinct structural reasons: no assimilation on valid land, and outside valid-land/model support. These must be distinguished using the `observation_frequency` mask.

**COUNT & VALUE CONSERVATION**:
The mapping perfectly conserves the finite count and the value sum relative to the native event-based variables up to float32 precision limits.

**CDF VS NoCDF**:
DA-CDF uses the CDF-matched SMAP representation, while DA-NoCDF uses the non-CDF-matched observation representation used by that experiment. Thus, they cannot be interpreted as directly comparable independent model-skill metrics.

**RELATION TO DAILY INCREMENT**:
The relationship between daily innovation and daily signed increment remains remarkably strong (Pearson $\approx$ 0.91 to 0.95, Spearman $\approx$ 0.97 to 0.98) with a 100% sign agreement fraction, matching the validated event-space behavior.

**2019 OUTAGE**:
During the 19 June to 23 July 2019 SMAP outage, the daily innovation correctly maps to `NaN` everywhere on valid land. This explicitly contrasts with `daily_signed_increment` and `daily_absolute_increment`, which map to `0.0` over the same period.

**XAI-SOURCE ROLE**:
Candidate predictor representing the pre-analysis observation-model mismatch. Since it is only defined conditionally on assimilation, it naturally supports the future assimilation-conditional XAI analysis.

**PRE-ANALYSIS STATUS**:
**Data Leakage Note**: `daily_innovation` is a pre-analysis diagnostic and can be considered as a valid candidate explanatory variable for the increment. This contrasts with post-analysis residuals, which may contain downstream target information.

**STORAGE**:
`data/processed/daily_enkf/da_[no]cdf/daily_innovation/daily_innovation_YYYY.nc`

## EnKF / Daily Normalized Innovation

**SOURCE**:
Derived directly from the validated native event-based `normalized_innovation`.

**FORMULA**:
`normalized_innovation = innovation / sqrt(forecast_variance + R)`
where `R` is the observation error variance.

**UNITS**:
Dimensionless (`1`).

**R & S**:
`R = 0.0016 (m3 m-3)^2`
`S = forecast_variance + R` (the innovation variance). The denominator is `sqrt(S)`, which is the expected innovation standard deviation.

**EVENT-TO-DAY MAPPING**:
Unique finite event mapped to UTC calendar day without averaging. Because maximum multiplicity is 1, events are conserved exactly. The canonical daily calendar is complete over 1827 days; normalized innovation remains assimilation-conditional and is NaN on no-assimilation pixel-days.

**NaN SEMANTICS**:
`NaN` exists where no assimilation occurred (`observation_frequency == 0`) or outside canonical model support. Zero is never used for imputation.

**CDF VS NoCDF**:
DA-CDF uses the CDF-matched SMAP representation; DA-NoCDF uses the non-CDF-matched observation representation used by that experiment. The distributions differ substantially but a smaller magnitude does not intrinsically imply better DA skill.

**COUNT/VALUE CONSERVATION**:
Matches the exact number of finite assimilation events perfectly (DA-CDF: 2,456,233; DA-NoCDF: 7,507,641). The daily mapping exhibits 0 absolute value differences across all 10 million matched samples.

**FORMULA RECONSTRUCTION**:
An independent reconstruction using matched EVENT-BASED samples verified `innovation / sqrt(forecast_variance + 0.0016)` yields bit-for-bit exact identity (`Max abs diff = 0.0`) relative to the stored native `normalized_innovation`.

**EXCEEDANCE SEMANTICS**:
Magnitude thresholds:
- $|NI| > 1$: $\approx 10.3\%$ (CDF), $10.6\%$ (NoCDF)
- $|NI| > 2$: $\approx 2.66\%$ (CDF), $1.51\%$ (NoCDF)
- $|NI| > 3$: $\approx 0.68\%$ (CDF), $0.18\%$ (NoCDF)
These are strictly descriptive standardized thresholds and must not automatically label observations as "bad" without additional diagnostics.

**XAI ROLE**:
Candidate predictor representing pre-analysis mismatch standardized by the expected innovation uncertainty. Tests whether scaled observation-model mismatch relates to the final correction magnitude (`daily_absolute_increment`). In these descriptive QC relationships, absolute dimensional innovation shows a higher correlation with absolute increment than absolute normalized innovation. This result is retained for later XAI feature-design analysis and is not used here for feature selection.

**PRE-ANALYSIS STATUS**:
**Data Leakage Note**: `daily_normalized_innovation` is exclusively pre-analysis and is safely computable before the updated soil-moisture state is obtained. 

**FEATURE REDUNDANCY NOTE**:
Because `daily_normalized_innovation` explicitly combines `daily_innovation`, `daily_forecast_variance`, and `R`, XAI feature selection must carefully assess multicollinearity and redundancy if multiple terms of the analytical formula are presented simultaneously.

**STORAGE**:
`data/processed/daily_enkf/da_[no]cdf/daily_normalized_innovation/daily_normalized_innovation_YYYY.nc`

## EnKF / Daily Forecast Variance

**SOURCE**:
Derived directly from the validated native event-based `forecast_variance`.

**RAW VARIABLE NAME**:
`forecast_sigma_01`

**LIS SOURCE-CODE MEANING**:
Despite the raw LIS variable name (`forecast_sigma_01`), source code inspection demonstrates the stored quantity is exactly `HPH^T` (variance), not standard deviation.

**HPH^T DEFINITION**:
`HPH^T`, the forecast-error variance projected into observation space. 

**VARIANCE VS STANDARD DEVIATION**:
The raw variable represents *variance*. The expected innovation standard deviation used as the denominator for normalized innovation is `sqrt(HPH^T + R)`.

**UNITS**:
`(m3 m-3)^2`

**EVENT-TO-DAY MAPPING**:
Unique finite event mapped to UTC calendar day without averaging. Because maximum multiplicity is 1, events are conserved exactly. The canonical daily calendar is complete over 1827 days; forecast variance remains assimilation-conditional and is NaN on no-assimilation pixel-days.

**NaN SEMANTICS**:
`NaN` exists where no assimilation occurred (`observation_frequency == 0`) or outside canonical model support. Zero is never used for imputation.

**ZERO SEMANTICS**:
An exact zero represents zero stored forecast observation-space variance at numerical precision. (Found in 7 CDF samples and 5 NoCDF samples). `forecast_variance > 0` must NOT be used as an assimilation-support criterion. 

**COUNT/VALUE CONSERVATION**:
Matches the exact number of finite assimilation events perfectly (DA-CDF: 2,456,233; DA-NoCDF: 7,507,641). The daily mapping exhibits 0 absolute value differences across all matched samples.

**RELATION TO S**:
`S = daily_forecast_variance + R` (where `R = 0.0016 (m3 m-3)^2`). `S` is the innovation variance.

**RELATION TO NORMALIZED INNOVATION**:
Independent reconstruction using matched event-based samples verified `daily_innovation / sqrt(daily_forecast_variance + 0.0016)` yields bit-for-bit exact identity (`Max abs diff = 0.0`) relative to `daily_normalized_innovation`. 
Descriptively, there is a weak negative rank correlation between daily forecast variance and absolute normalized innovation (Spearman: ~ -0.02 for DA-CDF, ~ -0.12 for DA-NoCDF).

**QUARTILE DIAGNOSTIC**:
Across forecast-variance quartiles, absolute normalized innovation is non-monotonic. In both experiments it decreases toward the middle/high-middle variance classes and increases again in Q4. DA-NoCDF has its largest median |NI| in Q1, whereas DA-CDF has comparable Q1 and Q4 values, with Q4 slightly larger.
Median |innovation| is non-monotonic across Q1-Q4 in both experiments, although Q4 has the largest median value.
It is valid to state descriptively that median absolute increment generally increases across forecast-variance quartiles:
- DA-CDF: 0.002420, 0.008020, 0.008846, 0.014522
- DA-NoCDF: 0.006598, 0.009068, 0.010640, 0.015408

**XAI ROLE**:
Candidate pre-analysis observation-space forecast-variance predictor. Conceptually models the forecast uncertainty context prior to assimilation.

**PRE-ANALYSIS STATUS**:
**Data Leakage Note**: `daily_forecast_variance` is a pre-analysis DA diagnostic available before the analysis state is generated. It is a legitimate explanatory variable for the increment.

**FEATURE-DEPENDENCE WARNING**:
Because `daily_normalized_innovation` is mathematically derived from `daily_innovation`, `daily_forecast_variance`, and constant `R`, using all three in the same ML model introduces deterministic feature dependence. XAI feature selection must carefully assess multicollinearity.

**STORAGE**:
`data/processed/daily_enkf/da_[no]cdf/daily_forecast_variance/daily_forecast_variance_YYYY.nc`

## EnKF / Daily Analysis Residual

**SOURCE**:
Derived directly from the validated native event-based `analysis_residual`.

**DEFINITION**:
`y - H(x_a)` (Assimilated observation minus analysis equivalent in observation space).

**SIGN**:
- `> 0`: assimilated observation is wetter than the analysis equivalent
- `< 0`: assimilated observation is drier than the analysis equivalent
- `= 0`: exact agreement at numerical precision

**UNITS**:
`m3 m-3`

**EVENT-TO-DAY MAPPING**:
Unique valid event mapped to UTC calendar day without averaging (maximum multiplicity is 1). The canonical UTC daily calendar is complete over 1827 days; daily_analysis_residual remains assimilation-conditional and is NaN on no-assimilation pixel-days.

**NaN SEMANTICS**:
`NaN` exists where no assimilation occurred (`observation_frequency == 0`) or outside canonical model support. Zero is NOT used to mean no assimilation.

**CDF VS NoCDF**:
DA-CDF uses the CDF-matched observation representation. DA-NoCDF uses the non-CDF-matched observation representation used by that experiment. Residuals between the two experiments should NOT be interpreted directly as independent skill metrics; smaller residual does not causally equate to a superior experiment without independent verification.

**COUNT/VALUE CONSERVATION**:
Matches the exact number of finite assimilation events perfectly (DA-CDF: 2,456,233; DA-NoCDF: 7,507,641). The daily mapping exhibits 0 absolute value differences across all matched samples.

**BEFORE VS AFTER MISMATCH**:
Observation-space mismatch is typically reduced after assimilation:
- DA-CDF: reduced in ~96.36% of samples. (mean |before| = 0.0258, mean |after| = 0.0132)
- DA-NoCDF: reduced in ~98.41% of samples. (mean |before| = 0.0270, mean |after| = 0.0126)

**MISMATCH REDUCTION**:
`|daily_innovation| - |daily_analysis_residual|`
- DA-CDF mean reduction: 0.0126 m3 m-3
- DA-NoCDF mean reduction: 0.0144 m3 m-3

**OBSERVATION-SPACE UPDATE**:
`daily_innovation - daily_analysis_residual` (Algebraically equal to `H(x_a) - H(x_f)`). This represents the actual analysis change in observation space.
- DA-CDF mean: -0.0067
- DA-NoCDF mean: -0.0035

**RELATION TO STATE INCREMENT**:
The observation-space update correlates very strongly with the `daily_signed_increment` (Spearman ~ 0.99 for both experiments), but it is NOT identical (RMSE ~ 0.001 - 0.0014). The analysis residual is strictly `y - H(x_a)`.

**2019 OUTAGE**:
During the documented SMAP observation outage from 19 June to 23 July 2019, `observation_frequency = 0` and `daily_analysis_residual = NaN` universally across valid land. This contrasts with the daily increment which is legitimately 0 on no-assimilation days.

**ZERO SEMANTICS**:
Exact finite residual zeros exist but are very rare (DA-CDF: 2 exact zeros; DA-NoCDF: 2 exact zeros), meaning observation and analysis equivalent agree exactly at stored numerical precision. 

**POST-ANALYSIS STATUS / XAI LEAKAGE WARNING**:
`daily_analysis_residual` is a post-analysis diagnostic. For an XAI model explaining `daily_signed_increment` or `daily_absolute_increment`, `daily_analysis_residual` is excluded from the pre-analysis predictor set because it contains information generated after the update. It may still be used as a post-analysis audit variable, secondary response, or diagnostic outcome.

**SPATIAL DIAGNOSTICS**:
The spatial diagnostics show structured variability, with no obvious rigid row-wise striping comparable to the previously diagnosed flux pattern.

**STORAGE**:
`data/processed/daily_enkf/da_[no]cdf/daily_analysis_residual/daily_analysis_residual_YYYY.nc`

# Static Predictors

## Elevation

**SOURCE**:
Extracted from static LIS input: `lis_input_NorthMor_5km.nc`.

**RAW VARIABLE**:
`ELEVATION` is selected as the canonical elevation source based on its metadata (`GTOPO30 (Native) elevation`), metre units, grid dimensions, and spatial field. `ELEVFGRD` was inspected separately and is not used as the canonical elevation predictor. `ELEVFGRD` represents "Elevation Area Fraction" with dimensionless units ("-"), consisting entirely of values equal to 1.0.

**UNITS**:
`m` (meters).

**GRID**:
Native spatial support is exactly aligned with the canonical Noah-MP model grid (Max coordinate difference = 0.0). No regridding or rotation is required. Latitude and longitude are both monotonically increasing.

**LAND MASK**:
The processed mask is aligned with the established canonical Noah-MP valid-land mask (16,030 valid pixels, 5,871 masked pixels; 26.8% masked fraction). Missing values inside canonical support count: 0.

**RAW SOURCE STATISTICS (Unmasked)**:
Before masking, the native `ELEVATION` array inherently matches the canonical mask exactly:
- Finite count: 16,030
- Missing count: 5,871
- Min: 3.0556
- Max: 3549.8057
- Mean: 927.0696
- Median: 833.9166
- Percentiles: p01 = 26.611, p05 = 129.510, p25 = 534.868, p75 = 1254.028, p95 = 1979.960, p99 = 2616.527

**VALUE PRESERVATION**:
Source valid land values are preserved exactly (0 differences).
- Min: 3.06 m (at 35.6 N, -5.3 E)
- Max: 3549.81 m (at 31.5 N, -6.45 E)
- Median: 833.92 m

**NO TIME DIMENSION**:
Elevation is static and does NOT contain a time dimension. It should only be joined/broadcast to pixel-days during the final XAI table construction to avoid unnecessary data replication.

**XAI ROLE**:
`elevation` is a static physiographic predictor. Elevation is a static pre-existing physiographic variable and contains no post-analysis information. It is therefore eligible as a candidate explanatory predictor, subject to the spatial cross-validation design used later.

**OUTPUT PATH**:
`data/processed/static/elevation/elevation.nc`

## Soil Texture

**SOURCE**:
Extracted from static LIS input: `lis_input_NorthMor_5km.nc`.

**RAW VARIABLE**:
`TEXTURE` (Standard name: `(NCAR) STATSGO+FAO blended soil texture map`).

**VARIABLE STRUCTURE**:
A stack of 16 class fractions with dimensions `(soiltypes, north_south, east_west)`. 

**CLASS/BIN SEMANTICS**:
The source provides a 16-element `soiltypes` dimension without explicit semantic class identifiers. Canonical `texture_class` IDs are assigned for indexing only. Mapping: source positional index 0 -> canonical `texture_class` 1, ..., source positional index 15 -> canonical `texture_class` 16.

**UNITS**:
Fraction `[0,1]`.

**GRID**:
Native spatial support exactly matches the canonical Noah-MP grid (Max coordinate difference = 0.0). No regridding is required.

**LAND MASK**:
The canonical valid-land mask is applied exactly (16,030 valid pixels, 5,871 masked pixels). Missing values inside canonical support count: 0.

**FRACTION CONVENTION**:
Fractions are stored inherently as `[0,1]`. Values were not modified, clipped, or renormalized. No fractions were < 0 or > 1.

**COMPOSITION SUM**:
The sum of the 16 fractions is mathematically 1.0 (maximum \|sum - 1\| = 0.0) for every valid land pixel.

**MIXTURE STRUCTURE**:
The representation is functionally one-hot soil-texture class fractions. Exactly 100% of valid land pixels (16,030) contain exactly 1 active class with a maximum fraction exactly equal to 1.0. The spatial QC shows no obvious missing stripes, duplicated rows/columns, checkerboard artifacts, or grid-orientation errors.

**DOMINANT-CLASS QC**:
Because it is perfectly one-hot, the dominant class perfectly captures all information. Classes 1, 3, 4, 6, 7, 9, 12 are present. Class 6 is the overwhelming dominant class (75.15%). No ties occurred. The sum over all 16 classes is perfectly conserved at 16,030 valid land pixels.

**VALUE PRESERVATION**:
Source valid land fractions are preserved exactly (mean absolute difference = 0.0, 0 exactly unequal pixels).

**NO TIME DIMENSION**:
Soil texture is static and contains no time dimension. It is broadcasted dynamically during final XAI table construction.

**COMPOSITIONAL DEPENDENCE & XAI REPRESENTATION**:
In this dataset the fractions are exactly one-hot, so the canonical 16-component representation contains the same categorical information as a single soil-texture class label. 
Because `sum(texture fractions) = 1`, using all 16 fractions directly as independent linear predictors creates deterministic redundancy. The canonical variable preserves all 16 fractions.
For future XAI design, note:
- integer class coding may introduce artificial ordinality in models that treat integers as continuous;
- one-hot representation avoids that issue;
- models with native categorical handling may instead use the class label;
- for linear models, all 16 one-hot components plus an intercept are exactly redundant, so one level would normally be omitted.

**XAI ROLE**:
`soil_texture_fraction` is a static pre-existing land-surface property and contains no post-analysis information. It is eligible as a candidate contextual predictor for explaining spatial heterogeneity, subject to later spatial cross-validation design.

**OUTPUT PATH**:
`data/processed/static/soil_texture/soil_texture_fraction.nc`

## Land Cover

**SOURCE**:
Extracted from static LIS input: `lis_input_NorthMor_5km.nc`.

**RAW VARIABLE**:
`LANDCOVER` (Standard name: `MODIS-IGBP (NCEP-modified) landcover map`).

**VARIABLE STRUCTURE**:
A stack of 20 class fractions with dimensions `(sfctypes, north_south, east_west)`. 

**CLASS-ID PROVENANCE**:
The source contains a 20-element `sfctypes` dimension without an explicit class-coordinate variable. Canonical `land_cover_class` IDs 1...20 are assigned for indexing only, with mapping source positional index 0 -> canonical `land_cover_class` 1, ..., source positional index 19 -> canonical `land_cover_class` 20.

**CLASS LABELS IF AVAILABLE**:
No explicit semantic class names are provided in the NetCDF beyond the global `MODIS-IGBP (NCEP-modified)` designation. Therefore, canonical numeric identifiers (1-20) are strictly retained without inventing semantic names.

**UNITS**:
Fraction `[0,1]`.

**GRID**:
Native spatial support exactly matches the canonical Noah-MP grid (Max coordinate difference = 0.0). No regridding is required.

**LAND MASK**:
The canonical valid-land mask is applied exactly (16,030 valid pixels, 5,871 masked pixels). Missing values inside canonical support count: 0.

**FRACTION CONVENTION**:
Values are natively fractions in `[0,1]`. Values were not modified, clipped, or renormalized. No fractions were < 0 or > 1.

**COMPOSITION SUM**:
The processed fractions close to unity at float32 precision, with maximum |sum - 1| = 1.19e-07 and zero pixels exceeding 1e-6. The native source sums ranged from ~0.99999994 to ~1.0000001.

**MIXTURE / ONE-HOT STRUCTURE**:
Unlike soil texture, LANDCOVER contains substantial sub-grid fractional mixing in the LIS input representation. Out of 16,030 valid land pixels, the number of active classes per pixel is:
- exactly 1 active class: 3,769
- exactly 2 active classes: 5,486
- exactly 3 active classes: 3,175
- >3 active classes: 3,600
These counts sum exactly to 16,030. The spatial QC shows heterogeneous fractional land-cover patterns, with no obvious missing stripes, duplicated rows/columns, checkerboard artifacts, transposition, or grid-orientation errors.

**DOMINANT-CLASS QC**:
Classes 7 (35.16%) and 16 (52.09%) are the most dominant. 
Dominant maximum fractions have the following distribution:
- max_fraction == 1.0: 3,769
- max_fraction >= 0.95: 4,647
- max_fraction >= 0.90: 6,014
- max_fraction >= 0.75: 9,391
- max_fraction >= 0.50: 14,465
- max_fraction < 0.50: 1,565
Statistics of the dominant fraction: min: 0.1429, mean: 0.7740, median: 0.8056, p05: 0.4167, p25: 0.6111, p75: 0.9722, p95: 1.0000.
There are exactly 241 pixels with tied maximum fractions. For QC-only dominant-class summaries, ties are resolved deterministically by the first maximum along source positional order, corresponding to the lowest canonical `land_cover_class` ID among tied components. Dominant-class counts depend on this QC tie-breaking convention for those 241 pixels.

**ZERO-VARIANCE COMPONENTS**:
Classes 15, 17, 18, 19, and 20 are exactly zero on all valid land pixels. These components have zero variance over the current valid-land domain and therefore provide no variation for model fitting. They should be filtered or otherwise handled during feature-matrix construction according to the modeling pipeline.

**VALUE PRESERVATION**:
Source valid land fractions are preserved exactly (mean absolute difference = 0.0, 0 exactly unequal pixels).

**NO TIME DIMENSION**:
Land cover is static and contains no time dimension. It will be joined by spatial index during final XAI table construction.

**COMPOSITIONAL DEPENDENCE & IMPORTANT XAI NOTE**:
Because `sum(class fractions) = 1`, the 20 components are compositionally constrained. Using all 20 fractions directly as independent linear predictors creates deterministic redundancy. The canonical variable preserves all 20 fractions.
Crucially, LANDCOVER differs fundamentally from TEXTURE. TEXTURE is an exact one-hot representation with no sub-grid mixing. LANDCOVER represents a genuine fractional mixture; only 23.51% of valid land pixels have exactly one active class, and many contain multiple active classes. Therefore, the canonical fractional representation retains information that would be lost by reducing LANDCOVER to only the dominant class.

**XAI ROLE**:
`land_cover_fraction` is a static pre-existing land-surface property and contains no post-analysis information. It is eligible as a candidate contextual predictor for explaining spatial heterogeneity, subject to later spatial cross-validation design.

**IRRIGATION INVENTORY**:
During inventory, `IRRIGFRAC` was identified (standard_name = "User Derived Irrig gridcell fraction"). It has not been preprocessed or merged with land cover in this pipeline.

**OUTPUT PATH**:
`data/processed/static/land_cover/land_cover_fraction.nc`

## Irrigation Fraction Audit

**SOURCE**:
`lis_input_NorthMor_5km.nc`

**RAW VARIABLE**:
`IRRIGFRAC`

**METADATA**:
- `standard_name`: "User Derived Irrig gridcell fraction"
- `units`: "-"

**GRID**:
Native spatial support exactly matches the canonical Noah-MP grid (Max coordinate difference = 0.0).

**LAND MASK**:
The canonical valid-land mask was explicitly applied for the audit (16,030 valid land pixels).

**VALUE DISTRIBUTION**:
Over all 16,030 valid land pixels, the variable is exactly 0.0.
- Count > 0: 0
- Count == 0: 16,030

**ZERO-VARIANCE STATUS**:
`IRRIGFRAC` has zero variance over the current valid-land domain. There is exactly 1 unique finite value (0.0) on valid land.

**EXPERIMENT CONFIGURATION**:
An exhaustive census of LIS configuration files was conducted across all three experiments (`OPL_noirr_2016_2020`, `DA_nocdf_noirr_2016_2020`, `DA_cdf_noirr_2016_2020`). Exactly 60 `.config` files were inspected per experiment (180 total). Every file was checked for the following keys, with 0 missing and 0 mismatches:
- `Irrigation scheme:` (180 files matched exactly `"none"`)
- `Noah-MP.4.0.1 crop model option:` (180 files matched exactly `0  # Irrigation OFF`)
No configuration file disagreed with these settings.

**STATIC-FIELD VS PROCESS-ACTIVATION DISTINCTION**:
There are two distinct and independent findings:
1. Static input: `IRRIGFRAC = 0` everywhere on canonical valid land.
2. Process configuration: irrigation is disabled in the current Noah-MP experiments.
Neither statement is logically inferred solely from the other; both were independently verified.

**CURRENT XAI ELIGIBILITY**:
`IRRIGFRAC` is constant zero over the current valid-land domain and therefore contains no sample-to-sample variation for the current modeling dataset. It is excluded from the current feature matrix due to zero variance.

**FUTURE IRRIGATION-AWARE RELEVANCE**:
Future XAI experiments that contrast irrigation-ON vs irrigation-OFF configurations may require revisiting this dataset or establishing a dedicated irrigation-aware predictor block. For the current experiments, it is strictly excluded.

## Transfer Targets / Delta RZSM

**SOURCE PRODUCTS**:
Derived exclusively from validated canonical RZSM targets:
- `data/processed/daily_model/opl/rzsm/rzsm_YYYY.nc`
- `data/processed/daily_model/da_cdf/rzsm/rzsm_YYYY.nc`
- `data/processed/daily_model/da_nocdf/rzsm/rzsm_YYYY.nc`

**DEFINITION**:
The daily 24-h-mean DA-minus-OPL root-zone soil-moisture difference target:
`delta_rzsm = daily 24-h-mean RZSM_DA - RZSM_OPL`

**SIGN**:
- `> 0`: DA daily-mean RZSM is wetter than OPL
- `< 0`: DA daily-mean RZSM is drier than OPL
- `= 0`: Equality at stored numerical precision.

**UNITS**:
$m^3 m^{-3}$

**ROOT-ZONE DEPTH**:
0-100 cm (derived from Noah-MP Layers 1-3). Layer 4 is explicitly excluded.

**GRID/TIME IDENTITY**:
Exact coordinate equality (max diff = 0.0) between OPL and DA experiments was verified prior to subtraction for all annual arrays.

**MASK**:
Maintains the exact canonical model valid-land mask (16,030 valid pixels). Missing values (`NaN`) on valid land count is exactly 0.

**ALL-DAY SUPPORT**:
Support is the complete canonical model calendar (1,827 days, 2016-01-01 through 2020-12-31). `delta_rzsm` remains fully defined on no-assimilation pixel-days whenever model RZSM exists.

**DIFFERENCE FROM ENKF INCREMENT**:
`delta_rzsm` is a daily model-state difference, NOT an instantaneous EnKF event diagnostic. It reflects accumulated and persistent differences from previous updates and subsequent Noah-MP dynamics, rather than just the effect of a single day's assimilation event. The correlations are modest in these descriptive comparisons (Pearson $\sim 0.07 - 0.28$), proving it is not a mere renaming of the increment.

**NO-ASSIMILATION PERSISTENCE**:
On valid-land pixel-days where no assimilation occurred (`observation_frequency == 0`), `delta_rzsm` continues to persist robustly. >99.9% of these no-assimilation days maintain a persistent absolute difference `> 1e-6` from OPL. This demonstrates that the DA-OPL RZSM difference is not restricted to same-day assimilation support and is consistent with persistence of the altered DA trajectory between assimilation events.

**2019 OUTAGE BEHAVIOR**:
During the SMAP observation outage (19 June - 23 July 2019), `observation_frequency` was zero, yet `delta_rzsm` remained fully populated and finite. This reflects persistent DA-OPL trajectory differences during a documented period without assimilated SMAP observations (e.g., >97% of valid pixels maintained an absolute difference `> 1e-4`), reflecting memory rather than new assimilation updates.

**CDF VS NOCDF CAUTION**:
The two experiments differ in observation representation, assimilation support frequency, and DA trajectory. Therefore, raw `delta_rzsm` differences between CDF and NoCDF conflate multiple aspects of the DA configuration. They should not be used to directly rank one experiment as "better" than the other.

**XAI TRANSFER ROLE**:
`delta_rzsm` is a Transfer block target describing the propagation of the assimilation-induced model trajectory into the 0-100 cm root zone. For future predictive models, variables mathematically containing the target or future information must be excluded to prevent leakage.

**OUTPUT PATH**:
- `data/processed/transfer/da_cdf/delta_rzsm/delta_rzsm_YYYY.nc`
- `data/processed/transfer/da_nocdf/delta_rzsm/delta_rzsm_YYYY.nc`

## Transfer Targets / Delta ET

**SOURCE PRODUCTS**:
Derived exclusively from validated canonical ET targets:
- `data/interim/noahmp/opl/et/et_YYYY.nc`
- `data/interim/noahmp/da_cdf/et/et_YYYY.nc`
- `data/interim/noahmp/da_nocdf/et/et_YYYY.nc`

**DEFINITION**:
The daily DA-minus-OPL evapotranspiration difference target:
`delta_et = et_DA - et_OPL`

**SIGN**:
- `> 0`: DA experiment has higher daily-mean ET than OPL
- `< 0`: DA experiment has lower daily-mean ET than OPL
- `= 0`: DA and OPL ET agree at stored numerical precision.

**UNITS**:
`mm/day`

**24-H MEAN FLUX SEMANTICS**:
Canonical daily ET is derived from the 24-h mean Noah-MP Evap_tavg flux using Evap_tavg * 86400 and expressed in mm/day. `delta_et` accordingly represents the daily DA-minus-OPL evapotranspiration difference derived from the corresponding 24-h mean flux products.

**GRID/TIME SUPPORT**:
Exact coordinate equality (max diff = 0.0) between OPL and DA experiments was verified prior to subtraction for all annual arrays.

**NEGATIVE ET PRESERVATION**:
The upstream ET preprocessing retained original negative flux values without clipping or converting to NaN. These negative values are faithfully preserved and propagated into `delta_et`.

**ALL-DAY SUPPORT**:
Support is the complete canonical model calendar (1,827 days, 2016-01-01 through 2020-12-31). `delta_et` is defined on the DAILY MODEL support, not just on assimilation-event pixel-days.

**ASSIMILATION VS NO-ASSIMILATION QC**:
On no-assimilation days (`observation_frequency == 0`), DA-minus-OPL flux differences persistently occur outside same-day assimilation support. This reflects the difference between the complete DA experiment trajectory and the OPL trajectory, rather than an instantaneous assimilation correction.

**OUTAGE BEHAVIOR**:
During the SMAP observation outage (19 June - 23 July 2019), `observation_frequency` was zero, yet `delta_et` remains populated with persistent DA-minus-OPL ET differences during a documented period without assimilated SMAP observations.

**RELATION TO DELTA_RZSM**:
Correlations are descriptive comparisons. `delta_et` and `delta_rzsm` exhibit expected statistical relationships, but this does not imply unique causality from individual assimilation events.

**RELATION TO SURFACE INCREMENT**:
The relationship between `delta_et` and the instantaneous EnKF Layer-1 surface increment is weak/modest, as they represent different stages (instantaneous EnKF correction vs daily model ET flux difference).

**ROW-WISE NUMERICAL STRUCTURE**:
A critical numerical diagnostic: `delta_et` exhibits a known row-wise numerical structure (alternating magnitudes along latitude rows). This row-wise structure is inherited from the DA model outputs and was previously verified in the raw LIS flux diagnostics; it is not introduced by `delta_et` preprocessing (see `docs/preprocessing/model_diagnostics.md`).

**CDF VS NOCDF CAUTION**:
The two experiments differ in observation representation, assimilation support frequency, and DA trajectory. Descriptive comparisons should not be used to rank one experiment as "better" or "worse" than the other based solely on raw `delta_et`.

**XAI TRANSFER ROLE**:
`delta_et` is a DA-minus-OPL Transfer response describing the evapotranspiration difference associated with the DA experiment trajectory. Conceptually: DA trajectory -> altered land states -> altered daily ET flux. This represents a difference between complete DA and OPL experiment trajectories, not a pure causal SMAP-assimilation effect.

**TARGET-TIMING WARNING**:
For future `delta_et` predictive models, predictor timing must be explicitly defined. Future information (e.g., same-day post-analysis variables, future RZSM, future ET, analysis residual) MUST NOT be used automatically as predictors.

**OUTPUT PATH**:
- `data/processed/transfer/da_cdf/delta_et/delta_et_YYYY.nc`
- `data/processed/transfer/da_nocdf/delta_et/delta_et_YYYY.nc`

## Transfer Targets / Delta Surface Runoff

**SOURCE PRODUCTS**:
Derived exclusively from validated canonical surface runoff targets:
- `data/interim/noahmp/opl/surface_runoff/surface_runoff_YYYY.nc`
- `data/interim/noahmp/da_cdf/surface_runoff/surface_runoff_YYYY.nc`
- `data/interim/noahmp/da_nocdf/surface_runoff/surface_runoff_YYYY.nc`

**DEFINITION**:
The daily DA-minus-OPL surface-runoff difference target:
`delta_surface_runoff = surface_runoff_DA - surface_runoff_OPL`

**SIGN**:
- `> 0`: DA experiment has greater daily surface runoff than OPL
- `< 0`: DA experiment has lower daily surface runoff than OPL
- `= 0`: DA and OPL surface runoff are equal at stored numerical precision.
(Note: `delta_surface_runoff` can be negative even though each individual surface-runoff field is non-negative).

**UNITS**:
`mm/day`

**24-H FLUX SEMANTICS**:
Canonical surface runoff is the daily surface-runoff amount/rate-equivalent derived from the 24-h mean Qs_tavg flux and expressed in mm/day. `delta_surface_runoff` accordingly represents the daily difference between the two experiment trajectories.

**GRID/TIME SUPPORT**:
Exact coordinate equality (max diff = 0.0) between OPL and DA experiments was verified prior to subtraction for all annual arrays.

**SOURCE ZERO STRUCTURE**:
Surface runoff is strongly zero-inflated (the majority of valid model land pixel-days are exactly 0.0).

**ALL-DAY SUPPORT**:
Support is the complete canonical model calendar (1,827 days, 2016-01-01 through 2020-12-31). `delta_surface_runoff` is defined on the DAILY MODEL support, not just on assimilation-event pixel-days.

**RUNOFF-ACTIVE SUPPORT**:
Runoff-active subset is defined where `(surface_runoff_OPL > 0) OR (surface_runoff_DA > 0)`.
*Caveat*: If tiny positive floating-point/model runoff values are widespread, then `runoff_active` may approach 100% even when hydrologically meaningful surface runoff is extremely small. Therefore, `runoff_active` is a numerical non-zero support diagnostic, not automatically a hydrologically significant runoff-event mask.

**ZERO-DELTA DECOMPOSITION**:
A large mass of exact zeros exists in `delta_surface_runoff`. These correspond primarily to days where both OPL and DA surface runoff are exactly zero, and a small minority where both are non-zero but perfectly equal.

**ASSIMILATION / NO-ASSIMILATION QC**:
On no-assimilation days (`observation_frequency == 0`), DA-minus-OPL runoff differences can still be non-zero due to persistence. The target represents a difference between complete DA and OPL trajectories, not a pure causal SMAP-assimilation effect.

**OUTAGE BEHAVIOR**:
DA-minus-OPL runoff differences during the documented period without assimilated SMAP observations (19 June - 23 July 2019) reflect the behavior of the DA-trajectory relative to OPL in a season generally dominated by no-runoff.

**RELATION TO DELTA_RZSM**:
Correlations are descriptive comparisons. Associations between `delta_rzsm` and `delta_surface_runoff` do not establish that the root-zone response exclusively causes the runoff response.

**RELATION TO DELTA_ET**:
Correlations between `delta_et` and `delta_surface_runoff` are descriptive associations only.

**RELATION TO SURFACE INCREMENT**:
The relationship between `delta_surface_runoff` and the EnKF Layer-1 surface increment is assessed descriptively on the subset of runoff-active days to prevent zero-dominated suppression of correlation signals.

**SEASONAL BEHAVIOR**:
The relative frequency and magnitude of active-runoff responses vary strongly by season, being generally highest in DJF/MAM and minimal in JJA.

**ROW-WISE NUMERICAL STRUCTURE**:
A critical numerical diagnostic: `delta_surface_runoff` preserves a row-dependent numerical structure. This structure is inherited from the DA runoff outputs and is consistent with the implementation-dependent numerical structure previously documented in the raw LIS flux diagnostics.

**CDF VS NOCDF CAUTION**:
The DA experiments differ from OPL in observation representation, assimilation frequency, DA trajectory, and potentially perturbed forcing. Therefore, `delta_surface_runoff` raw amplitudes should not be used to rank experiments against each other.

**XAI TRANSFER ROLE**:
`delta_surface_runoff` is a Transfer target describing the surface-runoff flux response associated with the DA experiment trajectory. Conceptually: altered DA experiment trajectory -> altered land-state evolution -> altered surface runoff.

**TIMING / LEAKAGE CAUTION**:
For future predictive models, predictor timing must be explicitly defined. Future model states, future runoff, or same-day information generated after the target interval MUST NOT be used automatically as predictors.

**OUTPUT PATH**:
- `data/processed/transfer/da_cdf/delta_surface_runoff/delta_surface_runoff_YYYY.nc`
- `data/processed/transfer/da_nocdf/delta_surface_runoff/delta_surface_runoff_YYYY.nc`

## Transfer Targets / Delta Baseflow

**SOURCE PRODUCTS**:
Derived exclusively from validated canonical baseflow targets:
- `data/interim/noahmp/opl/baseflow/baseflow_YYYY.nc`
- `data/interim/noahmp/da_cdf/baseflow/baseflow_YYYY.nc`
- `data/interim/noahmp/da_nocdf/baseflow/baseflow_YYYY.nc`

**Qsb_tavg PROVENANCE**:
The canonical baseflow target is derived directly from the Noah-MP Qsb_tavg model output. The provenance as subsurface runoff / baseflow flux is preserved explicitly.

**DEFINITION**:
The daily DA-minus-OPL subsurface-runoff/baseflow difference target:
`delta_baseflow = baseflow_DA - baseflow_OPL`

**SIGN**:
- `> 0`: DA experiment has greater Noah-MP Qsb/baseflow flux than OPL
- `< 0`: DA experiment has lower Noah-MP Qsb/baseflow flux than OPL
- `= 0`: DA and OPL baseflow agree at stored numerical precision.

**UNITS**:
`mm/day`

**24-H FLUX SEMANTICS**:
Canonical daily baseflow is derived from the 24-h mean Noah-MP Qsb_tavg flux using Qsb_tavg * 86400 and expressed in mm/day. `delta_baseflow` is the daily DA-minus-OPL difference derived from the corresponding 24-h mean subsurface-runoff/baseflow flux products.

**DISTINCTION FROM STREAMFLOW / GROUNDWATER STORAGE**:
`delta_baseflow` is exactly the Noah-MP Qsb_tavg flux expressed as mm/day. It is NOT routed streamflow, HyMAP discharge, observed baseflow, groundwater storage, or groundwater-table depth.

**GRID / TIME SUPPORT**:
Exact coordinate equality (max diff = 0.0) between OPL and DA experiments was verified prior to subtraction for all annual arrays.

**SOURCE SIGN / ZERO STRUCTURE**:
Source baseflow is strictly non-negative. Zero diagnostics reveal that baseflow is essentially non-zero everywhere across the canonical land mask for the 2016-2020 period (non-zero fraction is 100.00%). Therefore, no artificial numerical active/inactive threshold is forced. Exact zeros in `delta_baseflow` occur only where DA precisely equals OPL.

**ALL-DAY SUPPORT**:
Support is the complete canonical model calendar (1,827 days, 2016-01-01 through 2020-12-31). `delta_baseflow` is defined on all valid daily model pixel-days, not just on assimilation-support days.

**ASSIMILATION VS NO-ASSIMILATION QC**:
On no-assimilation days (`observation_frequency == 0`), DA-minus-OPL baseflow differences continue to persist at substantial magnitudes, reflecting differences between the complete integrated DA and OPL experiment trajectories rather than instantaneous assimilation corrections.

**OUTAGE BEHAVIOR**:
During the SMAP observation outage (19 June - 23 July 2019), `observation_frequency` was exactly zero everywhere. However, `delta_baseflow` remained fully populated, quantifying the DA-minus-OPL baseflow differences during a documented period without assimilated SMAP observations.

**TEMPORAL PERSISTENCE**:
The aggregated daily `delta_baseflow` diagnostics exhibit strong temporal persistence.

**RELATION TO DELTA_RZSM**:
Correlations are descriptive comparisons only. `delta_baseflow` exhibits expected positive associations with `delta_rzsm`, but this does not state that RZSM exclusively causes baseflow from correlation alone.

**RELATION TO DELTA_ET**:
Correlations between `delta_et` and `delta_baseflow` are descriptive associations.

**RELATION TO DELTA_SURFACE_RUNOFF**:
Associations compare the two runoff pathways descriptively and must not be interpreted as direct partition causality.

**RELATION TO SURFACE INCREMENT**:
The relationship between `delta_baseflow` and the EnKF Layer-1 surface increment is weak/negligible on assimilation days, reflecting the different stages and quantities (instantaneous surface EnKF update vs daily Noah-MP Qsb flux difference).

**SEASONAL BEHAVIOR**:
Responses occur year-round. Given baseflow is continuously active across the domain, seasonal stratifications summarize varying mean magnitude differences without requiring zero-support adjustments.

**ROW-WISE NUMERICAL STRUCTURE**:
A critical numerical diagnostic: `delta_baseflow` preserves a row-dependent numerical structure. This row-dependent structure in `delta_baseflow` is inherited from the DA Qsb/baseflow outputs and is consistent with the row-dependent implementation-related structure previously documented in the raw LIS flux diagnostics (see `docs/preprocessing/model_diagnostics.md`).

**CDF VS NOCDF CAUTION**:
The DA experiments differ in observation representation, assimilation support frequency, and their complete DA and ensemble/forcing trajectories. Descriptive comparisons should not be used to rank experiments against each other based on raw `delta_baseflow`.

**XAI TRANSFER ROLE**:
`delta_baseflow` is a Transfer target describing the DA-minus-OPL subsurface-runoff/baseflow flux difference. It represents the difference between complete DA and OPL experiment trajectories, conceptually summarizing the sequence: altered DA trajectory -> altered subsurface/root-zone evolution -> altered Noah-MP Qsb/baseflow flux. It is not labeled as a pure causal SMAP assimilation impact.

**TARGET-TIMING / LEAKAGE CAUTION**:
For future XAI prediction of `delta_baseflow`, feature timing must be designed explicitly. Future model states, future fluxes, post-analysis residuals, or information produced after the target interval MUST NOT be used automatically as predictors. Future XAI models may also learn the implementation-dependent spatial numerical structure in addition to physically meaningful hydrological relationships.

**OUTPUT PATH**:
- `data/processed/transfer/da_cdf/delta_baseflow/delta_baseflow_YYYY.nc`
- `data/processed/transfer/da_nocdf/delta_baseflow/delta_baseflow_YYYY.nc`

---

## Further Reading
For a complete cross-target audit, numerical diagnostics, and implications for ML feature engineering, please refer to the dedicated [Transfer Target Audit](transfer_target_audit.md).

For independent evaluation reference preparation, please refer to [Value Data Preparation](value_data_preparation.md).

