# Baseline Model Reports

**Author:** M. El Aabaribaoune

This directory contains the computed metrics for all baseline models across SOURCE, TRANSFER, and VALUE tasks. 
Metrics include MAE, RMSE, bias, R2, and Pearson correlation, and relative MAE/RMSE skills.

## Files Generated
- `temporal_baseline_metrics.csv`: Performance of all baselines grouped by target, fold, and experiment over the temporal CV.
- `spatial_baseline_metrics.csv`: Performance of all baselines over the 5-fold balanced spatial-block CV.
- `source_matched_support_metrics.csv`: Sensitivity analysis of SOURCE CDF vs NoCDF baselines using strictly matched spatial-temporal support (computed on validation fold 3).

No raw predictions are persisted to avoid creating massive duplicate datasets. Only summarized results are kept here.
