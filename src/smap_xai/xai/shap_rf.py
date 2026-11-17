"""
SHAP TreeExplainer wrapper.

Expects:
- Explainer Class: shap.TreeExplainer
- Feature Perturbation Mode: tree_path_dependent
- Model Output Mode: raw

Produces compact per-sample wide products containing identifiers, expected_value, and shap__<feature> columns.
"""
