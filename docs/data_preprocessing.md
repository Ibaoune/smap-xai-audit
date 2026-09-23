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
This proves that finite innovation perfectly controls where an assimilation update occurs.

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
- `= 0` (where `observation_frequency == 0`): No assimilation update occurred.

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
Two distinct ML modeling approaches are possible for the XAI dataset:
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
