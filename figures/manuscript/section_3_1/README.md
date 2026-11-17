# Sorties de la Section 3.1 du manuscrit (Diagnostics d'assimilation)

## Statut du répertoire et préparation de la DA-CDF corrigée

Ce répertoire hébergera les résultats scientifiques corrigés de la Section 3.1 (Figure 3 et Figures S1–S3).

- **Archivage des anciennes sorties :** L'intégralité des 25 fichiers historiques (les 5 figures PNG de référence ainsi que les 20 fichiers intermédiaires : PDF vectoriels, tables CSV sources, grilles NetCDF, distributions NPZ et rapports QC) issus de la simulation historique invalidée ont été déplacés et préservés dans [`figures/legacy/section_3_1/`](../../legacy/section_3_1/README.md) avec leurs empreintes SHA-256.
- **Répertoire actif vierge :** Ce dossier ne contient plus aucun résultat de l'ancien run et accueillera directement les nouvelles figures et données sources issues de la chaîne `scripts/postprocessing/manuscript/sec3.1/` dès l'achèvement du prétraitement de la simulation DA-CDF réalignée (`DA_cdf_noirr_2016_2020` sous `NoahMP_Morocco`).
- **Régénération :** Exécuter séquentiellement :
  ```bash
  python scripts/postprocessing/manuscript/sec3.1/process_fig3_data.py
  python scripts/postprocessing/manuscript/sec3.1/process_supplementary_data.py
  python scripts/postprocessing/manuscript/sec3.1/plot_fig3.py
  python scripts/postprocessing/manuscript/sec3.1/plot_fig_s1.py
  python scripts/postprocessing/manuscript/sec3.1/plot_fig_s2.py
  python scripts/postprocessing/manuscript/sec3.1/plot_fig_s3.py
  ```
- **Documentation d'invalidation :** Consulter [`docs/invalidated_legacy_cdf_results.md`](../../../docs/invalidated_legacy_cdf_results.md).
