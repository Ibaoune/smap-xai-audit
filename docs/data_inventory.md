# SMAP-XAI Operational Data Inventory

**Author:** M. El Aabaribaoune (@um6p)

## 1. Purpose

This document is the operational inventory of source data used by SMAP-XAI Audit and records:
- source paths;
- variables;
- file patterns;
- units;
- temporal resolution;
- spatial resolution;
- coverage;
- unresolved preprocessing decisions.

## 2. Noah-MP / LIS Experiments

**Root:** `/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/`

| Experiment | Directory | Assimilation | CDF matching |
|------------|-----------|--------------|--------------|
| OPL | `OPL_noirr_2016_2020/` | No | No |
| DA-NoCDF | `DA_nocdf_noirr_2016_2020/` | Yes (EnKF) | No |
| DA-CDF | `DA_cdf_noirr_2016_2020/` | Yes (EnKF) | Yes |

## 3. Common Noah-MP Output Characteristics

**SURFACEMODEL file pattern:**
`output/YYYY-MM/SURFACEMODEL/YYYYMM/LIS_HIST_YYYYMMDD0000.d01.nc`

- **Format:** NetCDF4
- **Grid:** 121 x 181
- **Latitude:** 30.0 to 36.0
- **Longitude:** -10.0 to -1.0
- **Resolution:** 0.05 degree
- **Native output interval:** 24 h
- **Available HIST timestamp range:** 2016-01-02 00:00 to 2021-01-01 00:00
- **Number of HIST timestamps:** 1827

> **Important note:** Variables are `_tavg` outputs with `time_increment=86400`. The LIS filename timestamp corresponds to the **end of the averaging interval** (confirmed from LIS source code: `LIS_surfaceModelMod.F90`, `LIS_fileIOMod.F90`, `LIS_histDataMod.F90`, `LIS_historyMod.F90`). For example, `LIS_HIST_201601020000.d01.nc` represents the daily average over `[2016-01-01 00:00, 2016-01-02 00:00)`. Thus, its canonical model date is **2016-01-01**.

## 4. Variables Used by SMAP-XAI

| Scientific quantity | Experiment(s) | File family | Exact variable | Units | Native temporal representation | Grid |
|---------------------|---------------|-------------|----------------|-------|--------------------------------|------|
| Surface soil moisture | OPL, DA-NoCDF, DA-CDF | SURFACEMODEL | `SoilMoist_tavg`, layer 1 | m3 m-3 | `_tavg` (24 h) | 121x181 |
| Root-zone soil moisture components | OPL, DA-NoCDF, DA-CDF | SURFACEMODEL | `SoilMoist_tavg`, layers 1–4 | m3 m-3 | `_tavg` (24 h) | 121x181 |
| Evapotranspiration | OPL, DA-NoCDF, DA-CDF | SURFACEMODEL | `Evap_tavg` | kg m-2 s-1 | `_tavg` (24 h) | 121x181 |
| Surface runoff | OPL, DA-NoCDF, DA-CDF | SURFACEMODEL | `Qs_tavg` | kg m-2 s-1 | `_tavg` (24 h) | 121x181 |
| Baseflow / subsurface runoff | OPL, DA-NoCDF, DA-CDF | SURFACEMODEL | `Qsb_tavg` | kg m-2 s-1 | `_tavg` (24 h) | 121x181 |

## 5. Soil-Moisture Layers

- **Layer 1:** 0–10 cm
- **Layer 2:** 10–40 cm
- **Layer 3:** 40–100 cm
- **Layer 4:** 100–200 cm

**Thicknesses:** `[10, 30, 60, 100]` cm

SSM = Layer 1.

Final RZSM depth and depth-weighted combination remain a preprocessing decision.

## 6. Assimilation Diagnostics

**DA experiments:**
DA-NoCDF, DA-CDF

**Increment file pattern:**
`output/YYYY-MM/EnKF/YYYYMM/LIS_DA_EnKF_YYYYMMDDHHMI_incr.a01.d01.nc`

**Increment variables:**
`anlys_incr_Soil Moisture Layer X_01` (X = 1,2,3,4)

**Innovation file pattern:**
`output/YYYY-MM/EnKF/YYYYMM/LIS_DA_EnKF_YYYYMMDDHHMI_innov.a01.d01.nc`

**Innovation variable:**
`innov_01`

**Temporal organization:**
event-driven / irregular; timestamps encoded in filenames.

**Units:**
To confirm from LIS/EnKF documentation.

*(Optional diagnostic: ensemble spread is available in `_spread.a01.d01.nc` files)*

## 7. Flux Preprocessing Note

`Evap_tavg`, `Qs_tavg` and `Qsb_tavg` are time-averaged flux rates in `kg m-2 s-1`.

