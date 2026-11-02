# Figures — Diagnostics d'Assimilation SMAP / EnKF

Ce répertoire rassemble les sorties graphiques relatives au fonctionnement direct de l'assimilation SMAP via le filtre de Kalman d'ensemble (EnKF) dans Noah-MP / LIS.

## 1. Contenu du répertoire

### `figure_soil_texture_rejection_maps.png` (2 × 3 panneaux, JA 2016–2020)
- **(a)** Texture dominante du sol (classes USDA discrétisées, grille LIS).
- **(b)** Seuil volumique de flétrissement `smcwlt` ($\text{m}^3\,\text{m}^{-3}$, table `SOILPARM.TBL`).
- **(c)** Fraction des observations SMAP rejetées par le critère de flétrissement (%).
- **(d)** Moyenne des observations SMAP brutes reçues ($\text{m}^3\,\text{m}^{-3}$).
- **(e)** Moyenne de l'humidité du sol simulée en couche 1 (0–10 cm) par Noah-MP en boucle ouverte OPL ($\text{m}^3\,\text{m}^{-3}$).
- **(f)** Fraction de superficie équipée pour l'irrigation (GMIA).

### `figure_point_d_nowilt_vs_control_pm005.png` (1 × 3 panneaux, JA 2018)
- **(A)** Fraction des observations rejetées au contrôle de flétrissement dans le contrôle (%).
- **(B)** Différence d'incréments d'assimilation cumulés : Nowilt − Contrôle (mm d'eau).
- **(C)** Différence moyenne d'humidité du sol simulée en couche 1 (0–10 cm) : Nowilt − Contrôle, avec échelle bornée à $[\pm 0.05]\ \text{m}^3\,\text{m}^{-3}$.

## 2. Données sources et expériences

- **Données géographiques et forçages LIS :** lues directement dans le dépôt distinct `NoahMP_Morocco` (grille `lis_input_NorthMor_5km.nc`, table `SOILPARM.TBL`), sans modification de celui-ci.
- **Irrigation (GMIA v5) :** raster global à résolution native de 5 minutes d'arc (~0.0833°), découpé régionalement, interpolé bilinéairement sur la grille LIS 5 km, puis lissé par un filtre spatial uniforme de $7 \times 7$ mailles normalisé par les mailles continentales.
- **Expériences d'assimilation DA-NoCDF :**
  - `DA_nocdf_noirr_2016_2020` : assimilation EnKF des observations SMAP brutes (sans redimensionnement CDF). Utilisée comme référence de contrôle.
  - `DA_nocdf_TEST_nowilt` : simulation de sensibilité sur juillet–août 2018 avec désactivation du seuil de flétrissement.
  - `OPL_noirr_2016_2020` : simulation Open-Loop de contrôle, utilisée exclusivement pour la comparaison d'humidité en boucle ouverte dans le panneau (e) de la figure texturale.

## 3. Script producteur

- [`scripts/audit_soil_texture_and_wilt_analysis.py`](../../scripts/audit_soil_texture_and_wilt_analysis.py)

## 4. Précautions et traçabilité scientifiques

- Ces figures documentent des simulations issues de la chaîne DA-NoCDF et des tests de sensibilité associés.
- **Effet du seuil de flétrissement :** Le critère implémenté dans LIS rejette les observations vérifiant $SMAP < \theta_{wilt} + 0.02\ \text{m}^3\,\text{m}^{-3}$. En sol lourd sec (classe 12 argile, $\theta_{wilt} = 0.138\ \text{m}^3\,\text{m}^{-3}$), ce seuil ($0.158\ \text{m}^3\,\text{m}^{-3}$) dépasse la valeur SMAP brute estivale moyenne ($0.07$–$0.10\ \text{m}^3\,\text{m}^{-3}$), provoquant un rejet massif supérieur à 95 %.
- La levée de ce seuil dans le test de sensibilité (`nowilt`) débloque l'assimilation d'incréments négatifs, mais ne supprime pas les autres filtres de contrôle qualité actifs dans LIS (variance d'innovation, gel, neige, etc.).
- Le code LIS et les tests de sensibilité mettent en évidence le rôle du seuil de flétrissement, dépendant de la texture du sol, dans les rejets observés. Ces diagnostics sont indépendants de l'ancienne grille DA-CDF invalidée, mais ne constituent pas une validation globale de l'assimilation DA-NoCDF.
