# Scripts de Prétraitement et de Standardisation (`scripts/preprocessing/`)

**Auteur :** M. El Aabaribaoune (@um6p)
**Rôle :** Extraction, harmonisation et calcul des diagnostics spatio-temporels pour les simulations LIS / Noah-MP et les références satellites.

---

## 1. Objectif scientifique

Le répertoire `scripts/preprocessing/` constitue la porte d'entrée technique de la chaîne de données. Son rôle scientifique est de :
1. **Extraire et découpler** les trajectoires temporelles simulées par Noah-MP (états hydriques de surface et profonds, flux d'évapotranspiration, ruissellement et drainage) à partir des fichiers bruts `LIS_HIST`.
2. **Isoler les diagnostics EnKF d'assimilation** (incréments d'analyse, innovations, incertitudes de prévision et résidus d'analyse) pour caractériser l'intervention du filtre de Kalman.
3. **Harmoniser les géométries et les échelles temporelles** : convertir les diagnostics événementiels instantanés en agrégats journaliers rigoureusement masqués par le passage effectif du satellite SMAP.
4. **Calculer les cibles différentielles** de réponse hydrologique ($\Delta\text{RZSM}$, $\Delta\text{ET}$, etc.) et le gain face à la référence indépendante externe (GLEAM v4.3a).

---

## 2. Logique méthodologique

Le prétraitement suit quatre principes méthodologiques directeurs :

1. **Reproductibilité déterministe :** Chaque script opère sur une variable unique ou un groupe fonctionnel cohérent, avec prise en charge explicite de l'expérience via l'option CLI `--experiment` (`opl`, `da_nocdf`, `da_cdf`).
2. **Gabarit spatial invariant :** Le fichier `data/interim/noahmp/da_cdf/ssm/ssm_2016.nc` sert de masque géographique canonique ($121 \times 181$ mailles, 16 030 terres émergées) pour réaligner les grilles de coordonnées lors de l'extraction de l'EnKF.
3. **Conditionnement par la fréquence d'observation :** Les diagnostics journaliers EnKF (scripts 15 à 20) sont strictement masqués par `observation_frequency` (script 14). Un pixel-jour sans observation valide SMAP est systématiquement affecté à `NaN` afin d'éviter toute dilution artificielle par des zéros.
4. **Intégration verticale standardisée :** La zone racinaire ($\text{RZSM}$, 0–100 cm) est calculée par pondération canonique des trois premières couches du sol :
   $$\text{RZSM} = 0{,}10 \times \theta_1 + 0{,}30 \times \theta_2 + 0{,}60 \times \theta_3$$
   La quatrième couche (100–200 cm) est explicitement exclue du réservoir racinaire actif.

---

## 3. Données et variables (Nomenclature des 32 scripts)

| # | Script | Variable produite | Dossier de sortie | Unités | Dimension spatiale | Support temporel |
|---|---|---|---|:---:|:---:|:---:|
| **01** | `01_prepare_ssm.py` | `ssm` (couche 1, 0–10 cm) | `data/interim/noahmp/<exp>/ssm/` | $\text{m}^3\,\text{m}^{-3}$ | $121 \times 181$ | Journalier (moyenne 24h) |
| **02** | `02_prepare_soil_moisture_layer.py` | `sm_layer2`, `sm_layer3`, `sm_layer4` | `data/interim/noahmp/<exp>/sm_layer[2-4]/` | $\text{m}^3\,\text{m}^{-3}$ | $121 \times 181$ | Journalier |
| **03** | `03_derive_rzsm.py` | `rzsm` (0–100 cm) | `data/processed/daily_model/<exp>/rzsm/` | $\text{m}^3\,\text{m}^{-3}$ | $121 \times 181$ | Journalier |
| **04** | `04_prepare_precipitation.py` | `precipitation` (pluie incidente) | `data/interim/noahmp/forcing/precipitation/` | $\text{mm}\,\text{d}^{-1}$ | $121 \times 181$ | Journalier |
| **05** | `05_prepare_air_temperature.py` | `air_temperature` (Tair 2m) | `data/interim/noahmp/forcing/air_temperature/` | $\text{K}$ | $121 \times 181$ | Journalier |
| **06** | `06_prepare_et.py` | `et` (Évapotranspiration totale) | `data/interim/noahmp/<exp>/et/` | $\text{mm}\,\text{d}^{-1}$ | $121 \times 181$ | Journalier |
| **07** | `07_prepare_surface_runoff.py` | `surface_runoff` (Ruissellement) | `data/interim/noahmp/<exp>/surface_runoff/` | $\text{mm}\,\text{d}^{-1}$ | $121 \times 181$ | Journalier |
| **08** | `08_prepare_baseflow.py` | `baseflow` (Drainage profond) | `data/interim/noahmp/<exp>/baseflow/` | $\text{mm}\,\text{d}^{-1}$ | $121 \times 181$ | Journalier |
| **09** | `09_prepare_analysis_increment.py` | `increment_signed` ($\Delta\theta_1^a$) | `data/interim/enkf/<exp>/increment_signed/` | $\text{m}^3\,\text{m}^{-3}$ | $121 \times 181$ | Événement EnKF |
| **10** | `10_prepare_innovation.py` | `innovation` ($y - Hx^f$) | `data/interim/enkf/<exp>/innovation/` | $\text{m}^3\,\text{m}^{-3}$ | $121 \times 181$ | Événement EnKF |
| **11** | `11_prepare_forecast_uncertainty.py` | `forecast_variance` ($HPH^T$) * | `data/interim/enkf/<exp>/forecast_variance/` | $(\text{m}^3\,\text{m}^{-3})^2$| $121 \times 181$ | Événement EnKF |
| **12** | `12_prepare_normalized_innovation.py`| `normalized_innovation` | `data/interim/enkf/<exp>/normalized_innovation/` | Sans unité | $121 \times 181$ | Événement EnKF |
| **13** | `13_prepare_analysis_residual.py` | `analysis_residual` ($y - Hx^a$) | `data/interim/enkf/<exp>/analysis_residual/` | $\text{m}^3\,\text{m}^{-3}$ | $121 \times 181$ | Événement EnKF |
| **14** | `14_derive_observation_frequency.py` | `observation_frequency` | `data/processed/daily_enkf/<exp>/observation_frequency/` | $\{0, 1\}$ | $121 \times 181$ | Journalier |
| **15** | `15_derive_daily_signed_increment.py`| `daily_signed_increment` | `data/processed/daily_enkf/<exp>/daily_signed_increment/` | $\text{m}^3\,\text{m}^{-3}$ | $121 \times 181$ | Journalier (masqué) |
| **16** | `16_derive_daily_absolute_increment.py`| `daily_absolute_increment` | `data/processed/daily_enkf/<exp>/daily_absolute_increment/` | $\text{m}^3\,\text{m}^{-3}$ | $121 \times 181$ | Journalier (masqué) |
| **17** | `17_derive_daily_innovation.py` | `daily_innovation` | `data/processed/daily_enkf/<exp>/daily_innovation/` | $\text{m}^3\,\text{m}^{-3}$ | $121 \times 181$ | Journalier (masqué) |
| **18** | `18_derive_daily_normalized_innovation.py`| `daily_normalized_innovation` | `data/processed/daily_enkf/<exp>/daily_normalized_innovation/` | Sans unité | $121 \times 181$ | Journalier (masqué) |
| **19** | `19_derive_daily_forecast_variance.py`| `daily_forecast_variance` * | `data/processed/daily_enkf/<exp>/daily_forecast_variance/` | $(\text{m}^3\,\text{m}^{-3})^2$| $121 \times 181$ | Journalier (masqué) |
| **20** | `20_derive_daily_analysis_residual.py`| `daily_analysis_residual` | `data/processed/daily_enkf/<exp>/daily_analysis_residual/` | $\text{m}^3\,\text{m}^{-3}$ | $121 \times 181$ | Journalier (masqué) |
| **21** | `21_prepare_elevation.py` | `elevation` (MNT SRTM/LIS) | `data/processed/static/elevation/` | $\text{m}$ | $121 \times 181$ | Statique |
| **22** | `22_prepare_soil_texture.py` | 16 fractions texturales STATSGO | `data/processed/static/soil_texture/` | Fraction [0, 1] | $121 \times 181$ | Statique |
| **23** | `23_prepare_land_cover.py` | 20 fractions végétales MODIS | `data/processed/static/land_cover/` | Fraction [0, 1] | $121 \times 181$ | Statique |
| **25** | `25_derive_delta_rzsm.py` | $\Delta\text{RZSM} = \text{DA} - \text{OPL}$ | `data/processed/transfer/<exp>/delta_rzsm/` | $\text{m}^3\,\text{m}^{-3}$ | $121 \times 181$ | Journalier |
| **26** | `26_derive_delta_et.py` | $\Delta\text{ET} = \text{DA} - \text{OPL}$ | `data/processed/transfer/<exp>/delta_et/` | $\text{mm}\,\text{d}^{-1}$ | $121 \times 181$ | Journalier |
| **27** | `27_derive_delta_surface_runoff.py` | $\Delta\text{Runoff} = \text{DA} - \text{OPL}$ | `data/processed/transfer/<exp>/delta_surface_runoff/` | $\text{mm}\,\text{d}^{-1}$ | $121 \times 181$ | Journalier |
| **28** | `28_derive_delta_baseflow.py` | $\Delta\text{Baseflow} = \text{DA} - \text{OPL}$ | `data/processed/transfer/<exp>/delta_baseflow/` | $\text{mm}\,\text{d}^{-1}$ | $121 \times 181$ | Journalier |
| **30** | `30_prepare_gleam_value_reference.py`| Référence GLEAM v4.3a projetée | `data/processed/value/gleam/reference/` | $\text{mm}\,\text{d}^{-1}$ | $0{,}25^\circ$ (4 110 mailles) | Journalier |
| **31** | `31_derive_value_ae.py` | $\text{value\_ae} = \|e_{\text{OPL}}\| - \|e_{\text{DA}}\|$| `data/processed/value/value_ae/<exp>/` | $\text{mm}\,\text{d}^{-1}$ | $0{,}25^\circ$ | Journalier |
| **31b**| `31b_derive_assimilated_fraction.py`| Fraction de surface assimilée | `data/processed/value/gleam/assimilated_fraction/` | Fraction [0, 1] | $0{,}25^\circ$ | Journalier |
| **32** | `32_derive_da_precip_forcing_difference.py`| $\Delta\text{Precip}_{\text{forcing}}$ (bruit LIS)| `data/processed/transfer/<exp>/delta_precip_forcing/`| $\text{mm}\,\text{d}^{-1}$ | $121 \times 181$ | Journalier |

*\* Note sur `forecast_sigma_01` (scripts 11 et 19) :* La variable extraite des sorties brutes LIS EnKF est nommée `forecast_sigma_01`. Ses ordres de grandeur numériques sont caractéristiques de la variance de prévision d'observation ($HPH^T \approx 0{,}0023\text{ (m}^3\,\text{m}^{-3})^2$, soit un écart-type équivalent de $\approx 0{,}048\text{ m}^3\,\text{m}^{-3}$). Toutefois, sa définition physique formelle exacte dans le code source de LIS (variance d'innovation vs écart-type prévisionnel) reste un point à confirmer formellement avant toute utilisation dans des émulateurs mécanistiques.