For a 24-h interval, multiplying by 86400 converts the mean rate to `kg m-2 day-1`, numerically equivalent to mm/day for water.

## 8. ET Observations

Primary independent ET reference:
    GLEAM v4.3a

Product:
    GLEAM v4.3a

Variable:
    E

Units:
    mm day-1

Native temporal resolution:
    daily

Coverage:
    2015–2020

Analysis overlap:
    2016–2020

Grid:
    0.1 degree
    1800 x 3600
    global lat/lon

Second independent ET reference:
    MOD16A2GF Collection 6.1

Root:
    /home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/validation/evapotranspiration/MOD16/raw/

Product:
    MOD16A2GF Collection 6.1

Tile:
    h17v05

File pattern:
    MOD16A2GF.AYYYYDDD.h17v05.061.*.hdf

ET subdataset:
    ET_500m

QC subdataset:
    ET_QC_500m

Raw type:
    scaled integer

Scale factor:
    0.1

Physical ET:
    kg m-2 per composite
    numerically equivalent to mm per composite

Native temporal support:
    8-day composite

Coverage:
    2015–2020
    46 composites per year
    full overlap with 2016–2020

Spatial resolution:
    500 m

Projection:
    MODIS Sinusoidal

Tile coverage:
    h17v05 covers the Noah-MP study domain

Fill value:
    32767

### 8.1 Temporal Harmonization Note

For MOD16 comparison, we will aggregate
Noah-MP daily ET and GLEAM daily ET over the exact MOD16 composite
periods.

We will not treat MOD16 as native daily data.

The duration of the final composite of each year must be handled
explicitly because it may contain fewer than 8 days.

### 8.2 Spatial Harmonization Note

MOD16 must be reprojected from the MODIS Sinusoidal grid and
spatially aggregated to the Noah-MP 0.05-degree grid before
pixel-wise comparison.

## 9. In-Situ Observations

**Source:**
`/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/data/insitu_data/ABH_stations_plusziz_and_abhbc1.csv`

**Status:**
Historical in-situ precipitation dataset.
NOT usable for the current 2016–2020 SMAP-XAI analysis.

**Dataset Metadata:**
- **Stations:** 227
- **Native frequency:** daily
- **Full temporal coverage:** 1979-01-01 to 2014-12-31
- **Overlap with SMAP-XAI 2016–2020:** none
- **Coordinates:** available for all stations
- **Precipitation units:** not documented / to confirm
- **Negative precipitation values:** 10,390 records
- **Interpretation of negative values:** unresolved

**Note:**
This dataset has been removed from the ACTIVE preprocessing inputs for the 2016–2020 workflow. A replacement in-situ precipitation dataset overlapping 2016–2020 would be required if station-based forcing diagnostics are retained in the study.

### 9.1 Individual station files

**Source directory:**
`/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/data/insitu_data/`

**Structure:**
- **Format:** Plain text, space/tab delimited, no headers.
- **Date representation:** Columns 1, 2, 3 correspond to Year, Month, Day.
- **Missing value convention:** Sentinel value `-99.9`.

| Station | Station ID | Variables | Units | Frequency | Period | Domain status | Metadata provenance |
|---------|------------|-----------|-------|-----------|--------|---------------|---------------------|
| Agadir-massira | Candidate: 60252 / GMAD | Col 4, 5, 6 | To confirm externally | Daily | 1992–2022 | Inside | Unknown source; coordinates from historical CSV |
| Chefchaouen | Candidate: 60106 | Col 4, 5, 6 | To confirm externally | Daily | 1994–2022 | Inside | Unknown source; coordinates from historical CSV |
| Guelmim | Candidate: 60280 | Col 4, 5, 6 | To confirm externally | Daily | 1992–2022 | Outside | Unknown source; coordinates from historical CSV |
| Tiznit | Candidate: 60270 | Col 4, 5, 6 | To confirm externally | Daily | 1989–2022 | Outside | Unknown source; coordinates from historical CSV |

**Active SMAP-XAI Station Inputs:**
Pending external confirmation of variable names and units, **Agadir-massira** and **Chefchaouen** are potentially usable for the 2016–2020 study. Guelmim and Tiznit fall outside the model domain and will not be used.

## 10. Remaining Decisions

| Item | Decision / metadata still needed |
|------|----------------------------------|
| Final RZSM definition | To confirm |
| EnKF diagnostic units | To confirm |
| GLEAM/Noah-MP spatial harmonization | To confirm |
| MOD16 temporal/spatial harmonization and QC handling | To confirm |
| In-situ precipitation for 2016–2020 | replacement dataset currently unavailable |
| Station column names and units | To confirm externally |
