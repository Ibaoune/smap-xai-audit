# SMAP-XAI Model Diagnostics and Known Numerical Characteristics

**Project:** SMAP-XAI Audit
**Author:** M. El Aabaribaoune (@um6p)

## 1. Purpose of this Document

This document distinguishes preprocessing problems from upstream model and Data Assimilation (DA) numerical characteristics. The row-wise structures described below were discovered during preprocessing quality control (QC), but they originate natively in the original LIS DA outputs. This document is written for hydrologists, Earth scientists, and XAI researchers, clarifying the numerical mechanism without requiring specialized knowledge in random-number generation or MPI (Message Passing Interface) parallelization.

## 2. Row-wise spatial structures in DA water-flux responses

During preprocessing QC, distinct horizontal / latitude-aligned structures were discovered in the water-flux fields:
- Evapotranspiration (ET)
- Surface runoff
- Baseflow

These stripes are especially prominent in the difference fields (e.g., DA-CDF minus OPL). 
- OPL fields (Open Loop, no assimilation) are comparatively smooth.
- Some DA-minus-OPL fields show alternating, horizontal row-wise structures (stripes).
- Raw-versus-interim checks definitively prove that these structures already exist in the raw LIS outputs. 
- Routine preprocessing steps—such as extraction, unit conversion, coordinate handling, timestamp shifting, temporal averaging, and plotting—were entirely ruled out as causes.

## 3. Ensemble Perturbations

In the EnKF (Ensemble Kalman Filter) data assimilation system, the model runs 20 parallel ensemble members. To generate this ensemble, small random perturbations (noise) are added to the meteorological forcing and model states. The spread (variance) among these 20 ensemble members represents the model's uncertainty, which is just as important to the assimilation process as the ensemble mean.

## 4. Gaussian Pair Generation

The LIS random-number routine uses a standard mathematical algorithm (Box-Muller / Marsaglia polar method) to generate random perturbations. A known characteristic of this algorithm is that it generates two Gaussian (normal) random values at once. 
Importantly, these two Gaussian values are mathematically independent. The pairing of values by the Box-Muller algorithm itself is NOT the diagnosed issue.

## 5. LIS Grid-Mapping Behavior

The mechanism creating the stripes originates from how the LIS model maps these paired Gaussian values onto the spatial grid (`generate_white_field`):
- The routine traverses the native grid, iterating over latitude rows (inner loop) for each longitude column.
- On the first row, it calls the random-number generator, receives a pair of Gaussian values, assigns the first value immediately to the cell, and caches the second value.
- On the second row, instead of calling the generator again, it simply consumes the cached second value.
- Because the second row consumes a cached value, it does not invoke or update its own cell-specific random-number seed. 
- Furthermore, the cell-specific random seeds are initialized deterministically based on their global grid index.

Conceptually:
    Row 1 -> generate pair -> use z1, cache z2
    Row 2 -> use cached z2
    Row 3 -> generate pair -> use z1, cache z2
    Row 4 -> use cached z2

This means that odd rows strictly receive the *first* generated value of a pair, and even rows strictly receive the *second*.

## 6. Finite Ensemble Effect

The ensemble contains only 20 members. Because this sample size is small, the finite-sample variance across the 20 members does not perfectly converge to theoretical perfection.

Exact reproduction of the LIS algorithm confirmed:
- Odd and even rows possess systematic differences in their ensemble variance.
- Representative differences in variance reached approximately 1–4%.
- A local period-2 (alternating row-by-row) structure was explicitly reproduced.

Although the LIS system applies an `adjust_mean` step to ensure the ensemble *mean* perturbation is exactly zero, it does not equalize the *variance*. Thus, the ensemble mean is perfectly zero, while the ensemble variance remains systematically different between odd and even rows.

## 7. MPI Domain Decomposition

MPI (Message Passing Interface) domain decomposition is the method LIS uses to split the global grid into smaller local blocks so they can be processed in parallel across multiple CPUs.
- x-processors = 4
- y-processors = 8

