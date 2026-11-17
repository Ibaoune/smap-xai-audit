# Random Forest Development Matrix (RF-03B/RF-03C)

## Overview
This document summarizes the final, frozen configuration of the Random Forest primary predictive matrix built during the **RF-03B** and **RF-03C** stages. This matrix serves as the foundation for the Explainable AI (XAI) stages.

## Stage Status
- **RF-03B (Primary RF Matrix):** CLOSED
- **RF-03C (Matched-Baseline Reproducibility):** CLOSED
- **2020 Data:** SEALED

## Model Matrix Details

### Data Splits
- **Development/Train:** 2016-01-08 through 2018-12-31 (temporal folds 1 and 2).
- **Validation:** 2019-01-01 through 2019-12-31 (temporal fold 3).
- **Test:** 2020 (Sealed).

### Frozen RF Configurations
- **SOURCE:** `RF_A`
- **TRANSFER:** `RF_A`
- **VALUE:** `RF_B`

### Native SOURCE Models
Native models were trained on the full available canonical support for both `da_cdf` and `da_nocdf` independently. These models utilize the native temporal baselines for skill assessment.

### Matched SOURCE Models
To allow for direct attribution comparisons without support bias, **matched SOURCE models** were trained and evaluated exclusively on the intersected canonical support.
- **Matched Support Generation:** Common subset of `date`, `y_index`, `x_index`.
- **Exact Matched Baselines:**
  - `da_cdf` matched baseline MAE: `0.009457439`
  - `da_nocdf` matched baseline MAE: `0.009304297`
- The evaluation resolver explicitly enforces matched baselines for matched SOURCE metrics and prohibits silent fallback to native baselines.

### TRANSFER Primary Matrix
The TRANSFER matrix consists of 4 core scientific targets modeled over common support:
- `delta_rzsm`
- `delta_et`
- `delta_surface_runoff`
- `delta_baseflow`

### VALUE Primary Matrix
The VALUE matrix consists of the single `value_ae` target modeled for `da_cdf` and `da_nocdf` over the GLEAM support grid.

## Relevant Links
- **XAI Protocol:** [XAI README](../../docs/xai/README.md) and [Protocol Freeze](../../docs/xai/01_rf_xai_protocol.md)
- **Model Configurations:** `configs/modeling/models.yaml`
- **Evaluation Module:** `src/smap_xai/modeling/evaluation.py`
