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
| Storage partitions | 60 `YYYY-MM` dirs (2016-01 → 2020-12); all present, none missing | Verified P1.2 |
| SURFACEMODEL filename pattern | `LIS_HIST_YYYYMMDDHHMI.d01.nc` | Verified P1.2 |
| SURFACEMODEL native cadence | One file per 24 h at 00:00 UTC — perfectly regular | Verified P1.2 |
| SURFACEMODEL timestamp range | 2016-01-02 00:00 → 2021-01-01 00:00 | Verified P1.2 |
| SURFACEMODEL HIST file count | 1,827 — zero gaps, zero duplicates | Verified P1.2 |
| Restart file pattern | `LIS_RST_NOAHMP401_YYYYMMDDHHMI.d01.nc` | Verified P1.2 |
| Restart cadence | 2 per calendar month (end-of-month 23:45; first-of-next 00:00) | Verified P1.2 |
| YYYYMM sub-partition | Each `YYYY-MM/SURFACEMODEL/` contains 2 `YYYYMM/` subdirs; first file of next month spills into current storage partition | Verified P1.2 |
| Variable names in HIST | To verify in P1.3 | — |
| Spatial resolution / grid | To verify in P1.3 | — |
| Physical units | To verify in P1.3 | — |
| Timestamp semantics (instantaneous vs. averaged) | To verify in P1.3 | — |

Internal structure (verified):
```
OPL_noirr_2016_2020/
├── config/           # experiment.ini
├── generated/        # configs/, jobs/
├── logs/             # subdirectories by MMYYYY (012016 … 122020)
├── output/
│   └── YYYY-MM/                         # 60 storage partitions
│       └── SURFACEMODEL/
│           ├── YYYYMM/                  # files for current month
│           │   ├── LIS_HIST_YYYYMMDD0000.d01.nc   # daily at 00:00 UTC
│           │   └── LIS_RST_NOAHMP401_YYYYMM312345.d01.nc
│           └── YYYYMM+1/               # spillover: first file of next month
│               ├── LIS_HIST_YYYYMM+101000000.d01.nc
│               └── LIS_RST_NOAHMP401_YYYYMM+1010000.d01.nc
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
| Storage partitions | 60 `YYYY-MM` dirs (2016-01 → 2020-12); all present, none missing | Verified P1.2 |
| SURFACEMODEL native cadence | One `LIS_HIST_*` per 24 h at 00:00 UTC — identical to OPL | Verified P1.2 |
| SURFACEMODEL HIST file count | 1,827 — identical set to OPL and DA-CDF | Verified P1.2 |
| DAOBS filename pattern | `LISDAOBS_YYYYMMDDHHMI.a01.d01.1gs4r` | Verified P1.2 |
| DAOBS cadence | Irregular/event-driven (observation-dependent); NOT uniform | Verified P1.2 |
| DAOBS file count | 4,619 (2016-01-01 06:00 → 2020-12-31 18:00) | Verified P1.2 |
| DAOBS time-of-day observed | 06:00, 07:00, 18:00, 19:00 UTC predominate | Verified P1.2 |
| EnKF `_incr` / `_innov` files | 4,619 each; `LIS_DA_EnKF_YYYYMMDDHHMI_incr/innov.a01.d01.nc`; same timestamps as DAOBS | Verified P1.2 |
| EnKF `_spread` files | 1,827; `LIS_DA_EnKF_YYYYMMDDHHMI_spread.a01.d01.nc`; 24 h cadence, same timestamps as SURFACEMODEL | Verified P1.2 |
| EnKF total file count | 13,012 (`.nc`) | Verified P1.2 |
| DAPERT filename pattern | `LIS_DAPERT_YYYYMMDDHHMI.d01.bin` | Verified P1.2 |
| DAPERT cadence | 2 per calendar month (end-of-month 23:45; first-of-next 00:00) | Verified P1.2 |
| DAPERT total file count | 120 (60 months × 2) | Verified P1.2 |
| Variable names in HIST | To verify in P1.3 | — |
| Spatial resolution / grid | To verify in P1.3 | — |
| Physical units | To verify in P1.3 | — |
| Timestamp semantics | To verify in P1.3 | — |
| `.1gs4r` format / content | To verify in P1.3 | — |

Internal structure (verified):
```
DA_nocdf_noirr_2016_2020/
├── output/
│   └── YYYY-MM/                         # 60 storage partitions
│       ├── SURFACEMODEL/YYYYMM/          # LIS_HIST_*.nc  +  LIS_RST_*.nc
│       ├── DAOBS/YYYYMM/                 # LISDAOBS_*.1gs4r (irregular timestamps)
│       ├── DAPERT/YYYYMM/               # LIS_DAPERT_*.bin (2 per month)
│       └── EnKF/YYYYMM/                 # LIS_DA_EnKF_*_{incr,innov,spread}.*.nc
├── config/ generated/ logs/ restarts/ scripts/ templates/
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
| Storage partitions | 60 `YYYY-MM` dirs (2016-01 → 2020-12); all present, none missing | Verified P1.2 |
| SURFACEMODEL native cadence | One `LIS_HIST_*` per 24 h at 00:00 UTC — identical to OPL and DA-NoCDF | Verified P1.2 |
| SURFACEMODEL HIST file count | 1,827 — identical set to OPL and DA-NoCDF | Verified P1.2 |
| DAOBS file count | 4,411 (vs 4,619 in DA-NoCDF; 209 fewer + 1 extra = 210-file symmetric difference) | Verified P1.2 |
| DAOBS cadence | Irregular/event-driven — same overall character as DA-NoCDF | Verified P1.2 |
| EnKF `_incr` / `_innov` count | 4,411 each (matched to DAOBS) | Verified P1.2 |
| EnKF `_spread` count | 1,827 — 24 h cadence, identical to DA-NoCDF | Verified P1.2 |
| EnKF total file count | 12,596 (`.nc`) | Verified P1.2 |
| DAPERT file count | 120 — **identical** to DA-NoCDF | Verified P1.2 |
| Variable names in HIST | To verify in P1.3 | — |
| Spatial resolution / grid | To verify in P1.3 | — |
| Physical units | To verify in P1.3 | — |
| Timestamp semantics | To verify in P1.3 | — |

