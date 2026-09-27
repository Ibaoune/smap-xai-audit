# SMAP-XAI Explainable AI Protocol

This directory contains the documentation and scientific protocols for the Explainable AI (XAI) stages of the SMAP-XAI Audit project.

## Important Definitions

- **Predictive Modeling**: Fitting the model to minimize error against a target (RF-01 to RF-03).
- **Model Explanation**: Quantifying how the fitted model uses inputs to produce its specific predictions (RF-04 onwards).
- **Scientific Interpretation**: Synthesizing explanations within the context of physical domain knowledge.
- **Causal Inference**: Estimating the true physical impact of an intervention.

**Explicit Statement**: SHAP explains the fitted RF predictions. It does not establish causal effects. SHAP provides a rigorous mathematical allocation of the model's predictive variance among the input features, but due to feature correlation and observational constraints, these allocations cannot be strictly interpreted as isolated physical causal impacts.
