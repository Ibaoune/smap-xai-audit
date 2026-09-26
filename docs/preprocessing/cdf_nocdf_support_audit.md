# DA-CDF vs DA-NoCDF Finite-Innovation Support Audit

**Author:** M. El Aabaribaoune

## 1. Audit Question
Why does the `DA-NoCDF` experiment map approximately 3 times as many finite EnKF innovation diagnostics to valid land pixels compared to the `DA-CDF` experiment? Is this difference primarily temporal (NoCDF assimilates on days CDF does not) or spatial (NoCDF assimilates at pixels CDF rejects on the same day)?

## 2. Exact `observation_frequency` Definition
In this project, `observation_frequency == 1` means exactly: the corresponding daily pixel contains a finite native EnKF innovation diagnostic for that experiment. It is *not* a raw SMAP availability flag.

## 3. Native Event Timestamps Comparison
Over the 2016-2020 domain, the exact event timestamps recorded in the native `innovation_YYYY.nc` files are:
- **CDF total event timestamps:** 4,411
- **NoCDF total event timestamps:** 4,619
- **Common event timestamps:** 4,410
- **CDF-only timestamps:** 1
- **NoCDF-only timestamps:** 209

While NoCDF has 209 additional distinct assimilation events, this temporal difference is insufficient to explain the ~5 million pixel-day support discrepancy.

## 4. Temporal vs. Spatial Support Decomposition
To isolate spatial differences, the native pixel-events were cross-tabulated strictly at the **4,410 Common Event Timestamps** over the canonical Noah-MP valid-land mask (16,030 pixels):
- **BOTH (CDF & NoCDF finite):** 2,441,779
- **CDF_ONLY (CDF finite, NoCDF missing):** 14,451
- **NOCDF_ONLY (NoCDF finite, CDF missing):** 5,057,301
- **NEITHER (Both missing):** 63,178,769

*(Note: Previous percentages used a restricted 14,250-pixel mask comprising only pixels that received at least one update across the 5 years. The finite-support counts remain exactly unchanged under the full 16,030-pixel canonical land mask; only the NEITHER denominator correctly expands by 1,780 pixels per timestamp).*

**Excess Support Decomposition:**
Total excess NoCDF finite support relative to CDF across all timestamps is 5,051,408 pixel-days.
- **Contribution from NoCDF-only native timestamps (net):** 8,558 (0.2%)
- **Net contribution from shared timestamps:** 5,042,850 (99.8%)

**Conclusion:** The difference is overwhelmingly a finite-innovation spatial-support difference at shared timestamps. Even when the exact same assimilation event timestamp exists in both experiments, NoCDF maps finite innovations to a significantly wider spatial area.

## 5. Daily Support Comparison
The native-event totals map perfectly to the previously audited canonical daily datasets via experiment-only timestamp additions:
- **DA-CDF Retained Rows:** 2,441,779 (BOTH) + 14,451 (CDF_ONLY) + 3 (CDF-only timestamps) = **2,456,233**
- **DA-NoCDF Retained Rows:** 2,441,779 (BOTH) + 5,057,301 (NOCDF_ONLY) + 8,561 (NoCDF-only timestamps) = **7,507,641**
*(These exactly match the pre-lag daily counts before filtering for 7-day antecedent history availability).*

## 6. Representative Diagnostic Cases (Timestamp: 2016-07-11T07:00:00)
**NOCDF_ONLY Cases:**
- `(y=0, x=18)`: CDF innovation=NaN, NoCDF innovation=0.0227, NoCDF FV=0.001623
- `(y=0, x=19)`: CDF innovation=NaN, NoCDF innovation=0.0065, NoCDF FV=0.002510
- `(y=0, x=20)`: CDF innovation=NaN, NoCDF innovation=-0.0282, NoCDF FV=0.002906

**BOTH Cases:**
- `(y=0, x=12)`: CDF innovation=0.0025, NoCDF innovation=0.0142
- `(y=0, x=13)`: CDF innovation=-0.0045, NoCDF innovation=-0.0163

*Observation:* At exactly the same time, adjacent pixels are processed by NoCDF but explicitly masked/dropped by CDF before or during the innovation calculation.

## 7. Native Variables Available for Tracing
The downstream EnKF interim diagnostic files contain only:
`analysis_residual`, `normalized_innovation`, `innovation`, `increment_signed`, `forecast_variance`.
They do **not** contain raw SMAP L2 availability flags, CDF-matching ancillary valid-pixel masks, or exact QC rejection codes.

## 8. Conclusion Level

**ESTABLISHED:**
The support difference occurs predominantly at shared event timestamps (99.8% of the excess) as a spatial finite-innovation-support difference.

**UNRESOLVED:**
The exact upstream mechanism (why the CDF branch lacks a finite innovation at those specific locations) remains LEVEL 3 — UNRESOLVED. The exact cause (e.g., CDF-matching pixel validity, differing QC thresholds, or observation preprocessing masks) cannot be isolated because raw source SMAP flags and CDF-matching ancillary tables are not persisted in these downstream EnKF interim diagnostics. A dedicated upstream observation-processing audit would be required. This must not be casually attributed to CDF matching itself without direct evidence.

## 9. Implications for SOURCE Sampling
The difference in valid assimilation support is a real feature of the EnKF diagnostics. The SOURCE datasets correctly capture the experiment-specific conditional samples (Given an update occurred in *this* experiment, what drove it?). The discrepancy is documented, and the SOURCE generation logic correctly remains as implemented.

### Matched-Support Modeling Implication
Primary SOURCE modeling uses experiment-specific conditional samples. However, any DIRECT CDF-vs-NoCDF model or XAI comparison should include a matched-support sensitivity analysis restricted to `BOTH` (shared pixel-days where both branches successfully generated a finite innovation). Otherwise, differences in model behavior or XAI attributions may reflect the different sampled locations/times rather than strictly the differences between the assimilation algorithms. This matched subset can be obtained dynamically by inner-joining `date` + `y_index` + `x_index` between the two canonical SOURCE tables.
