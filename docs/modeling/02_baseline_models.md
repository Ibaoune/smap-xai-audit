# Modeling Step 02: Baseline Models

**Author:** M. El Aabaribaoune

## 1. Purpose
This document specifies the baseline modeling protocol and definitions for the SMAP-XAI project. Baseline models provide transparent reference performance before training flexible machine-learning models, establishing the fundamental predictive difficulty and identifying naive persistence scales. All computationally heavy tasks are executed on SLURM architecture using CPU.

## 2. Quantities Evaluated
- **SOURCE Target:** `daily_absolute_increment` (absolute magnitude of the EnKF analysis-minus-forecast increment). The `daily_signed_increment` is kept only as a secondary diagnostic variable.
- **TRANSFER Targets:** `delta_rzsm`, `delta_et`, `delta_surface_runoff`, `delta_baseflow` (DA minus OPL for the corresponding variable).
- **VALUE Target:** `value_ae` (abs(ET_OPL - ET_GLEAM) - abs(ET_DA - ET_GLEAM)).

## 3. SOURCE Baselines
Target: `daily_absolute_increment`
- **ZERO:** `y_hat = 0`. Assumes no update magnitude.
- **TRAIN MEDIAN:** `y_hat = median(y_train)`. Global central tendency. Fits the context-only feature modes.
- **MONTHLY TRAIN MEDIAN:** `y_hat(month) = median(y_train, month)`. Captures seasonal magnitude climatology.

*(Note: The SCALAR ENKF GAIN PROXY has been removed from the main baseline protocol as it is a mechanistic assimilation diagnostic, not a standard statistical baseline. If retained, it belongs in an optional assimilation QC section.)*

## 4. TRANSFER Baselines
Targets: `delta_rzsm`, `delta_et`, `delta_surface_runoff`, `delta_baseflow`
- **ZERO:** `y_hat = 0`. Assumes no DA-minus-OPL response.
- **TRAIN MEAN:** `y_hat = mean(y_train)`. Global central tendency for continuous Transfer differences.
- **MONTHLY TRAIN MEAN:** `y_hat(month) = mean(y_train, month)`. Captures seasonal transfer climatology.
- **PERSISTENCE_LAG1:** `y_hat = target_lag1`. Memory-informed baseline strictly required for memory-augmented ML feature sets. It does not reflect physical timescales but rather statistical autocorrelation.

## 5. VALUE Baselines
Target: `value_ae`
- **ZERO:** `y_hat = 0`. Assumes DA and OPL have equal absolute ET disagreement with the reference.
- **TRAIN MEAN:** `y_hat = mean(y_train)`. Global mean tendency.
- **TRAIN MEDIAN:** `y_hat = median(y_train)`. Global median tendency.
- **MONTHLY TRAIN MEDIAN:** `y_hat(month) = median(y_train, month)`. Seasonal variability of absolute error difference.

## 6. Temporal Evaluation
We use a strictly locked expanding-window pre-test cross-validation strategy:
- **Fold 1:** Train = 2016-01-08 -> 2016-12-31, Validation = 2017-01-01 -> 2017-12-31
- **Fold 2:** Train = 2016-01-08 -> 2017-12-31, Validation = 2018-01-01 -> 2018-12-31
- **Fold 3:** Train = 2016-01-08 -> 2018-12-31, Validation = 2019-01-01 -> 2019-12-31

*The year 2020 is strictly forbidden in Step 02.*

## 7. Spatial Sensitivity
We use a deterministic balanced spatial-block assignment (5 folds). Baselines are fit using data from 4 folds and validated on the held-out fold. We restrict all spatial baseline development strictly to dates <= 2019-12-31. 
Spatial and temporal metrics are completely separate.

## 8. Metrics
For every target/baseline/fold, we report:
`N`, `MAE`, `RMSE`, `bias` (mean(prediction - target)), `R2`, `Pearson`.
*Note: Pearson correlation is mathematically undefined when predictions have zero variance. Therefore, for constant baselines (`ZERO`, `TRAIN_MEAN`, `TRAIN_MEDIAN`), Pearson is explicitly reported as `NaN`.*

Fixed skill references are defined as `1 - MAE_candidate / MAE_reference`:
- **SOURCE statistical reference:** `MONTHLY_TRAIN_MEDIAN`
- **TRANSFER non-memory reference:** `MONTHLY_TRAIN_MEAN`
- **TRANSFER memory reference:** `PERSISTENCE_LAG1`
- **VALUE statistical reference:** `MONTHLY_TRAIN_MEDIAN`

## 9. SLURM Execution
All baselines are executed on CPU via SLURM array jobs:
- `02_source.sbatch`: Array size 2 (da_cdf, da_nocdf).
- `02_transfer.sbatch`: Array size 8 (2 experiments × 4 targets).
- `02_value.sbatch`: Array size 2 (da_cdf, da_nocdf).
- `02_source_matched_support.sbatch`: Runs matched support analysis (`ZERO`, `TRAIN_MEDIAN`, `MONTHLY_TRAIN_MEDIAN`).
- `02_merge.sbatch`: Collects and validates all outputs into final CSVs.
- `02_audit.sbatch`: Audits final merged outputs.

## 10. Output Structure
Raw job outputs go to `reports/modeling/baselines/raw/`.
Merged final outputs go to `reports/modeling/baselines/` and include:
- `temporal_baseline_metrics.csv`
- `spatial_baseline_metrics.csv`
- `source_matched_support_metrics.csv`
- `baseline_summary.csv`

## 11. Final Audit Requirements
The audit job asserts:
1. 2020 isolation (evaluated_2020_rows == 0).
2. Train-only fitting strictly respected.
3. Identical sample identity across baselines.
4. All expected combinations complete and deduplicated.
5. Finite metrics exist where expected.

## 12. Canonical Baseline Results & Interpretation

### Audit Summary
- **2020 isolation:** PASS
- **Train-only baseline fitting:** PASS
- **Temporal fold completeness:** PASS
- **Spatial fold completeness:** PASS
- **Expected experiment-target matrix:** PASS
- **Duplicate metric keys:** PASS
- **Finite metrics:** PASS
- **Canonical target names:** PASS

### SOURCE
**How difficult is increment-magnitude prediction relative to seasonal climatology?**
Prediction is extremely challenging. The simple `monthly_train_median` captures the vast majority of the predictable signal, outperforming a global median and vastly outperforming a zero-increment baseline.

### TRANSFER
**Which targets are strongly dominated by persistence and which are not?**
- `delta_rzsm` and `delta_baseflow` are overwhelmingly dominated by persistence (`persistence_lag1` R2 > 0.99).
- `delta_surface_runoff` and `delta_et` exhibit less dominance from persistence, highlighting more dynamic response profiles.

### VALUE
**How much predictive structure is already captured by simple climatological baselines?**
A significant baseline structure exists simply through seasonal medians (`monthly_train_median`), setting a modest baseline floor that context-aware ML must significantly surpass to prove predictive utility.

For detailed numbers, consult the canonical merged metrics in `reports/modeling/baselines/`.
