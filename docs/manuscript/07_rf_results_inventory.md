# RF-07 Results Inventory

| Manuscript Section | Scientific Question | Figure / Table | Canonical Numerical Source |
|---|---|---|---|
| 3.1 | What soil-moisture signal enters the assimilation system, and how does CDF matching modify the resulting analysis updates? | Figure 3 | Pre-computed diagnostic maps and `reports/qc/` distribution summaries |
| 3.2 | Are SOURCE, TRANSFER, and VALUE sufficiently predictable to support subsequent XAI interpretation? | Figure 4, Table 2 | `reports/modeling/final_2020/final_metrics_2020.csv` + frozen RF-04 block CV metrics |
| 3.3 | Under which antecedent conditions are large soil-moisture updates predicted, and how does the explanatory structure differ between CDF and NoCDF? | Figure 5, S1, S3, S7 | SOURCE final 2020 XAI summaries, `tidy_group_summary.csv` |
| 3.4 | How does the explanatory structure of the DA-minus-OPL response differ across RZSM, ET, surface runoff, and baseflow? | Figure 6, S4, S8 | TRANSFER final 2020 XAI summaries, `tidy_group_summary.csv` |
| 3.5 | Under which conditions is assimilation associated with lower or higher ET disagreement relative to the independent GLEAM reference? | Figure 7, S5, S9 | VALUE final 2020 XAI summaries, `tidy_group_summary.csv` |
| 3.6 | How does the explanatory structure reorganize from the initial soil-moisture update to downstream land responses and external ET value? | Figure 8 | Synthesized from `tidy_group_summary.csv` |
| Supplementary | Robustness of attribution to seasonal differences | S3, S4, S5, Table S6 | `seasonal_group_summary_2020.csv` |
| Supplementary | Robustness of attribution to spatial variability | S6, Table S7 | `spatial_group_stability_2020.csv` |
| Supplementary | Robustness of attribution across XAI methods | S2, Table S5 | `robustness_*.json` outputs |
| Supplementary | Final Frozen Predictor and Group Registry | Table S1, Table S8 | `configs/xai/feature_groups.yaml`, `dependence_summary_2020.csv` |
