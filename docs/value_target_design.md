# Value Target Design and Audit

## Scientific Question
The Value block asks whether Data Assimilation (DA) agrees more closely with an independent ET reference (GLEAM v4.3a) than the Open Loop (OPL) does.

## Evaluation Reference
The canonical harmonized reference is GLEAM v4.3a actual ET on the 4110-cell daily common support.

## Candidate Metrics
1. **Absolute-Error Improvement (`value_ae`)**: `abs(e_OPL) - abs(e_DA)`. Positive means DA is closer to GLEAM.
2. **Squared-Error Improvement (`value_se`)**: `e_OPL^2 - e_DA^2`. Emphasizes large errors.
3. **Normalized Absolute-Error Improvement (`value_nae`)**: `(abs(e_OPL) - abs(e_DA)) / (abs(e_OPL) + abs(e_DA) + epsilon)`. Bounded [-1, 1].
4. **Reference-Scaled Improvement (`value_refnorm`)**: `(abs(e_OPL) - abs(e_DA)) / (abs(ET_GLEAM) + epsilon_ref)`.
5. **Log Error Ratio (`log_error_ratio`)**: `log((abs(e_DA) + epsilon) / (abs(e_OPL) + epsilon))`. (Note: sign is inverted).

## Mathematical Relationships
It was verified that `value_se = value_ae * (abs(e_OPL) + abs(e_DA))`. The maximum absolute difference is `< 4.83e-06`. Thus squared-error improvement has identical sign semantics but reweights the sample according to baseline error magnitude.

## Candidate Distributions
All candidate distributions are finite and strictly closed for all expected 7,508,970 cell-days (4110 support) and 7,072,317 cell-days (3871 support), with exactly 0 NaNs and 0 Infs.

**DA-CDF `value_ae`**: Mean: -0.0312, Median: -0.0411, Skew: 0.41, Kurt: 7.01. Top 1% contribution: 6.95%.
**DA-NoCDF `value_ae`**: Mean: 0.0035, Median: -0.0183, Skew: 0.55, Kurt: 5.47. Top 1% contribution: 6.54%.

## Candidate Correlations & Rank-Stability
The evaluated candidate metrics show 100% sign agreement after applying the expected sign inversion for `log_error_ratio`.
Mathematical reason: `value_se`, `value_nae`, and `value_refnorm` all multiply/divide `value_ae` by strictly positive quantities. `log_error_ratio` sign is opposite by construction.
Spearman R vs `value_ae` (DA-NoCDF): `value_se` (0.971), `value_nae` (0.900), `value_refnorm` (0.868), `log_error_ratio` (0.900).

## Support Definitions & Sensitivity
*   **Common Availability (4110 cells)**: Mean `value_ae` (DA-CDF) = -0.0312.
*   **High-Coverage (3871 cells)**: Mean `value_ae` = -0.0316.
Sensitivity to partial boundary cells is negligible (diff mean = 3.7e-04).

## GLEAM-Zero Issue
GLEAM-zero conditions form a large subset (~22%) and show a distinct `value_ae` distribution.
*   **GLEAM == 0**: DA-CDF median = -0.0804 (12.5% positive, 87.5% negative). DA-NoCDF median = -0.0642 (26.7% positive).
*   **GLEAM > 2.0**: DA-CDF median = 0.0258 (54.9% positive). DA-NoCDF median = -0.0458 (45.5% positive).

## Epsilon Sensitivity
*   **value_nae** (`epsilon=1e-6` vs `1e-4` vs `1e-3`): Demonstrates limited sensitivity over the tested epsilon range. Median (-0.0331) and rank-correlation (0.900) remain virtually unchanged across all magnitudes for DA-NoCDF. Top/bottom bounds (-0.9999 to 0.9999) are strictly respected. A numerical deadband is not required for floating-point stability. Whether a scientifically meaningful deadband is desirable remains a separate Value-target design decision.
*   **value_refnorm** (`eps_ref=0.01` vs `0.05` vs `0.1`): `eps_ref=0.01` creates pronounced tail amplification under low-reference ET. For ET_GLEAM much smaller than epsilon_ref, value_refnorm becomes approximately proportional to value_ae, with scaling ~1/epsilon_ref.

## Baseline-Error Dependence
`value_ae` correlates positively with baseline error `abs(e_OPL)` (Pearson R=0.29 for DA-CDF, 0.36 for DA-NoCDF). 
Note: large baseline disagreement permits larger possible absolute agreement changes.
*   **Q1 Baseline Error**: DA-NoCDF median = -0.0891 (13.7% positive).
*   **Q4 Baseline Error**: DA-NoCDF median = 0.1473 (68.0% positive).

## Transfer-vs-Value Relationship (delta_et)
Magnitude of the DA-minus-OPL ET response (`abs(delta_et)`) is very strongly correlated with `abs(value_ae)` (Spearman > 0.91). Large ET responses can correspond to either improved or degraded agreement relative to GLEAM.

## Assimilation-Support Stratification
`assimilated_fraction` was aggregated to GLEAM support.
*   **No Assimilation (af == 0)**: DA-CDF median = -0.0443 (36.9% positive). DA-NoCDF median = -0.0222 (44.5% positive).
*   **Some Assimilation (af > 0)**: DA-CDF median = -0.0241 (43.6% positive). DA-NoCDF median = -0.0075 (48.6% positive).
DA improves agreement (relatively speaking) in observed cells.

## 2019 SMAP Outage
Expected cell-days (143,850) strictly matched the actual zero-assimilation cell-days (0 mismatches). During the documented period with no assimilated SMAP observations, the `value_ae` distribution had DA-CDF median -0.0643 (33.0% pos) and DA-NoCDF median -0.0603 (35.3% pos).

## Temporal Structure
*   **Seasonal mean (CDF)**: DJF (-0.0074), MAM (-0.0372), JJA (-0.0563), SON (-0.0236)
*   **Yearly mean (CDF)**: 2016 (-0.0425), 2017 (-0.0658), 2018 (-0.0038), 2019 (-0.0113), 2020 (-0.0328)

## Remaining Decision Before Canonicalization
Value candidates derived and audited. The final canonical target is still undecided.
