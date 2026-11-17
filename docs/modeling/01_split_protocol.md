# SMAP-XAI Modeling Protocol

**Author:** M. El Aabaribaoune

## 1. Fundamental Anti-Leakage Rule

**RANDOM PIXEL-DAY SPLITTING IS FORBIDDEN.**

The datasets contain substantial temporal autocorrelation, spatial autocorrelation, repeated observations of the same pixels/cells, static predictors repeated across dates, and trajectory persistence. A random row split would place nearly identical spatial/temporal conditions in train and test sets and lead to overly optimistic generalization estimates.

## 2. Primary Temporal Split

The PRIMARY evaluation protocol is defined as:

*   **TRAIN:** 2016-01-08 through 2018-12-31
*   **VALIDATION:** 2019-01-01 through 2019-12-31
*   **TEST:** 2020-01-01 through 2020-12-31

For SOURCE, use all available finite-innovation-selected samples falling inside those dates.
For TRANSFER and VALUE, use their complete modeling support inside those dates.
Do NOT rebalance years. Do NOT randomly sample test rows.

## 3. Pre-Test Expanding-Window Temporal CV

In addition to the primary split, a pretest temporal CV is defined for robust pre-test hyperparameter/model comparison. 2020 MUST NOT participate.

*   **Fold 1:** Train: 2016-01-08 -> 2016-12-31 | Val: 2017-01-01 -> 2017-12-31
*   **Fold 2:** Train: 2016-01-08 -> 2017-12-31 | Val: 2018-01-01 -> 2018-12-31
*   **Fold 3:** Train: 2016-01-08 -> 2018-12-31 | Val: 2019-01-01 -> 2019-12-31

## 4. Final Model-Development Rule

During development, hyperparameters/model choices may be informed by pretest_temporal_cv and/or 2019 validation.
After model design is frozen, **refit final selected model on 2016-2019**, then evaluate **ONCE on 2020 final test**. Do not use 2020 SHAP/results to modify the model. 2020 remains untouched.

## 5. Spatial-Block Sensitivity Design

A spatial-block grouping independent of model resolution is created using geographic coordinates rather than native array indices.

*   **Primary spatial block size:** 1.0 degree latitude × 1.0 degree longitude
*   **Anchoring:** Blocks are anchored to integer-degree geographic boundaries (e.g., `lat_block = floor(latitude)`).
*   **Consistency:** A stable `spatial_block_id` is derived. A geographic block is never split. The same `spatial_block_id` receives the same fold for Noah-MP and GLEAM.

## 6. Spatial Fold Assignment

Spatial blocks are assigned to **5 deterministic folds** using a BALANCED geometric support weight.
*   `block_weight = (n_noahmp_cells / total_noahmp) + (n_gleam_cells / total_gleam)`
*   Blocks are sorted by descending `block_weight`, tie-broken by `spatial_block_id`.
*   Blocks are assigned greedily to the fold with the smallest total block weight, tie-broken by lowest fold integer.

This uses ONLY spatial geometric information, and avoids target values, experiment outcomes, etc.

## 7. Spatial CV Remains A Different Question

*   **Temporal holdout:** future-year generalization within the same geographic domain.
*   **Spatial block CV:** geographic generalization to unseen 1-degree blocks.
*   **Pretest temporal CV:** robustness of model selection across unseen years before final test.
Do NOT average temporal and spatial scores into a single performance number.

*(Optional Future Buffered Spatial Test: A future stricter sensitivity may add a geographic buffer around held-out spatial blocks to reduce train-test adjacency. Current 1-degree grouped CV remains the primary spatial sensitivity.)*

## 8. Verify Feature Modes Share Exactly the Same Splits

Feature modes (e.g. source_context, memory_augmented) MUST share EXACTLY the same splits. Changing feature mode does not change row membership in temporal/spatial splits. Splitting is independent of feature selection.

## 9. Dataset Integrity

No split columns are added to the canonical SOURCE/TRANSFER/VALUE Parquets. Splits must be derived dynamically from date and location.
