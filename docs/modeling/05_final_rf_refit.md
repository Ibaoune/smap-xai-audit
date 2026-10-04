# RF-05: Final Random Forest Refit on 2016-2019

## Overview
This document serves as the formal record of the final Random Forest refit phase (RF-05). Following the RF-04C methodological freeze, all chosen models were retrained on the entire available pre-test data to maximize predictive capacity prior to the final 2020 holdout evaluation.

**Explicit Statement:** The 2020 validation year remained completely **SEALED** during this phase. No 2020 data was accessed, loaded, evaluated, or inspected.

- **RF-04C Freeze Commit:** `bb777c91889d76ecab02067520c9a9f948f3563e`
- **Training Window:** 2016-01-08 to 2019-12-31

## Model Inventory & Assignments

Exactly 14 final models were produced, divided across the three diagnostic blocks:

### SOURCE (4 Models)
- **Target:** `daily_absolute_increment`
- **Model Configuration:** `RF_A`
- **Feature Set:** `context_only_feature_set` (35 features)
- **Experiments:** CDF/NoCDF on Native and Matched support

### TRANSFER (8 Models)
- **Targets:** `delta_rzsm`, `delta_et`, `delta_surface_runoff`, `delta_baseflow`
- **Model Configuration:** `RF_A`
- **Feature Set:** `source_context_feature_set` (52 features)
- **Experiments:** CDF/NoCDF on Native support

### VALUE (2 Models)
- **Target:** `value_ae`
- **Model Configuration:** `RF_B`
- **Feature Set:** `value_context_feature_set` (52 features)
- **Experiments:** CDF/NoCDF on Native support

## Training Support Fingerprints & Row Counts

*(Table to be populated after training completes)*

| Block | Experiment | Target | Support | N_Rows | Fingerprint |
|-------|------------|--------|---------|--------|-------------|
| SOURCE | da_cdf | daily_absolute_increment | matched | 1841519 | 332ce20783aed1dcf90593a1ddc10bfa |
| SOURCE | da_cdf | daily_absolute_increment | native | 1853127 | ce91915d11055713ef307ad12b2e6192 |
| SOURCE | da_nocdf | daily_absolute_increment | matched | 1841519 | 332ce20783aed1dcf90593a1ddc10bfa |
| SOURCE | da_nocdf | daily_absolute_increment | native | 5881531 | 211550cc63ce17146cc4ff31ee602b86 |
| TRANSFER | da_cdf | delta_baseflow | native | 23307620 | 9967a50e8efe0075fd17b2748430e883 |
| TRANSFER | da_cdf | delta_et | native | 23307620 | 9967a50e8efe0075fd17b2748430e883 |
| TRANSFER | da_cdf | delta_rzsm | native | 23307620 | 9967a50e8efe0075fd17b2748430e883 |
| TRANSFER | da_cdf | delta_surface_runoff | native | 23307620 | 9967a50e8efe0075fd17b2748430e883 |
| TRANSFER | da_nocdf | delta_baseflow | native | 23307620 | 9967a50e8efe0075fd17b2748430e883 |
| TRANSFER | da_nocdf | delta_et | native | 23307620 | 9967a50e8efe0075fd17b2748430e883 |
| TRANSFER | da_nocdf | delta_rzsm | native | 23307620 | 9967a50e8efe0075fd17b2748430e883 |
| TRANSFER | da_nocdf | delta_surface_runoff | native | 23307620 | 9967a50e8efe0075fd17b2748430e883 |
| VALUE | da_cdf | value_ae | native | 5975940 | 3728b9e1ce23267764330503c60bf51a |
| VALUE | da_nocdf | value_ae | native | 5975940 | 3728b9e1ce23267764330503c60bf51a |

## Artifact Locations
All final model binaries (`model.joblib`) and their associated metadata (`metadata.json`) have been saved to:
`reports/modeling/models/final_refit_2016_2019/`

The development artifacts from RF-04 were completely preserved and not overwritten.

## QC Result
The final QC audit (`05_audit_final_rf_refit.py`) was successfully executed, verifying the exact 14 models, absence of 2020 leakage, correct feature counts, correct training hyperparameters, and matching of keys between CDF and NoCDF matched models.

**Result:** `RF-05 FINAL REFIT AUDIT PASSED`