---

## 4. Fonctionnement technique et ordre d'exécution

L'exécution doit respecter un ordonnancement strict en 5 phases séquentielles :

```
Phase 1 : Extraction du gabarit spatial canonique
  └─► python scripts/preprocessing/01_prepare_ssm.py --experiment da_cdf --year 2016

Phase 2 : Trajectoires d'états et flux Noah-MP (2016-2020)
  ├─► 01_prepare_ssm.py
  ├─► 02_prepare_soil_moisture_layer.py (couches 2, 3, 4)
  ├─► 03_derive_rzsm.py
  ├─► 04_prepare_precipitation.py & 05_prepare_air_temperature.py
  └─► 06_prepare_et.py, 07_prepare_surface_runoff.py, 08_prepare_baseflow.py

Phase 3 : Extraction des diagnostics EnKF intermédiaires
  ├─► 09_prepare_analysis_increment.py
  ├─► 10_prepare_innovation.py
  ├─► 11_prepare_forecast_uncertainty.py
  ├─► 12_prepare_normalized_innovation.py
  └─► 13_prepare_analysis_residual.py

Phase 4 : Agrégations journalières EnKF conditionnées
  ├─► 14_derive_observation_frequency.py
  └─► 15 à 20 (signed_incr, abs_incr, innov, norm_innov, forecast_var, residual)

Phase 5 : Dérivation des cibles différentielles et valeur externe
  ├─► 21 à 23 (statiques : elevation, texture, land cover)
  ├─► 25 à 28 (deltas de transfert : rzsm, et, runoff, baseflow)
  ├─► 30 (référence GLEAM v4.3a projetée à 0.25°)
  ├─► 31 & 31b (value_ae et fraction assimilée)
  └─► 32 (contrôle du forçage de précipitation LIS)
```

