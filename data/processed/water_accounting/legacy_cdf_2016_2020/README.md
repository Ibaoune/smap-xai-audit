# Comptabilité des incréments EnKF — Données historiques de préservation (Ancienne DA-CDF)

Ce répertoire contient les copies historiques de préservation des données de comptabilité des incréments d'assimilation EnKF pour la période 2016–2020. Ces données sont conservées uniquement à des fins de traçabilité scientifique et d'audit méthodologique. Elles sont **INVALIDÉES POUR PUBLICATION** et ne doivent pas être utilisées comme résultats scientifiques validés.

## Contenu des fichiers et unités physiques réelles

Les variables correspondent aux ajustements de la couche de surface (0–10 cm) convertis en équivalent lame d'eau ($100 \times \text{incr en m}^3\,\text{m}^{-3} \rightarrow \text{mm}$) :
- `analysis_water_accounting_monthly.csv` : Séries temporelles mensuelles (60 mois, 2016–2020) des moyennes spatiales pondérées par le cosinus de la latitude ($W_{\text{positive}}$, $W_{\text{removal}}$, $W_{\text{absolute}}$, $W_{\text{net}}$).
- `analysis_water_accounting_seasonal.csv` : Moyennes spatiales climatologiques par saison (DJF, MAM, JJA, SON).
- `analysis_water_accounting_summary.csv` : Synthèse tabulaire du bilan cumulé sur 5 ans (moyenne pondérée, médiane spatiale, Q25, Q75).
- `analysis_water_accounting_pixel_cumulative_cdf.nc` : Grille 2D ($121 \times 181$) du cumul temporel 2016–2020 pour l'expérience DA-CDF sur support apparié.
- `analysis_water_accounting_pixel_cumulative_nocdf.nc` : Grille 2D ($121 \times 181$) du cumul temporel 2016–2020 pour l'expérience DA-NoCDF restreinte au support apparié CDF.
- `qc_report.txt` : Rapport de contrôle numérique (comptages annuels d'événements, quantiles et vérifications algébriques d'intégrité).

## Provenance et conditions d'échantillonnage

- **Expériences sources :** `DA_cdf_noirr_2016_2020` et `DA_nocdf_noirr_2016_2020`.
- **Support apparié :** Les calculs sont restreints à l'intersection des jours d'assimilation active entre CDF et NoCDF (`matched_mask = mask_cdf & mask_nocdf`). Les données NoCDF présentes dans ce dossier ne constituent donc pas une évaluation native indépendante de DA-NoCDF.
- **Statut scientifique :** **INVALIDÉ POUR PUBLICATION**. La simulation historique `DA_cdf_noirr_2016_2020` souffre d'un décalage géométrique de grille dans ses tables CDF (détaillé dans [`docs/invalidated_legacy_cdf_results.md`](../../../../docs/invalidated_legacy_cdf_results.md)). Les totaux appariés et les comparaisons NoCDF − CDF sont formellement erronés.

## Anomalies de métadonnées dans les fichiers NetCDF

- **Unités erronées dans les variables :** Les variables `W_positive`, `W_removal`, `W_absolute` et `W_net` ont hérité des attributs de la variable source (`units = 'm3 m-3'` et `long_name = 'Signed EnKF Analysis Increment...'`), alors que les données effectives sont des cumuls en **mm** (multipliés par 100 et sommés sur le temps).
- **Absence d'attributs globaux :** Les deux fichiers NetCDF ne comportent aucun attribut global décrivant l'expérience source, la période temporelle ou le masque de support.

## Traçabilité logicielle et statut des copies

- **Scripts producteurs :** [`scripts/postprocessing/water_accounting/process_water_accounting.py`](../../../../scripts/postprocessing/water_accounting/process_water_accounting.py) et [`scripts/postprocessing/water_accounting/plot_water_accounting.py`](../../../../scripts/postprocessing/water_accounting/plot_water_accounting.py).
- **Script consommateur :** [`scripts/postprocessing/manuscript/sec3.1/process_supplementary_data.py`](../../../../scripts/postprocessing/manuscript/sec3.1/process_supplementary_data.py).
- **Copies de préservation :** Les fichiers de ce dossier sont des copies exactes octet par octet. Les originaux restent temporairement situés à la racine du dépôt pour préserver l'exécution des scripts consommateurs existants.
- **Usage réservé :** Ce répertoire est strictement réservé aux données de l'ancienne simulation DA-CDF invalidée. Il est formellement interdit de réutiliser ce dossier pour stocker les sorties de futures simulations réalignées.

## Intégrité des fichiers

Les six fichiers de données ci-dessous correspondent strictement aux originaux conservés temporairement à la racine du dépôt (empreintes SHA-256 identiques recalculées) :

| Fichier | Empreinte SHA-256 |
| :--- | :--- |
| `analysis_water_accounting_monthly.csv` | `f3e4d9998f6bba4f955a82a89383da650738924d22fd7e997ab1d40ae4701dd1` |
| `analysis_water_accounting_seasonal.csv` | `ac1f72f6d3e918e7c4b033372304f0fa4a62ac51c5b89c7a8979b250489e9a94` |
| `analysis_water_accounting_summary.csv` | `04092a0a39222117e399898e26709cba410717a149aca78b208b82d5504532d3` |
| `analysis_water_accounting_pixel_cumulative_cdf.nc` | `8763db736505ce23d90fd8f6310ff8b1e85fd43f53e6013a3c751c0cbc3e0f21` |
| `analysis_water_accounting_pixel_cumulative_nocdf.nc` | `391681edecafe8e4d332c4d53c3082202609fed2c02ee1b3907811d5a060f9a1` |
| `qc_report.txt` | `206e193a05df7618dddec91e918482c1e0af5cc75b1eb0e54292173ed63b0235` |

Ces fichiers de données sont ignorés par Git (`.gitignore`). Leur présence sur le système de fichiers Lustre garantit la traçabilité locale mais ne constitue pas une sauvegarde indépendante externe.
