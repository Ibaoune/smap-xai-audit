# Archive des résultats historiques de la Section 3.1 (DA-CDF invalidée)

## 1. Provenance et statut scientifique

- **Date d'exécution :** 11 octobre 2026 (12:58–15:50 UTC).
- **Dépôt d'origine :** `figures/manuscript/section_3_1/` (commit d'archivage partiel raster `b2f74f3`).
- **Statut scientifique :** **INVALIDÉ**.
- **Cause méthodologique :** Incompatibilité géométrique et de masque identifiée les 24–25 octobre 2026 dans la simulation historique `DA_cdf_noirr_2016_2020` (juillet 2026). Le fichier CDF historique couvrait un domaine spatial distinct plus large, où le domaine NorthMor ne constituait qu'un sous-domaine interne. LIS lisant les paramètres CDF comme un vecteur séquentiel 1D de mailles terrestres, la dimension `ngrid` du CDF ne correspondait pas à l'ordonnancement séquentiel des 16 030 mailles continentales actives de la grille NorthMor, provoquant une attribution erronée des bornes de mise à l'échelle d'un pixel à un autre. L'impact spatial effectif sur les innovations et les incréments (qui ne doit pas être confondu avec le nombre total de mailles du domaine) reste à quantifier comparativement face à la simulation réalignée.
- **Documentation de référence :** [`docs/invalidated_legacy_cdf_results.md`](../../../docs/invalidated_legacy_cdf_results.md).
- **Rôle de cette archive :** Préservation patrimoniale et comparaison méthodologique avant/après correction du domaine CDF. Ces fichiers ne doivent en aucun cas être intégrés comme résultats scientifiques validés dans le manuscrit.

## 2. Inventaire et empreintes SHA-256 des 25 fichiers préservés

