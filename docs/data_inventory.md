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

> **Important unresolved note:** Variables are `_tavg` outputs with `time_increment=86400`. The exact interpretation of the filename timestamp as end-of-period labeling remains to confirm from LIS documentation/configuration.

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

**GLEAM path:**
`/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/validation/evapotranspiration/GLEAM/`

- Actual ET variable/product: E
- Versions available: v3.7a and v4.3a
- Period observed: 2015–2020
- Format: NetCDF

| Item | Status |
|------|--------|
| Version to use | To confirm |
| Native frequency | To confirm |
| Units | To confirm |
| Spatial resolution | To confirm |
| Dimensions | To confirm |
| Missing-value convention | To confirm |

**WaPOR path:**
`/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/validation/evapotranspiration/WaPOR/`

- WaPOR v2 AETI
- Dekadal organization
- Format: GeoTIFF
- WaPOR v3 material exists but covers only 2018–2020

| Item | Status |
|------|--------|
| WaPOR product/version retained for the analysis | To confirm |
| Exact coverage | To confirm |
| Units | To confirm |
| Spatial resolution | To confirm |
| CRS | To confirm |
| Nodata convention | To confirm |

## 9. In-Situ Precipitation

**File:**
`/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/data/insitu_data/ABH_stations_plusziz_and_abhbc1.csv`

**Known columns:**
`Date`, `Station`, `Precipitation`, `Longitude`, `Latitude`

- Format: CSV
- Precipitation is the only meteorological variable currently available in this file.

| Item | Status |
|------|--------|
| Number of stations | To confirm |
| Temporal frequency | To confirm |
| Temporal coverage | To confirm |
| Precipitation units | To confirm |
| Missing-data characteristics | To confirm |

## 10. Remaining Decisions

| Item | Decision / metadata still needed |
|------|----------------------------------|
| Exact LIS HIST timestamp convention | To confirm |
| Final RZSM depth/definition | To confirm |
| EnKF increment/innovation units | To confirm |
| GLEAM metadata and version retained | To confirm |
| WaPOR metadata and product retained | To confirm |
| In-situ precipitation metadata | To confirm |