Internal structure (verified): identical layout to DA-NoCDF above.

---

### 3.4 Native Temporal and File Organization — Cross-Experiment Summary (P1.2)

> **CRITICAL NOTE:** `YYYY-MM` directory names are **storage partitions only**.
> They do not define the scientific temporal resolution of model outputs.

#### SURFACEMODEL — all three experiments

| Property | OPL | DA-NoCDF | DA-CDF |
|----------|-----|----------|--------|
| Filename pattern | `LIS_HIST_YYYYMMDDHHMI.d01.nc` | same | same |
| Cadence | 24 h at 00:00 UTC | same | same |
| First timestamp | 2016-01-02 00:00 | same | same |
| Last timestamp | 2021-01-01 00:00 | same | same |
| HIST file count | 1,827 | 1,827 | 1,827 |
| Gaps / duplicates | None | None | None |
| Timestamp sets identical? | — | **Yes** (OPL = DA-NoCDF = DA-CDF) | **Yes** |

> First HIST timestamp is 2016-01-02 (not Jan 1). Last HIST timestamp is 2021-01-01 (one day beyond the declared window).
> The significance of this boundary behavior requires verification in P1.3.

#### Restart files — all three experiments

| Property | Value |
|----------|-------|
| Filename pattern | `LIS_RST_NOAHMP401_YYYYMMDDHHMI.d01.nc` |
| Cadence | 2 per calendar month: last day of month at 23:45; first day of next month at 00:00 |
| Total count (OPL) | 121 files (60 months × 2 + 1 extra at 2021-01-01) |

#### DAOBS and EnKF (_incr / _innov) — DA experiments

| Property | DA-NoCDF | DA-CDF |
|----------|----------|--------|
| Filename pattern | `LISDAOBS_YYYYMMDDHHMI.a01.d01.1gs4r` | same |
| Cadence | **Irregular / event-driven** (observation-dependent) | same character |
| Times-of-day observed | 06:00, 07:00, 18:00, 19:00 UTC predominate | same |
| File count | 4,619 | 4,411 |
| First timestamp | 2016-01-01 06:00 | 2016-01-01 06:00 |
| Last timestamp | 2020-12-31 18:00 | 2020-12-31 18:00 |
| Symmetric difference | 210 files (209 in NoCDF only; 1 in CDF only) | — |

