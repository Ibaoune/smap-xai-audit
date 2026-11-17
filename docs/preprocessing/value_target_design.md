# Final Value Target Design and Audit

## Scientific Question
The Value block asks whether Data Assimilation (DA) agrees more closely with an independent ET reference (GLEAM v4.3a) than the Open Loop (OPL) does.

## Evaluation Reference
The canonical harmonized reference is GLEAM v4.3a actual ET on the 4110-cell daily common support. GLEAM remains an external evaluation reference, not ground truth.

## Canonical Value Definition
The ONLY Value metric retained in the final SMAP-XAI workflow is the absolute-error improvement metric (`value_ae`), calculated separately for each DA experiment:

```
value_ae = |ET_OPL - ET_GLEAM| - |ET_DA - ET_GLEAM|
```

(Note: Alternative transformations were examined during development; the final workflow retains only the physically interpretable absolute-error improvement metric value_ae.)

## Physical Interpretation
*   **value_ae > 0**: DA agrees more closely with GLEAM than OPL does under absolute ET error (improved agreement).
*   **value_ae < 0**: DA agrees less closely with GLEAM than OPL does (degraded agreement).
*   **value_ae == 0**: Equal absolute disagreement.

## Units and Sign Convention
*   **Units**: mm/day
*   **Positive sign**: ET agreement improvement relative to GLEAM
*   **Negative sign**: Change in absolute ET disagreement relative to GLEAM

## Common Support
The canonical availability support consists of exactly 4110 cells/day on every one of the 1827 days from 2016-01-01 to 2020-12-31. No temporal aggregation is applied; the canonical target operates at daily resolution.

## High-Coverage Sensitivity Support
A stricter high-land-coverage sensitivity subset of 3871 cells/day containing only target cells with >= 0.99 valid source land fractional coverage was tested. Sensitivity to these partial boundary cells is negligible. 
For example, the absolute difference in mean `value_ae` between the 4110 and 3871 supports is ~0.0003 mm/day, and the change in the positive fraction is < 0.20%. Both support subsets are available for analysis, but the 3871 subset is NOT a second Value target.

## Distribution and Near-Zero Behavior
The `value_ae` distributions are finite and strictly closed for all expected 7,508,970 cell-days (4110 support) with exactly 0 NaNs and 0 Infs.
*   **DA-CDF `value_ae`**: Mean: -0.0312, Median: -0.0411, Skew: 0.41, Kurtosis: 7.01.
*   **DA-NoCDF `value_ae`**: Mean: 0.0035, Median: -0.0183, Skew: 0.55, Kurtosis: 5.47.

GLEAM-zero conditions form a large subset (~22%) and show a distinct `value_ae` distribution. For instance, when GLEAM == 0, the DA-CDF median `value_ae` is -0.0804 (12.5% positive). When GLEAM > 2.0, the DA-CDF median is 0.0258 (54.9% positive).

## Baseline-Error Dependence
The metric inherently depends on the baseline OPL error. Large baseline disagreement permits larger possible absolute agreement changes. 
*   **Q1 Baseline Error**: DA-NoCDF median `value_ae` = -0.0891.
*   **Q4 Baseline Error**: DA-NoCDF median `value_ae` = 0.1473.

## Transfer-vs-Value Relationship
The magnitude of the DA-minus-OPL ET response (`abs(delta_et)`) is very strongly correlated with `abs(value_ae)` (Spearman > 0.91). Large ET responses can correspond to either improved or degraded agreement relative to GLEAM.

## Assimilation-Support Stratification
The `observation_frequency` from the EnKF system was mapped to the harmonized GLEAM support.
*   **No Assimilation (af == 0)**: DA-CDF median = -0.0443 (36.9% positive). DA-NoCDF median = -0.0222 (44.5% positive).
*   **Some Assimilation (af > 0)**: DA-CDF median = -0.0241 (43.6% positive). DA-NoCDF median = -0.0075 (48.6% positive).
DA improves agreement (relatively speaking) in cell-days with some assimilation support compared to cell-days with no assimilation support.

## Seasonal and Yearly Structure
*   **Seasonal mean (CDF)**: DJF (-0.0074), MAM (-0.0372), JJA (-0.0563), SON (-0.0236)
*   **Yearly mean (CDF)**: 2016 (-0.0425), 2017 (-0.0658), 2018 (-0.0038), 2019 (-0.0113), 2020 (-0.0328)

## 2019 SMAP Outage
During the documented period with no assimilated SMAP observations (2019-06-19 to 2019-07-23), expected cell-days (143,850) strictly matched the actual zero-assimilation cell-days (0 mismatches). The `value_ae` distribution remained strictly finite.

## Final Value Contract
The canonical Value target (`value_ae`) is finalized and integrated into the workflow. All alternative experimental candidate metrics have been deprecated and removed from the active data pipeline.
