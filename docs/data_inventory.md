# SMAP-XAI Audit — Data Inventory

**Author:** M. El Aabaribaoune (@um6p)

---

## 1. Purpose

This is the **living inventory** of the scientific datasets used by the SMAP-XAI Audit project.

It records what physically exists in the source datasets on the HPC filesystem.
Its scope and guiding rules are:

- Only **verified** information is recorded here. Verification source is noted for each entry.
- Metadata that has not been explicitly checked is marked **"To verify"** — it is never inferred.
- This document is **different from the future data contract** (P1.3): the inventory is a
  factual record of what exists; the data contract will define what the pipeline expects.
- The document is updated progressively as Phase 1 tasks complete.

---

## 2. Data Locations

All paths are absolute on the Lustre filesystem.

| Role | Absolute path |
|------|---------------|
| Workspace root | `/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/` |
| Noah-MP experiments | `…/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/` |
| ET observations | `…/NoahMP_Morocco/data/validation/evapotranspiration/` |
| In-situ observations | `…/data/insitu_data/ABH_stations_plusziz_and_abhbc1.csv` |

> Path validation performed in P1.1. All three paths confirmed to exist and be readable
> under owner `mohammad.elaabaribao`, group `empowermed-ahl6xm8o7mg-managers`.

---

## 3. Noah-MP Experiments

**Root:**
```
/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/
  NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/
```

### 3.1 OPL — Open-Loop baseline

| Attribute | Value | Status |
|-----------|-------|--------|
| Directory | `OPL_noirr_2016_2020/` | Verified P1.1 |
| Role | Open-loop simulation (no data assimilation) | Verified P1.1 |
| Irrigation flag | No irrigation (`noirr`) | Verified P1.1 |
| Approx. disk size | 5.5 GB | Verified P1.1 |
| Output subdirectory | `output/` | Verified P1.1 |
| Output file count | 1,947 files | Verified P1.1 |
| Monthly output dirs | 60 (2016-01 → 2020-12) | Verified P1.1 |
| Output subfolders per month | `SURFACEMODEL/` | Verified P1.1 |
| File format | NetCDF (`.nc`) | Verified P1.1 |
| Output frequency (within month) | To verify in P1.2 | — |
| Variable names | To verify in P1.2 | — |
| Spatial resolution / grid | To verify in P1.2 | — |
| Units | To verify in P1.2 | — |
| Timestamp convention | To verify in P1.2 | — |
| Completeness at daily level | To verify in P1.2 | — |

Internal structure (verified):
```
OPL_noirr_2016_2020/
├── config/           # experiment.ini
├── generated/        # configs/, jobs/
├── logs/             # subdirectories by MMYYYY (012016 … 122020)
├── output/
│   └── YYYY-MM/      # 60 monthly dirs
│       └── SURFACEMODEL/   # .nc files
├── restarts/         # LIS restart .nc files
├── scripts/          # chain_da.py
└── templates/        # lis_da.config.template
```

---

### 3.2 DA-NoCDF — Data Assimilation without CDF matching

| Attribute | Value | Status |
|-----------|-------|--------|
| Directory | `DA_nocdf_noirr_2016_2020/` | Verified P1.1 |
| Role | EnKF data assimilation, no CDF-matching applied to observations | Verified P1.1 |
| Irrigation flag | No irrigation (`noirr`) | Verified P1.1 |
| Approx. disk size | 35 GB | Verified P1.1 |
| Output subdirectory | `output/` | Verified P1.1 |
| Output file count | 17,751 files | Verified P1.1 |
| Monthly output dirs | 60 (2016-01 → 2020-12) | Verified P1.1 |
| Output subfolders per month | `SURFACEMODEL/`, `DAOBS/`, `DAPERT/`, `EnKF/` | Verified P1.1 |
| File formats | NetCDF (`.nc`), `.1gs4r`, `.bin` | Verified P1.1 |
| Output frequency (within month) | To verify in P1.2 | — |
| Variable names | To verify in P1.2 | — |
| Spatial resolution / grid | To verify in P1.2 | — |
| Units | To verify in P1.2 | — |
| Timestamp convention | To verify in P1.2 | — |
| Completeness at daily level | To verify in P1.2 | — |

