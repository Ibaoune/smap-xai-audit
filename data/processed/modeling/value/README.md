# Block 3: VALUE Modeling Dataset

**Author:** M. El Aabaribaoune

This dataset contains the evaluation of DA-modified ET trajectories against the external GLEAM reference dataset over the exact common spatial support (approx. 0.1 degree).

## Scientific Question
Under what assimilation-source, land-surface, meteorological, and Transfer-response conditions does the DA trajectory reduce absolute ET disagreement relative to the external GLEAM reference?

## Target Definition
The single canonical target is `value_ae`:
`value_ae = abs(ET_OPL - ET_GLEAM) - abs(ET_DA - ET_GLEAM)`

* `value_ae > 0`: DA is closer to GLEAM than OPL (improved agreement).
* `value_ae < 0`: DA is farther from GLEAM than OPL (degraded agreement).

## Support
* Native 0.05-degree predictors are aggregated to the 0.1-degree GLEAM grid using exact spatial overlap area weighting.
* Temporal modeling support: 2016-01-08 through 2020-12-31 (first 7 days removed to ensure complete antecedent history features).
* Spatial support: 4110 valid common cells per day.

## Feature Modes
1. **value_context_feature_set**: Primary contemporaneous explanatory context mode.
2. **value_memory_augmented_feature_set**: Includes antecedent Transfer memory.
3. **value_transfer_informed_feature_set**: Includes contemporaneous realized Transfer responses (explanatory only).
