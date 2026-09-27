# TRANSFER Development XAI (RF-04C)

## Purpose
To execute the frozen XAI protocol against the TRANSFER predictive matrix for all 4 hydrological targets.

## Scientific Question
How does the predictive utilization of antecedent land surface memory and external meteorological forcing shift when transferring SMAP assimilation impacts across divergent diagnostic boundaries (rzsm, et, runoff, baseflow)?

## Frozen Inputs
- Frozen `da_cdf` and `da_nocdf` TRANSFER RF models (RF_A).
- The dynamically verified single-support `transfer_2019.parquet` shared cohort.
- Predefined scientific feature groups.
- Frozen TreeSHAP and permutation parameters.

## Planned Outputs
- Target-specific predictor-level mean |SHAP| and global statistics.
- Scientific-group SHAP importance contrasting the 4 distinct structural targets.
- Explanatory dependence logic for specific hydrological fluxes.
- Permutation-importance controls across targets.

## Status
- **Status:** PLANNED