Internal structure (verified):
```
DA_nocdf_noirr_2016_2020/
├── config/           # experiment.ini
├── generated/        # configs/, jobs/
├── logs/             # subdirectories by MMYYYY
├── output/
│   └── YYYY-MM/      # 60 monthly dirs
│       ├── SURFACEMODEL/   # .nc files (soil/flux state)
│       ├── DAOBS/          # observation files (.nc, .1gs4r)
│       ├── DAPERT/         # perturbation files
│       └── EnKF/           # ensemble Kalman filter outputs
├── restarts/         # pert/, surf/ subdirs
├── scripts/          # chain_da.py
└── templates/        # lis_da.config.template
```

---

### 3.3 DA-CDF — Data Assimilation with CDF matching

| Attribute | Value | Status |
|-----------|-------|--------|
| Directory | `DA_cdf_noirr_2016_2020/` | Verified P1.1 |
| Role | EnKF data assimilation with CDF-matching applied to observations | Verified P1.1 |
| Irrigation flag | No irrigation (`noirr`) | Verified P1.1 |
| Approx. disk size | 35 GB | Verified P1.1 |
| Output subdirectory | `output/` | Verified P1.1 |
| Output file count | 17,127 files | Verified P1.1 |
| Monthly output dirs | 60 (2016-01 → 2020-12) | Verified P1.1 |
| Output subfolders per month | `SURFACEMODEL/`, `DAOBS/`, `DAPERT/`, `EnKF/` | Verified P1.1 |
| File formats | NetCDF (`.nc`), `.1gs4r`, `.bin` | Verified P1.1 |
| Output frequency (within month) | To verify in P1.2 | — |
| Variable names | To verify in P1.2 | — |
| Spatial resolution / grid | To verify in P1.2 | — |
| Units | To verify in P1.2 | — |
| Timestamp convention | To verify in P1.2 | — |
| Completeness at daily level | To verify in P1.2 | — |

Internal structure (verified): identical layout to DA-NoCDF above.

---

### 3.4 Auxiliary Experiment Directories

These directories exist within `matrix_2016_2020/` but are **not part of the three main experiments
currently targeted** by the audit.

#### DA_anomaly_noirr_2016_2020

| Attribute | Value | Status |
|-----------|-------|--------|
| Directory | `DA_anomaly_noirr_2016_2020/` | Verified P1.1 |
| Role | Anomaly-based DA experiment | Verified P1.1 |
| Run status | Appears not yet run — no standard `output/` directory present | Verified P1.1 |
| Approx. disk size | 72 KB (configuration skeleton only) | Verified P1.1 |

#### CDF (lookup-table workspace)

| Attribute | Value | Status |
|-----------|-------|--------|
| Directory | `CDF/` | Verified P1.1 |
| Role | CDF fitting workspace; holds fitted lookup tables (`smap_cdf.nc`) and combined OPL monthly output used during CDF computation | Verified P1.1 |
| Approx. disk size | 388 MB | Verified P1.1 |
| Key files | `smap_cdf.nc`, `smap_cdf_domain.nc` (in `OUTPUT_noirr/`, `OUTPUT_irr/`); `ldt.config.cdf*`; `run_cdf.sh`; `SMAP_filelist.dat` | Verified P1.1 |
| Note | This is an auxiliary processing directory, not a standalone LIS simulation run | Verified P1.1 |

#### README.md

A `README.md` is present at the `matrix_2016_2020/` root level. Content not yet read.

---

## 4. Evapotranspiration Observations

**Root:**
```
/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/
  NoahMP_Morocco/data/validation/evapotranspiration/
```

### 4.1 GLEAM