---

## 5. Validation, contrôle qualité et interprétation

Tout fichier NetCDF généré doit satisfaire les critères bloquants suivants :
- **Intégrité dimensionnelle :** `lat: 121`, `lon: 181` (ou dimensions GLEAM pour les scripts 30–31).
- **Vérification du support continental :** Présence exacte de 16 030 pixels valides sur les variables continues (aucun `NaN` non sollicité sur terre).
- **Conservation du support d'observation :** Le nombre de pixels valides dans `daily_absolute_increment` doit être rigoureusement égal au nombre de pixels où `observation_frequency == 1`.
- **Non-contamination :** Aucune exécution ciblant `da_cdf` ne doit modifier les répertoires `opl` ou `da_nocdf`.

---

## 6. Statut des jeux de données et références internes

- **[Vérifié]** Scripts `01` à `20` : Exécutés et validés à 100 % sur les cinq années 2016–2020 pour `opl`, `da_nocdf` et `da_cdf` corrigée (100 fichiers NetCDF conformes).
- **[En attente]** Scripts `25` à `32` : Cibles de transfert et métrique `value_ae` à régénérer sur la DA-CDF corrigée dès validation de la nouvelle logique méthodologique.
- **Documentation associée :** Consulter [`docs/preprocessing/`](../../docs/preprocessing/) pour les notes techniques d'extraction et [`docs/invalidated_legacy_cdf_results.md`](../../docs/invalidated_legacy_cdf_results.md) pour les détails sur l'invalidation de l'ancienne grille CDF.