| Nom du fichier | Catégorie initiale | Taille (octets) | Empreinte SHA-256 |
| :--- | :--- | :---: | :--- |
| `Fig3_a_d_source_data.csv` | Fichier intermédiaire (ignoré Git) | 816 | `e686b5ea7dcb4a69159edea98b855fb89db753833be4c57d9d21d05c3696c170` |
| `Fig3_a_d_source_data.nc` | Fichier intermédiaire (ignoré Git) | 535,643 | `543603bf890b60ae971b3c126d2c979dac59e5a9ca7bb3da2a3c132b5da89494` |
| `Fig3_a_d_support.pdf` | Fichier intermédiaire (ignoré Git) | 1,477,199 | `2a8ec5280e6c3112294ba02f3cc51feed328e81d14a20ac72a14491a5073bb14` |
| `Fig3_a_d_support.png` | Figure PNG (suivie Git) | 466,768 | `b897805dfb632fedb0c23586ff570c6cbffe507734e82ff669b1a1deb3108cfd` |
| `Fig3_e_h_matched_updates.pdf` | Fichier intermédiaire (ignoré Git) | 1,639,141 | `0cc382d9ddc8a4320d3f5089fa33341e64d3c0d15d08eb208cf7e6182751ee72` |
| `Fig3_e_h_matched_updates.png` | Figure PNG (suivie Git) | 481,709 | `b1dc59ad023cb3782b69732b06d5cfee58b3f957742582243749601b1ba1921f` |
| `Fig3_e_h_source_data.csv` | Fichier intermédiaire (ignoré Git) | 1,073 | `f638a004e027381a09684842e45ebbcd81c8268578f9ef802119b6aae231be30` |
| `Fig3_e_h_source_data.nc` | Fichier intermédiaire (ignoré Git) | 272,842 | `6831a95ffdeae79bf091e2f2bbb5e8d7e7407695c235fd6bc33f0a7b459dbdd4` |
| `Fig3_qc_report.txt` | Fichier intermédiaire (ignoré Git) | 1,129 | `d9d357b1fe214c43331f9be7c66642bebd715f0a6922af34b02869b3d4de8f01` |
| `FigS1_S3_qc_report.txt` | Fichier intermédiaire (ignoré Git) | 1,435 | `b30b441b1e8a099bf83fc68c1e0fb146ed31862f99727f1cc063c3546e33ed38` |
| `FigS1_distributions.npz` | Fichier intermédiaire (ignoré Git) | 55,022,290 | `c66975d93a94ca4abaa8b1c664d3a88719cfd05374e787459df38ba58de23d9c` |
| `FigS1_sample_matching_sensitivity.pdf` | Fichier intermédiaire (ignoré Git) | 744,850 | `b9916a9c2552797b6a3754a5219773dddc3a967a3c6151837f63099fb45d88ab` |
| `FigS1_sample_matching_sensitivity.png` | Figure PNG (suivie Git) | 489,202 | `c673007877e4627a73614a1fed3a9b8bbd8d9b9b7728d2ffbe3a0424cfae40a5` |
| `FigS1_source_data.csv` | Fichier intermédiaire (ignoré Git) | 1,492 | `80e19bb172f750029bb682e1a1494d87fbafca3edad7cdc01bf3f192985bd746` |
| `FigS2_seasonal_matched_differences.pdf` | Fichier intermédiaire (ignoré Git) | 2,975,786 | `2cd6e5a3a255ada06ecc4647316e299b4c4f583c058c46d0ead369c0b9ecee66` |
| `FigS2_seasonal_matched_differences.png` | Figure PNG (suivie Git) | 273,902 | `f70341d16d4f9f28dc2f6be12a175f9a61acd76b9ab5cb32a794797c553af1ed` |
| `FigS2_seasonal_summary.csv` | Fichier intermédiaire (ignoré Git) | 1,077 | `f1789ac3616f403787232cf5b71e9d5a52d7ab2c1180e92c1f6185b55db8dc8a` |
| `FigS2_source_data.nc` | Fichier intermédiaire (ignoré Git) | 361,165 | `ce2b6467722748b4a0b0d42cca4137797dc0cd8159635f6bd6c1743b916e460c` |
| `FigS3_cumulative_map.nc` | Fichier intermédiaire (ignoré Git) | 16,826 | `2a592d913f5289a13ad13d19b221012684df9637cfdd491f2c0a692773286be2` |
| `FigS3_monthly_climatology.csv` | Fichier intermédiaire (ignoré Git) | 2,002 | `9b9236d6a79fa100e42c76f749f5ead5b636b0461ef6a228ecabdd8a6fc2ed68` |
| `FigS3_water_accounting.pdf` | Fichier intermédiaire (ignoré Git) | 996,893 | `af40eb87e3d340a847550592361841c80964e4254c0e1c430531d77521e94de6` |
| `FigS3_water_accounting.png` | Figure PNG (suivie Git) | 685,460 | `093bdae7562f6fdaa8481c70690299b8e5adeb3e0502642ecc887af576fe7075` |
| `FigS3_water_accounting_summary.csv` | Fichier intermédiaire (ignoré Git) | 527 | `a302be0f8082f9ba95544496406b9d029ba70b03c42cd75cdfcba0cfd52a558d` |
| `matched_increments_1d.npz` | Fichier intermédiaire (ignoré Git) | 18,128,243 | `e6b4a4214e5bf3dcae6d9038228ab0e773b801de7be5f8933bd70c61385a3b2d` |
| `matched_spatial_summary.csv` | Fichier intermédiaire (ignoré Git) | 867 | `07d08630b0e97c9fb50a897f3133c94212b64276610291f8e9a0f8a48c3c0b68` |

## 3. Remplacement programmé

Les résultats définitifs de la Section 3.1 seront recalculés de manière déterministe sous `figures/manuscript/section_3_1/` via la suite `scripts/postprocessing/manuscript/sec3.1/` dès l'achèvement du prétraitement de la nouvelle simulation réalignée `DA_cdf_noirr_2016_2020`.