#### EnKF _spread files — DA experiments

| Property | Value |
|----------|-------|
| Filename pattern | `LIS_DA_EnKF_YYYYMMDDHHMI_spread.a01.d01.nc` |
| Cadence | 24 h at 00:00 UTC — same timestamps as SURFACEMODEL |
| File count | 1,827 per experiment |

#### DAPERT files — DA experiments

| Property | Value |
|----------|-------|
| Filename pattern | `LIS_DAPERT_YYYYMMDDHHMI.d01.bin` |
| Cadence | 2 per calendar month (end-of-month 23:45; first-of-next 00:00) |
| File count | 120 per experiment — **identical** between DA-NoCDF and DA-CDF |
| Format | Binary (`.bin`) — contents not inspected |

#### File extension summary (across all three experiments)

| Extension | Family | Count (total) |
|-----------|--------|---------------|
| `.nc` | SURFACEMODEL HIST + RST + EnKF _incr/_innov/_spread | 27,555 |
| `.1gs4r` | DAOBS | 9,030 |
| `.bin` | DAPERT | 240 |

#### Representative files selected for P1.3 (around 2018-06)

| Experiment | Family | Representative file path |
|------------|--------|-------------------------|
| OPL | SURFACEMODEL HIST | `…/OPL_noirr_2016_2020/output/2018-06/SURFACEMODEL/201806/LIS_HIST_201806010000.d01.nc` |
| OPL | SURFACEMODEL RST | `…/OPL_noirr_2016_2020/output/2018-06/SURFACEMODEL/201806/LIS_RST_NOAHMP401_201806302345.d01.nc` |
| DA-NoCDF | SURFACEMODEL HIST | `…/DA_nocdf_noirr_2016_2020/output/2018-06/SURFACEMODEL/201806/LIS_HIST_201806010000.d01.nc` |
| DA-NoCDF | DAOBS | `…/DA_nocdf_noirr_2016_2020/output/2018-06/DAOBS/201806/LISDAOBS_201806010600.a01.d01.1gs4r` |
| DA-NoCDF | EnKF _incr | `…/DA_nocdf_noirr_2016_2020/output/2018-06/EnKF/201806/LIS_DA_EnKF_201806010600_incr.a01.d01.nc` |
| DA-NoCDF | EnKF _innov | `…/DA_nocdf_noirr_2016_2020/output/2018-06/EnKF/201806/LIS_DA_EnKF_201806010600_innov.a01.d01.nc` |
| DA-NoCDF | EnKF _spread | `…/DA_nocdf_noirr_2016_2020/output/2018-06/EnKF/201806/LIS_DA_EnKF_201806300000_spread.a01.d01.nc` |
| DA-NoCDF | DAPERT | `…/DA_nocdf_noirr_2016_2020/output/2018-06/DAPERT/201806/LIS_DAPERT_201806302345.d01.bin` |
| DA-CDF | SURFACEMODEL HIST | `…/DA_cdf_noirr_2016_2020/output/2018-06/SURFACEMODEL/201806/LIS_HIST_201806010000.d01.nc` |
| DA-CDF | DAOBS | `…/DA_cdf_noirr_2016_2020/output/2018-06/DAOBS/201806/LISDAOBS_201806010600.a01.d01.1gs4r` |
| DA-CDF | EnKF _incr | `…/DA_cdf_noirr_2016_2020/output/2018-06/EnKF/201806/LIS_DA_EnKF_201806010600_incr.a01.d01.nc` |
| DA-CDF | EnKF _innov | `…/DA_cdf_noirr_2016_2020/output/2018-06/EnKF/201806/LIS_DA_EnKF_201806010600_innov.a01.d01.nc` |
| DA-CDF | EnKF _spread | `…/DA_cdf_noirr_2016_2020/output/2018-06/EnKF/201806/LIS_DA_EnKF_201806300000_spread.a01.d01.nc` |
| DA-CDF | DAPERT | `…/DA_cdf_noirr_2016_2020/output/2018-06/DAPERT/201806/LIS_DAPERT_201806302345.d01.bin` |

