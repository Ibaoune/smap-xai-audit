# Random Forest XAI Protocol (RF-04)

## 1. Development and Validation Setup
The entire Explainable AI (XAI) protocol is developed, balanced, and frozen using the canonical
**2019 validation period**. 2020 remains sealed. This builds upon the
[Random Forest Development Matrix](../../docs/modeling/06_random_forest_development_matrix.md).

The identical cohort-generation algorithm and explanation settings will be applied later to the
final 2020 independent test set. No parameter or predictor-group definition may be changed after
unsealing 2020.

## 2. Conceptual Boundaries

| Concept | Definition |
|---|---|
| Predictive Modeling | Fitting the model to minimise error against a target (RF-01 to RF-03) |
| Model Explanation | Quantifying how the fitted model uses inputs to produce its predictions (RF-04) |
| Scientific Interpretation | Synthesising explanations within physical domain knowledge |
| Causal Inference | Estimating the true physical impact of an intervention — **not done here** |

**Explicit Statement**: SHAP explains the fitted RF predictions. It does not establish physical causality.
SHAP provides a rigorous mathematical allocation of predictive variance among inputs,
but due to feature correlation and observational constraints, these allocations cannot be
strictly interpreted as isolated physical causal effects.

## 3. Cohort Design

### 3.1 Cohort Index (50,000 rows per block)
For each block (SOURCE native CDF, SOURCE native NoCDF, SOURCE matched, TRANSFER, VALUE),
a deterministic cohort index of **50,000 pixel-days** is generated and stored as a Parquet file.
The index is balanced across `month × spatial_fold` cells using seed 42.
Target-stratification is **forbidden**.

### 3.2 SHAP Compute Subset (10,000 rows)
SHAP values are computed on a **10,000-row deterministic balanced sub-sample** nested within
the 50k cohort index.

**Rationale for 10k**: RF_A uses 300 trees with max_depth=12 and ~2700 leaves per tree.
Full-cohort TreeSHAP at 50k rows requires ~200 minutes per model; the 10k subset requires
~47 minutes while producing stable importance rankings.

**Sample-size stability audit** (RF-04B closure, SOURCE da_cdf matched support):

| Comparison | Predictor rank ρ | Top-10 overlap | Group ρ | Max group diff |
|---|---|---|---|---|
| 5,000 vs 10,000 rows | 0.9989 | 10/10 | 1.0000 | 0.016 |

**Decision**: 10k is frozen. Do not change without a documented technical failure.

### 3.3 Permutation Compute Subset (5,000 rows)
Permutation importance is computed on the **first 5,000 rows** (by sorted date, y_index, x_index)
of the 10k SHAP compute cohort — strictly nested within it.

## 4. Feature Registry

| Scope | Count |
|---|---|
| Global XAI feature-group registry (`feature_groups.yaml`) | 58 unique predictors |
| SOURCE `context_only_feature_set` active predictors | **35** |
| TRANSFER/VALUE (planned) | different subsets |

The global registry maps all 58 predictors to 9 scientific groups and is authoritative for all
future model families. SOURCE models only use the 35-predictor subset; groups containing features
absent from a given model will produce zero group importance and are correctly excluded.

## 5. Matched-Support Interpretation

Results from the **matched SOURCE cohort** (`source_matched_2019.parquet`) are a
**matched-support direct comparison**: CDF and NoCDF models are evaluated on **identical
pixel-days**.

**Correct wording**:
> On identical matched pixel-days, CDF and NoCDF show highly concordant predictor and group
> rankings (predictor rank ρ = 0.951, group ρ = 0.948), while the relative distribution
> of predictive attribution differs between some scientific groups.

**Do NOT write**:
- "native-support characterization" when describing matched results
- "CDF caused predictor X to become important"
- Any causal attribution of support-matched differences to the assimilation mechanism

**Native-support results** (native CDF, native NoCDF) must be labelled explicitly as
"native-support characterization" and must NOT be compared directly as CDF vs NoCDF differences.

## 6. TreeSHAP Configuration (Frozen)
- **Explainer**: `shap.TreeExplainer`
- **feature_perturbation**: `tree_path_dependent`
- **model_output**: `raw`
- **Library**: SHAP 0.51.0

## 7. Plotting Environment
Development figures use **matplotlib only**. Seaborn was installed ad-hoc during RF-04B
development and removed from the plotting code at RF-04B closure. `environment.yml` does
NOT include seaborn.

## 8. Cross-links
- [XAI README](README.md)
- [RF Development Matrix](../../docs/modeling/06_random_forest_development_matrix.md)
- [Cohort Design](02_xai_cohort_design.md)
- [Feature Group Contract](03_feature_group_contract.md)
- [RF SHAP Methodology](04_rf_shap_method.md)
- [SOURCE XAI Results](06_source_xai.md)
