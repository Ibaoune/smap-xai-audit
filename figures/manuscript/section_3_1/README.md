# Sorties de la Section 3.1 du manuscrit (Diagnostics d'assimilation)

## Avertissement de provenance scientifique (Résultats historiques invalidés)

Les fichiers graphiques, tables sources et rapports de QC contenus dans ce répertoire reposent sur l'ancienne simulation historique DA-CDF (juillet 2026), dont les tables CDF présentaient une discordance géométrique (16 030 mailles décalées) documentée dans [`docs/invalidated_legacy_cdf_results.md`](../../../docs/invalidated_legacy_cdf_results.md).

- **Statut scientifique :** **Invalidé**. Ces résultats ne doivent pas être utilisés pour des interprétations scientifiques définitives.
- **Figures raster suivies par Git :** Les versions PNG (`Fig3_a_d_support.png`, `Fig3_e_h_matched_updates.png`, `FigS1_sample_matching_sensitivity.png`, `FigS2_seasonal_matched_differences.png`, `FigS3_water_accounting.png`) sont archivées dans l'historique Git (commit `b2f74f3`) à titre de référence documentaire historique.
- **Fichiers dérivés locaux :** Les fichiers PDF vectoriels, tables CSV et rapports QC locaux sont maintenus sur le cluster pour permettre l'exécution et la comparaison des scripts de la chaîne [`scripts/postprocessing/manuscript/sec3.1/`](../../../scripts/postprocessing/manuscript/sec3.1/).
- **Régénération :** Dès l'achèvement du prétraitement de la simulation DA-CDF réalignée (`DA_cdf_noirr_2016_2020`), ces fichiers seront recalculés et écrasés par l'exécution de :
  ```bash
  python scripts/postprocessing/manuscript/sec3.1/process_fig3_data.py
  python scripts/postprocessing/manuscript/sec3.1/process_supplementary_data.py
  python scripts/postprocessing/manuscript/sec3.1/plot_fig3.py
  python scripts/postprocessing/manuscript/sec3.1/plot_fig_s1.py
  python scripts/postprocessing/manuscript/sec3.1/plot_fig_s2.py
  python scripts/postprocessing/manuscript/sec3.1/plot_fig_s3.py
  ```
