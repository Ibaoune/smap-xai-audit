# RF-06: Final 2020 Holdout Evaluation and XAI

## Overview
This document serves as the formal record of the one-time final opening of the 2020 holdout data. 

**The 2020 holdout was opened only after completion of model development, XAI protocol freeze, and final 2016–2019 refitting.**

- **RF-04C Freeze Commit:** `bb777c91889d76ecab02067520c9a9f948f3563e`
- **RF-05 Refit Commit:** `99de23e70503ff7151192e414ff66f7ec2e52c6d`
- **Timestamp of First 2020 Opening:** `2026-10-04T18:43:00+01:00`

## Frozen Methodology Checksums
- `configs/modeling/models.yaml`: `6ad55edc495c89328e368546b317fd74`
- `configs/xai/rf_xai.yaml`: `703b2b28fc892f6648b3202b5aa376ef`
- `configs/xai/feature_groups.yaml`: `7816dfed4aecc15a177c6e09fb7e7b2c`
- `configs/modeling/splits.yaml`: `feb391f1cfe306ec36fa7c462b40b5f0`

## Frozen Model Inventory (14 Models)
- **SOURCE (4)**: RF_A on `context_only_feature_set`. CDF (native, matched), NoCDF (native, matched). Target: `daily_absolute_increment`.
- **TRANSFER (8)**: RF_A on `source_context_feature_set`. CDF and NoCDF for `delta_rzsm`, `delta_et`, `delta_surface_runoff`, `delta_baseflow`.
- **VALUE (2)**: RF_B on `value_context_feature_set`. CDF and NoCDF. Target: `value_ae`.

## Frozen Baseline Definitions
- **SOURCE**: Monthly training-median (2016-2019).
- **TRANSFER**: Monthly training-mean (2016-2019).
- **VALUE**: Monthly training-median (2016-2019).

## Frozen XAI Sampling Protocol
- **Cohort Size**: 50,000 (if sufficient rows exist), balanced by month × spatial_fold.
- **TreeSHAP Subset**: 10,000 rows.
- **Permutation Subset**: 5,000 rows.
- **Random Seed**: 42.

## Pre-Opening Audit Status
- RF-XAI Global Freeze Audit: PASSED
- RF-05 Final Refit Audit: PASSED

*(Note: No methodological choice has been changed in response to 2020 opening. All metric calculations and XAI protocols strictly adhere to the frozen rules.)*
