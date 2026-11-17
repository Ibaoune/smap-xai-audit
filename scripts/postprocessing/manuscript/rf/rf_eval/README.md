# Random Forest Performance Evaluation Suite (Figure 4 Refactor)

This directory contains scripts and documentation for rebuilding **Figure 4** of the SMAP-XAI manuscript using standard regression metrics ($R^2$, Pearson $r$, MAE, RMSE, Bias) computed strictly from frozen baseline evaluation datasets.

---

## 1. Directory Structure & File Inventory

### Scripts (`scripts/postprocessing/manuscript/rf/rf_eval/`)
- **`build_rf_eval_metrics.py`**:
  Aggregates, filters, and standardizes metrics from frozen model report directories into figure source CSV files, robustness spatial-CV summaries, and the supplementary summary table (`TableS2_RF_2020_metrics.csv`).
- **`plot_figure4_rf_validation.py`**:
  Generates publication-quality 2 × 2 symmetric panel figures in high-resolution raster (PNG, 500 DPI) and vector (PDF) formats directly from `Figure4_2019_temporal_validation_metrics.csv` and `Figure4_2020_holdout_metrics.csv`.
- **`README.md`**:
  This document.

### Output Artifacts (`figures/manuscript/rf/rf_eval/`)
- **Figure Artifacts**:
  - `Figure_4_RF_validation_standard_metrics.png` (500 DPI, symmetric 4-panel layout)
  - `Figure_4_RF_validation_standard_metrics.pdf` (vector format)
- **Source Data Tables**:
  - `Figure4_2019_temporal_validation_metrics.csv`: 2019 temporal validation regression metrics ($N=12$).
  - `Figure4_2020_holdout_metrics.csv`: 2020 independent holdout regression metrics ($N=12$).
- **Robustness Data Tables (Spatial-CV, retained for prose & supplement)**:
  - `Figure4_spatial_block_cv_metrics.csv`: Per-fold metrics for 5-fold spatial-block CV ($N=15$).
  - `Figure4_spatial_block_cv_summary.csv`: Summary statistics (mean ± SD) across spatial folds ($N=3$).
- **Supplementary Table**:
  - `TableS2_RF_2020_metrics.csv`: Authoritative Table S2 containing sample sizes ($N$) and regression metrics for all 12 target/experiment pairs on the 2020 holdout.

---

## 2. Data Provenance & Metric Extraction

All metrics are derived directly from previously frozen model evaluations without retraining or running new inferences:

1. **2019 Temporal Validation (Panels a & b)**:
   - **Protocol**: Trained on 2016-01-08 to 2018-12-31; validated on 2019-01-01 to 2019-12-31 (`fold_3`).
   - **Panel (a)**: Coefficient of determination ($R^2$).
   - **Panel (b)**: Pearson correlation coefficient ($r$).
   - **Source Artifacts**:
     - `reports/modeling/models/random_forest/rf03b/rf03b_source_matched_metrics.csv` (SOURCE matched-support models: $N=515,112$).
     - `reports/modeling/models/random_forest/rf03b/rf03b_primary_metrics.csv` (TRANSFER: $N=5,850,950$; VALUE: $N=1,500,150$).
   - **Note on Support**: For SOURCE, native-support runs are excluded in favor of matched-support models to ensure an unbiased CDF vs. NoCDF evaluation on identical grid-cell days.

2. **Independent 2020 Holdout (Panels c & d, Table S2)**:
   - **Protocol**: Refitted on the full 2016–2019 period; evaluated on 2020-01-01 to 2020-12-31.
   - **Panel (c)**: Coefficient of determination ($R^2$).
   - **Panel (d)**: Pearson correlation coefficient ($r$).
   - **Source Artifact**: `reports/modeling/final_2020/final_metrics_2020.csv`
   - **Sample Counts**:
     - SOURCE (matched support): $N = 596,877$ for both CDF and NoCDF.
     - TRANSFER (native support): $N = 5,866,980$ across all targets.
     - VALUE (native support): $N = 1,504,260$ for both CDF and NoCDF.

3. **Five-fold Spatial-Block Cross-Validation (Robustness Check)**:
   - **Protocol**: 5-fold spatial cross-validation trained on 2016–2019 spatial blocks (`spatial_0` through `spatial_4`).
   - **Scope & Role**: Evaluated for the three representative CDF models (SOURCE RF_A, TRANSFER RZSM RF_A, and VALUE RF_B) under milestone RF-03A. Maintained in the data repository for manuscript prose and supplementary material.

---

## 3. Execution Pipeline

To rebuild metrics and render the figure from the project root:

```bash
# Step 1: Extract and validate source data tables
python scripts/postprocessing/manuscript/rf/rf_eval/build_rf_eval_metrics.py

# Step 2: Render Figure 4
python scripts/postprocessing/manuscript/rf/rf_eval/plot_figure4_rf_validation.py
```

---

## 4. Benchmark Summary (2020 Independent Holdout)

| Target | Experiment | $N$ | MAE | RMSE | Bias | $R^2$ | Pearson $r$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **SOURCE** | CDF | 596,877 | 0.005755 | 0.008649 | +0.000112 | **0.5800** | **0.7618** |
| **SOURCE** | NoCDF | 596,877 | 0.007410 | 0.012483 | -0.000219 | **0.2441** | **0.4954** |
| **RZSM** | CDF | 5,866,980 | 0.011639 | 0.017867 | +0.001906 | **0.2815** | **0.5384** |
| **RZSM** | NoCDF | 5,866,980 | 0.014674 | 0.021750 | +0.002009 | **0.4750** | **0.7093** |
| **ET** | CDF | 5,866,980 | 0.119465 | 0.194682 | -0.000779 | **0.6343** | **0.7972** |
| **ET** | NoCDF | 5,866,980 | 0.149764 | 0.250598 | -0.037929 | **0.5666** | **0.7597** |
| **Surface runoff** | CDF | 5,866,980 | 0.000961 | 0.008935 | +0.000370 | **0.2896** | **0.5452** |
| **Surface runoff** | NoCDF | 5,866,980 | 0.002643 | 0.038516 | -0.000778 | **0.4649** | **0.7233** |
| **Baseflow** | CDF | 5,866,980 | 0.005208 | 0.031135 | +0.001643 | **0.2428** | **0.5022** |
| **Baseflow** | NoCDF | 5,866,980 | 0.028569 | 0.180854 | -0.012304 | **0.3292** | **0.6009** |
| **VALUE** | CDF | 1,504,260 | 0.109749 | 0.178005 | +0.003042 | **0.3011** | **0.5517** |
| **VALUE** | NoCDF | 1,504,260 | 0.148394 | 0.240042 | +0.014953 | **0.3114** | **0.5683** |