| Attribute | Value | Status |
|-----------|-------|--------|
| Product family | GLEAM | Verified P1.1 |
| Directory | `GLEAM/` | Verified P1.1 |
| Versions present | v3.7a (in `GLEAM/`) and v4.3a (in `GLEAM/raw/`) | Verified P1.1 |
| Variables (from filenames) | `E` (actual ET), `Ep` (potential ET) | Verified P1.1 |
| Period | 2015–2020 (both versions) | Verified P1.1 |
| Total file count | 18 | Verified P1.1 |
| Format | NetCDF (`.nc`) | Verified P1.1 |
| Approx. disk size | 33 GB | Verified P1.1 |
| Temporal frequency | To verify in P1.3 | — |
| Spatial resolution | To verify in P1.3 | — |
| Variable dimensions / units | To verify in P1.3 | — |
| Coverage completeness | To verify in P1.3 | — |

File naming pattern (verified):
```
GLEAM/
├── E_{YYYY}_GLEAM_v3.7a.nc         # v3.7a actual ET — one file per year (2015–2020)
└── raw/
    ├── E_{YYYY}_GLEAM_v4.3a.nc     # v4.3a actual ET — one file per year (2015–2020)
    └── Ep_{YYYY}_GLEAM_v4.3a.nc    # v4.3a potential ET — one file per year (2015–2020)
```

> Note: coverage starts in 2015, one year before the main experiment window (2016–2020).
> This may be useful for warm-up or validation baseline — to be confirmed in P1.3.

---

### 4.2 WaPOR

| Attribute | Value | Status |
|-----------|-------|--------|
| Directory | `WaPOR/` | Verified P1.1 |
| Versions present | v2 and v3 | Verified P1.1 |
| Total file count | 52 | Verified P1.1 |
| Approx. disk size | 230 MB | Verified P1.1 |
| Format | GeoTIFF (`.tif`); metadata: `.csv`, `.yaml`, `.md` | Verified P1.1 |

**WaPOR v2 material (verified):**

| Attribute | Value | Status |
|-----------|-------|--------|
| Variable | AETI (Actual EvapoTranspiration and Interception) | Verified P1.1 |
| Temporal organisation | Dekadal products, organised by year under `WaPOR_v2_AETI/raw/YYYY/` | Verified P1.1 |
| File naming | `L1_AETI_{YYYYDDD}.tif` | Verified P1.1 |
| Metadata directory | `WaPOR_v2_AETI/metadata/` | Verified P1.1 |
| Exact year range | To verify in P1.3 | — |
| Spatial resolution / projection | To verify in P1.3 | — |
| Units | To verify in P1.3 | — |

**WaPOR v3 material (verified):**

| Attribute | Value | Status |
|-----------|-------|--------|
| Variables | AETI, E (actual ET), T (transpiration), NPP | Verified P1.1 |
| Temporal organisation | Annual composite GeoTIFFs, one file per variable per year | Verified P1.1 |
| Period observed | 2018–2020 (3 years) | Verified P1.1 |
| File naming | `WaPOR_v3_{VARIABLE}_{YYYY}.tif` | Verified P1.1 |
| Spatial resolution / projection | To verify in P1.3 | — |
| Units | To verify in P1.3 | — |

> Note: WaPOR v3 material covers 2018–2020 only — two years shorter than the main
> experiment window (2016–2020). Implications for validation to be assessed in P1.3.

---

### 4.3 MOD16

| Attribute | Value | Status |
|-----------|-------|--------|
| Product | MOD16A2GF | Verified P1.1 |
| Collection | 6.1 | Verified P1.1 |
| Directory | `MOD16/raw/` | Verified P1.1 |
| MODIS tile | h17v05 | Verified P1.1 |
| Nominal product frequency | 8-day (gap-filled composite) | Verified P1.1 |
| Period | 2015–2020 | Verified P1.1 |
| Total file count | 276 | Verified P1.1 |
| Format | HDF4 (`.hdf`) | Verified P1.1 |
| Approx. disk size | 3.4 GB | Verified P1.1 |
| File naming | `MOD16A2GF.A{YYYY}{DOY}.h17v05.061.{processing_timestamp}.hdf` | Verified P1.1 |
| Variable names / sub-datasets | To verify in P1.3 | — |
| Spatial resolution | To verify in P1.3 | — |
| Units | To verify in P1.3 | — |
| Completeness (missing 8-day periods) | To verify in P1.3 | — |

