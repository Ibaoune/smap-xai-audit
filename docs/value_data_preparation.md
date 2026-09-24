# SMAP-XAI Value Data Preparation

## Purpose of Value Block
The Value block of the SMAP-XAI framework asks a distinct question from Source and Transfer: "Under what conditions does the DA trajectory agree more closely with an independent observational reference than the open loop?" To evaluate this, we harmonize the canonical Noah-MP model output with an independent evaluation reference. 

## Primary ET Reference
The variable of interest for this milestone is evapotranspiration (ET). The primary external reference chosen is GLEAM v4.3a. GLEAM is treated strictly as an independent evaluation reference, NOT as a flawless "ground truth" or perfect observation. 

## GLEAM Source Inventory
GLEAM data was located at `data/validation/evapotranspiration/GLEAM/raw/E_*_GLEAM_v4.3a.nc`. 
*   **Complete File List**: 6 files spanning 2015-2020.
*   **Native Variable Name**: `E`
*   **Dimensions**: `('time', 'lat', 'lon')`
*   **Coordinate Orientation**: lat [89.95, -89.95], lon [-179.95, 179.95] (Descending latitude).
*   **Units**: `mm.day-1`
*   **Fill Value**: `-999.0`
*   **Product Version**: 4.3a

## Variable Semantics
*   **Source Variable Name**: `E`
*   **Long Name**: Actual evaporation from GLEAM 4.3a
*   **Units**: `mm.day-1`
This variable matches the required total actual ET flux and is preserved exactly without substituting other sub-fluxes (e.g. potential evaporation).

## Temporal Coverage
*   **Expected Dates (2016-2020)**: 1827
*   **Available Dates**: 1827
*   **Missing Dates**: 0
The 2016-01-01 through 2020-12-31 temporal coverage matches perfectly. No interpolation or leap-day removal is performed.

## Native Grid Geometry
*   **Noah-MP**: First 5 lat centers `[30.0, 30.05, 30.1, 30.15, 30.2]`. Exact grid bounds `29.975 to 36.025` and `-10.025 to -0.975` constructed dynamically via continuous midpoint geometry (Resolution: ~0.050°).
*   **GLEAM**: First 5 lat centers `[89.95, 89.85, 89.75, 89.65, 89.55]`. Exact continuous bounds used (Resolution: ~0.100°).

Because GLEAM cells fall on 0.1° boundaries (e.g. 30.0, 30.1) and Noah-MP cells fall on 0.05° boundaries (e.g. 29.975, 30.025), they do not integer-nest exactly. The half-cell offset means a single interior GLEAM cell boundary will geometrically intersect a 3x3 array of 9 Noah-MP cells.

## Spatial Aggregation Method
GLEAM is NOT upsampled or interpolated onto the fine Noah-MP grid. Instead, the canonical 0.05-degree Noah-MP ET products (OPL, DA-CDF, DA-NoCDF) are conservatively aggregated (upscaled) to the native 0.100-degree GLEAM evaluation grid.

### Exact Spherical Area Weighting
Because grid-cell areas vary slightly over latitude, an exact spherical area-weighting approach is implemented. 
Formula: `A = R^2 * Δλ * [sin(phi_north) - sin(phi_south)]`
Where R = 6371.0 km, and angular quantities are in radians.

### Geometric Coverage Progression
The exact geometric progression of evaluation support cells is:
1.  **Any geometric overlap**: 5,704
2.  **Fully geometrically covered**: 5,400
3.  **Partially covered at domain boundary**: 304
4.  **Cells with ANY valid Noah-MP land overlap**: 4,209

By using exact midpoint-boundary construction over floating-point tile limits, fractions exceeding 1.0 were structurally eliminated (Max geometric fraction: `1.000000`, Max land fraction: `1.000000`).

### Land Coverage Handling
For the 4,209 cells containing valid Noah-MP land:
*   Min valid-land fractional coverage is 0.0625, max is 1.0.
*   Partial cells (< 0.99 coverage) are NOT excluded from the geometry list. Instead, the area-weighted mean is computed exclusively over the valid-land overlap.
*   Normalized weights for these valid components strictly sum to 1.0 (Max deviation: `4.44e-16`).

## Common Evaluation Support
A single, authoritative Boolean common mask (`final_common_mask`) is strictly defined by the intersection of valid (finite) GLEAM observations and valid aggregate Noah-MP models (which rely on non-zero land area).

*   **Common Harmonized Availability Support**: Exactly 4,110 GLEAM cells per day. This support is defined exclusively by data availability (finite GLEAM + finite OPL + finite CDF + finite NoCDF).
*   **Total Common Availability**: 7,508,970 cell-days.
*   **Temporal Consistency**: The exact same 4,110 GLEAM cells form the common availability support on every one of the 1,827 days. (Intersection = 4,110, Union = 4,110, changes = 0).
*   **Closure**: Every diagnostic statistic and distribution table perfectly closes to exactly 7,508,970 cell-days across all four products (GLEAM, OPL, DA-CDF, DA-NoCDF).

### Harmonization Support vs. Future Value Support
It is critical to distinguish basic data availability from the final representativeness criterion for Machine Learning.
*   **Availability**: 4,110 cells/day represent the maximum possible spatial extent where ET data exists across all four products.
*   **Conservative High-Coverage Subset**: 3,871 of these cells have a valid Noah-MP land fractional coverage of `>= 0.99`. This represents a potentially useful subset that avoids any coastal or partial-boundary artifacts.

**IMPORTANT**: Neither 4,110 nor 3,871 are selected as the final XAI-Value training support at this stage. That decision is explicitly deferred to the future Value-target design milestone, avoiding the conflation of raw data availability with strict scientific representativeness.

## Quantitative Conservation Test
Absolute volume conservation was preserved. For every day, the target reconstructed integral `I_target = sum(ET_target_j * valid_overlap_area_j)` was numerically verified against the exact source integral `I_source = sum(ET_source_i * exact_overlap_area_i)` over the valid land coverage. 
Maximum relative error across all 1827 days and all three experiments was `< 2.31e-07`, fully satisfying the `< 1e-5` acceptance tolerance.

## Output Paths
*   **Harmonized Model ET**: `data/processed/value/gleam/model_et/<experiment>/et_on_gleam_YYYY.nc`
*   **Harmonized Reference ET**: `data/processed/value/gleam/reference/gleam_et_YYYY.nc`
*   **Final Boolean Mask**: `data/processed/value/gleam/reference/final_common_mask.npy`
*   **QC Plots/Reports**: `reports/qc/value_gleam/`

## Remaining Steps
*   Process the MOD16 evaluation reference using identical area-weighted aggregation principles.
*   Formalize the final ML target representing XAI-Value.
*   Construct explicit ML samples (incorporating source and transfer insights) to map state improvements to flux evaluation.
