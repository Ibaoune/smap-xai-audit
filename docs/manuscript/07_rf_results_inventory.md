# RF-07 Results Inventory

| Manuscript Section | Figure / Table | Panel | Exact Canonical Input File | Variable/Column Used | Support Used | Full-Support or XAI-Cohort | Aggregation Applied |
|---|---|---|---|---|---|---|---|
| 3.1 | Figure 3 | (a) | `da_nocdf/daily_innovation/*.nc` | `daily_innovation` | Native EnKF | Full-Support | `count(dim='time')` |
| 3.1 | Figure 3 | (b) | `da_nocdf/daily_innovation/*.nc` | `daily_innovation` | Native EnKF | Full-Support | `mean(dim='time')` |
| 3.1 | Figure 3 | (c) | `da_cdf/daily_innovation/*.nc` and `da_nocdf/daily_innovation/*.nc` | `daily_innovation` | Native EnKF | Full-Support | Flattened distributions |
| 3.1 | Figure 3 | (d) | `da_nocdf/daily_signed_increment/*.nc` | `daily_signed_increment` | Native EnKF | Full-Support | `mean(dim='time')` |
| 3.1 | Figure 3 | (e) | `da_cdf/daily_signed_increment/*.nc` | `daily_signed_increment` | Native EnKF | Full-Support | `mean(dim='time')` |
| 3.1 | Figure 3 | (f) | `da_cdf/daily_absolute_increment/*.nc` and `da_nocdf/daily_absolute_increment/*.nc` | `daily_absolute_increment` | Native EnKF | Full-Support | `groupby('time.season').mean(dim=['time', 'lat', 'lon'])` |
| 3.2 | Figure 4 | (a) | `rf03b_source_matched_metrics.csv`, `rf03b_primary_metrics.csv` | `MAE_skill` | Matched (SOURCE) & Native | Full-Support | Temporal Validation CV average |
| 3.2 | Figure 4 | (b) | `rf02_source_fold_metrics.csv`, `rf02_transfer_fold_metrics.csv`, `rf02_value_fold_metrics.csv` | `MAE_skill` | Native | Full-Support | 5-Fold Spatial CV Average |
| 3.2 | Figure 4 | (c) | `final_metrics_2020.csv` | `MAE_skill` | Matched (SOURCE) & Native | Full-Support | Frozen 2020 Holdout |
| 3.2 | Figure 4 | (d) | `final_metrics_2020.csv` | `R2` | Matched (SOURCE) & Native | Full-Support | Frozen 2020 Holdout |
| 3.3 | Figure 5 | (a) | `tidy_group_summary.csv` | `normalized_group_importance` | Matched | XAI-Cohort | Grouped SHAP average |
| 3.3 | Figure 5 | (b) | `tidy_predictor_summary.csv` | `mean_abs_shap` | Matched | XAI-Cohort | Top 10 mean \|SHAP\| |
| 3.3 | Figure 5 | (c) | `shap_SOURCE_*_matched_support_cohort.parquet` | `shap__ssm_lag1`, `value__ssm_lag1` | Matched | XAI-Cohort | None (scatter points) |
| 3.3 | Figure 5 | (d) | `shap_SOURCE_*_matched_support_cohort.parquet` | `shap__precip_lag1`, `value__precip_lag1` | Matched | XAI-Cohort | None (scatter points) |
| 3.4 | Figure 6 | (All) | `tidy_group_summary.csv` | `normalized_group_importance` | Native | XAI-Cohort | Filtered for TRANSFER targets |
| 3.5 | Figure 7 | (a) | `VALUE_da_*_value_ae_native_support_cohort.parquet` | `value_ae` | Native | Full-Support | Positive fractions exact full-support |
| 3.5 | Figure 7 | (b) | `tidy_group_summary.csv` | `normalized_group_importance` | Native | XAI-Cohort | Filtered for VALUE targets |
| 3.5 | Figure 7 | (c) | `tidy_predictor_summary.csv` | `mean_abs_shap` | Native | XAI-Cohort | Top 10 predictors for VALUE |
| 3.5 | Figure 7 | (d) | `shap_VALUE_*_native_support_cohort.parquet` | `shap__et_opl_lag1`, `value__et_opl_lag1` | Native | XAI-Cohort | None (scatter points) |
| 3.5 | Figure 7 | (e) | `shap_VALUE_*_native_support_cohort.parquet` | `shap__tair_t`, `value__tair_t` | Native | XAI-Cohort | None (scatter points) |
| 3.5 | Figure 7 | (f) | `shap_VALUE_*_native_support_cohort.parquet` | `shap__land_cover_fraction_16`, `value__land_cover_fraction_16` | Native | XAI-Cohort | None (scatter points) |
| 3.6 | Figure 8 | (All) | `tidy_group_summary.csv` | `normalized_group_importance` | Matched (SOURCE), Native | XAI-Cohort | Removed SOURCE native |