---

## 5. In-Situ Observations

**File:**
```
/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/
  data/insitu_data/ABH_stations_plusziz_and_abhbc1.csv
```

| Attribute | Value | Status |
|-----------|-------|--------|
| Format | CSV | Verified P1.1 |
| Approx. size | 117 MB | Verified P1.1 |
| Total rows (data, excl. header) | 2,413,378 | Verified P1.1 |
| Columns | `Date`, `Station`, `Precipitation`, `Longitude`, `Latitude` | Verified P1.1 |
| Temperature column | Not identified in P1.1 | Verified P1.1 |
| Station networks | ABH stations + Ziz basin + ABHBC1 (inferred from filename) | Filename only — to verify |
| Station count (unique) | To verify in P1.2 | — |
| Temporal frequency | To verify in P1.2 | — |
| Temporal coverage (start/end dates) | To verify in P1.2 | — |
| Missing-data rate | To verify in P1.2 | — |
| Precipitation units | To verify in P1.2 | — |
| Coordinate reference system | To verify in P1.2 | — |

---

## 6. Open Questions / Metadata To Verify

The table below consolidates all items flagged **"To verify"** across this document.

| # | Dataset | Attribute | Target task |
|---|---------|-----------|-------------|
| 1 | OPL / DA-NoCDF / DA-CDF | Output frequency within each month | P1.2 |
| 2 | OPL / DA-NoCDF / DA-CDF | Variable names in `SURFACEMODEL/` | P1.2 |
| 3 | OPL / DA-NoCDF / DA-CDF | Spatial grid / resolution | P1.2 |
| 4 | OPL / DA-NoCDF / DA-CDF | Physical units per variable | P1.2 |
| 5 | OPL / DA-NoCDF / DA-CDF | Timestamp convention (start/end of interval) | P1.2 |
| 6 | OPL / DA-NoCDF / DA-CDF | Output completeness at daily level | P1.2 |
| 7 | In-situ CSV | Unique station count | P1.2 |
| 8 | In-situ CSV | Temporal frequency (daily / sub-daily) | P1.2 |
| 9 | In-situ CSV | Temporal coverage (start / end dates) | P1.2 |
| 10 | In-situ CSV | Missing-data rate and pattern | P1.2 |
| 11 | In-situ CSV | Precipitation units | P1.2 |
| 12 | In-situ CSV | Coordinate reference system | P1.2 |
| 13 | GLEAM | Temporal frequency | P1.3 |
| 14 | GLEAM | Spatial resolution | P1.3 |
| 15 | GLEAM | Variable dimensions / units | P1.3 |
| 16 | GLEAM | Coverage completeness over 2015–2020 | P1.3 |
| 17 | WaPOR v2 | Exact year range | P1.3 |
| 18 | WaPOR v2/v3 | Spatial resolution / projection | P1.3 |
| 19 | WaPOR v2/v3 | Units | P1.3 |
| 20 | MOD16 | Variable names / HDF sub-datasets | P1.3 |
| 21 | MOD16 | Spatial resolution | P1.3 |
| 22 | MOD16 | Units | P1.3 |
| 23 | MOD16 | Completeness (missing 8-day periods) | P1.3 |
| 24 | In-situ CSV | Station networks (verify against file contents, not just filename) | P1.2 |
| 25 | `matrix_2016_2020/README.md` | Content — may contain additional experiment metadata | P1.2 |

---

## 7. Inventory History

| Task | Description | Date |
|------|-------------|------|
| P1.1 | Directory-level data inventory completed. All three source paths validated. Experiment structure, ET observation directories, and in-situ CSV basic metadata recorded. | 2026-09-21 |
| P1.1b | Validated P1.1 findings recorded in this living inventory document. | 2026-09-21 |
