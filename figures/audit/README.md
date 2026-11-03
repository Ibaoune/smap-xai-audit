# Figures d'audit (Projet SMAP-XAI)

Ce répertoire contient les sorties graphiques produites par les scripts d'audit et de diagnostic méthodologique.

## Provenance et reproductibilité

- **`nocdf_native_rf_2020_metrics.{pdf,png}`** :
  - **Script producteur :** [`scripts/audits/export_nocdf_native_rf_metrics.py`](../../scripts/audits/export_nocdf_native_rf_metrics.py)
  - **Données sources :** `reports/modeling/final_2020/final_metrics_2020.csv` et modèles sous `reports/modeling/models/final_refit_2016_2019/`.
  - **Table source versionnée :** [`tables/audit/nocdf_native_rf_2020_metrics.csv`](../../tables/audit/nocdf_native_rf_2020_metrics.csv)
  - **Documentation :** [`docs/nocdf_native_rf_results.md`](../../docs/nocdf_native_rf_results.md)
  - **Statut scientifique :** Valide (évaluation sur support natif DA-NoCDF, indépendante de la simulation CDF).
  - **Régénération :**
    ```bash
    python3 scripts/audits/export_nocdf_native_rf_metrics.py
    ```