---

### 3.5 Auxiliary Experiment Directories

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
| Station count (unique) | To verify in P1.3 | — |
| Temporal frequency | To verify in P1.3 | — |
| Temporal coverage (start/end dates) | To verify in P1.3 | — |
| Missing-data rate | To verify in P1.3 | — |
| Precipitation units | To verify in P1.3 | — |
| Coordinate reference system | To verify in P1.3 | — |

---

## 6. Open Questions / Metadata To Verify

The table below consolidates all items flagged **"To verify"** across this document.

**Resolved in P1.2** (SURFACEMODEL / DAOBS / EnKF / DAPERT temporal organization — see §3.5)

| # | Dataset | Attribute | Target task |
|---|---------|-----------|-------------|
| 1 | OPL / DA-NoCDF / DA-CDF | Why first HIST timestamp is 2016-01-02, not 2016-01-01 (spin-up?) | P1.3 |
| 2 | OPL / DA-NoCDF / DA-CDF | Variable names and dimensions in `LIS_HIST_*.nc` | P1.3 |
| 3 | OPL / DA-NoCDF / DA-CDF | Spatial grid / resolution | P1.3 |
| 4 | OPL / DA-NoCDF / DA-CDF | Physical units per variable | P1.3 |
| 5 | OPL / DA-NoCDF / DA-CDF | Timestamp semantics: instantaneous vs. period-averaged | P1.3 |
| 6 | DA-NoCDF / DA-CDF | Content and format of `.1gs4r` DAOBS files | P1.3 |
| 7 | DA-NoCDF / DA-CDF | Content and format of `.bin` DAPERT files | P1.3 |
| 8 | DA-NoCDF / DA-CDF | Variables in `LIS_DA_EnKF_*_incr/innov/spread.nc` | P1.3 |
| 9 | DA-NoCDF / DA-CDF | Why DAOBS count differs (4,619 vs 4,411; 210-file diff) | P1.3 |
| 10 | In-situ CSV | Unique station count | P1.3 |
| 11 | In-situ CSV | Temporal frequency (daily / sub-daily) | P1.3 |
| 12 | In-situ CSV | Temporal coverage (start / end dates) | P1.3 |
| 13 | In-situ CSV | Missing-data rate and pattern | P1.3 |
| 14 | In-situ CSV | Precipitation units | P1.3 |
| 15 | In-situ CSV | Coordinate reference system | P1.3 |
| 16 | In-situ CSV | Station networks (verify against file contents) | P1.3 |
| 17 | `matrix_2016_2020/README.md` | Content — may contain experiment metadata | P1.3 |
| 18 | GLEAM | Temporal frequency, spatial resolution, variable units | P1.3 |
| 19 | WaPOR v2 | Exact year range, spatial resolution, units | P1.3 |
| 20 | WaPOR v3 | Spatial resolution, units | P1.3 |
| 21 | MOD16 | Variable names / HDF sub-datasets, spatial resolution, units | P1.3 |

---

## 7. Inventory History

| Task | Description | Date |
|------|-------------|------|
| P1.1 | Directory-level data inventory completed. All three source paths validated. Experiment structure, ET observation directories, and in-situ CSV basic metadata recorded. | 2026-09-21 |
| P1.1b | Validated P1.1 findings recorded in this living inventory document. | 2026-09-21 |
| P1.2 | Noah-MP native temporal and file organization inventory completed. SURFACEMODEL cadence confirmed as 24 h at 00:00 UTC (1,827 files, perfectly regular, identical across OPL/DA-NoCDF/DA-CDF). DAOBS/EnKF-incr/innov cadence confirmed as irregular/event-driven. EnKF-spread and DAPERT cadences confirmed as 24 h and 2-per-month respectively. DA-NoCDF vs DA-CDF DAOBS difference (210 files) documented. Representative files for P1.3 selected. | 2026-09-21 |
