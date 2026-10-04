# SMAP-XAI Explainable AI Protocol

This directory contains the documentation and scientific protocols for the Explainable AI (XAI) stages of the SMAP-XAI Audit project.

## Important Definitions

- **Predictive Modeling**: Fitting the model to minimize error against a target (RF-01 to RF-03).
- **Model Explanation**: Quantifying how the fitted model uses inputs to produce its specific predictions (RF-04 onwards).
- **Scientific Interpretation**: Synthesizing explanations within the context of physical domain knowledge.
- **Causal Inference**: Estimating the true physical impact of an intervention.

**Explicit Statement**: SHAP explains the fitted RF predictions. It does not establish causal effects. SHAP provides a rigorous mathematical allocation of the model's predictive variance among the input features, but due to feature correlation and observational constraints, these allocations cannot be strictly interpreted as isolated physical causal impacts.

## Stage Status Table

| Stage | Status |
|---|---|
| RF-04A protocol/cohorts | COMPLETE |
| SOURCE development XAI | COMPLETE |
| TRANSFER development XAI | COMPLETE |
| VALUE development XAI | COMPLETE |
| spatiotemporal robustness | COMPLETE |
| protocol freeze | COMPLETE |
| final 2020 XAI | SEALED |
| paper figures | DEVELOPMENT PROTOTYPES COMPLETE |

RF-04C — COMPLETE
RF-05 — COMPLETE
RF-06 — NEXT

**2020 FINAL HOLDOUT: SEALED**

## Documentation Table of Contents
- [Random Forest Development Matrix](../../docs/modeling/06_random_forest_development_matrix.md)
- [01. RF XAI Protocol Freeze Specification](01_rf_xai_protocol.md)
- [02. XAI Cohort Design](02_xai_cohort_design.md)
- [03. Feature Group Contract](03_feature_group_contract.md)
- [04. RF SHAP Methodology](04_rf_shap_method.md)
- [05. Permutation Importance Methodology](05_permutation_importance.md)
- [06. SOURCE XAI](06_source_xai.md)
- [07. TRANSFER XAI](07_transfer_xai.md)
- [08. VALUE XAI](08_value_xai.md)
- [09. Spatiotemporal Robustness](09_xai_spatiotemporal_robustness.md)
- [10. Protocol Freeze](10_rf_xai_protocol_freeze.md)
- [11. Final 2020 XAI](11_final_2020_xai.md)
- [12. Paper Figures](12_paper_figures.md)