Because the global grid is split into these local blocks, the number of local rows on a given processor tile can be an odd or even number. 
If a local block has an odd number of rows (e.g., 15), the cached Gaussian-pair assignment carries over to the next column, changing the phase (flipping the odd/even alignment). Diagnostic comparisons found exact correspondence between these predicted local-domain phase boundaries and the observed spatial pattern breaks in the data. This verifies the interaction, but it does not imply that MPI itself is defective.

## 8. Nonlinear Amplification by Noah-MP

Noah-MP fluxes (like ET and runoff) are highly nonlinear functions of the land surface state. 
A very small change in soil moisture can trigger a disproportionately larger change in ET, runoff, or baseflow. This occurs because physical processes depend on strict thresholds, such as:
- Moisture stress functions
- Infiltration limits
- Drainage curves
- Vegetation response
- Hydraulic thresholds

A diagnostic example from the data:
    delta SSM  ~ +0.001
    delta RZSM ~ -0.003
    delta ET   ~ +1.024 mm day-1

This demonstrates that a tiny state perturbation can undergo massive amplification. The alternating variance between odd and even rows in the soil moisture perturbations is nonlinearly amplified by these thresholds into an alternating *mean* response in the fluxes.

## 9. Variable-Specific Response

The striping pattern is not equally strong in all variables. Diagnostic row-to-row variability (standard deviation of adjacent row differences) yielded:
    SSM  ~ 0.0031
    RZSM ~ 0.0040
    ET   ~ 0.0538
    Qs   ~ 0.0014
    Qsb  ~ 0.0093

Evapotranspiration (ET) showed the strongest amplification in this diagnostic, while surface runoff (Qs) was much weaker. Note that this ordering applies strictly to the analyzed experiments and is not necessarily a universal rule.

## 10. What Has Been Ruled Out

| Candidate cause | Status | Evidence |
| :--- | :--- | :--- |
| Preprocessing extraction | ruled out | raw-vs-interim equality |
| Timestamp shift | ruled out | same structures in raw daily fields |
| Plotting | ruled out | daily raw fields contain structure |
| Coordinate orientation | verified | structure follows north_south index |
| Simple SMAP swath footprint | not supported | |
| Static elevation/soil/land-cover boundaries | not supported as primary explanation | |
| Box-Muller correlation | ruled out | paired Gaussian values are independent |
| Perturbation/indexing implementation | supported | |
| Nonlinear flux amplification | supported | |

## 11. What This Does Not Mean

- The structure is **not** interpreted as a physical geographic signal.
- The structure does **not** imply that all DA results are invalid.
- **No preprocessing correction** has been applied.
- **No values** were filtered or smoothed.
- Broad-scale and fine-scale implications may differ significantly.
- A controlled sensitivity experiment is still required before deciding whether existing DA experiments should be regenerated.

## 12. Implications for XAI

Because Machine Learning models are highly sensitive to spatial patterns, future pixel-day XAI models may learn both:
- physical relationships, AND
- numerical structures inherited from the DA system.

Particular caution is required for:
- pixel-level SHAP maps
- fine-scale spatial attribution
- local feature importance
- row-scale interpretation

Regional or domain-average analyses may be less sensitive, but one should not assume they are unaffected without rigorous testing.

## 13. Planned Sensitivity Test

A future controlled experiment is planned to evaluate the exact impact:
- **Period**: 2016 initially
- **Experiment**: preferably DA-CDF first
- **Keep fixed**: forcing source, SMAP observations, observation errors, ensemble size, CDF settings, Noah-MP configuration, initial conditions.
- **Change only**: perturbation-field generation / RNG-grid mapping.

Metrics for comparison:
- increment, SSM, RZSM, ET, surface runoff, baseflow.

Objectives:
- Determine whether row-wise structures disappear.
- Quantify changes in domain-scale statistics.
- Determine the impact on future pixel-level XAI.

*(Note: This experiment is not being implemented at this time).*

## 14. Evidence vs Interpretation

**Confirmed:**
- raw structures exist in model output
- strict row orientation
- period-2 perturbation variance alternating behavior
- exact RNG reproducer demonstrates variance bias
- MPI-related spatial phase-flipping behavior
- nonlinear flux amplification

**Interpretation:**
- how strongly this affects scientific DA conclusions
- how strongly it affects XAI
- whether experiments need full regeneration
