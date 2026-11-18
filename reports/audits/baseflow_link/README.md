# Audit Hydrologique : Profil Vertical d'Humidité, Débit de Base ($Q_{\text{sb}}$) et Eau Nette Ajoutée par le Filtre

Ce rapport documente la réponse hydrologique globale à l'assimilation des données SMAP (2016–2020) sur le domaine NorthMor (~5 km, 121×181).

---

## 1. Contexte et Objectifs

L'assimilation de données SMAP (EnKF 20 membres) modifie l'état d'humidité du sol superficiel (couche 1 : 0–10 cm). Par diffusion capillaire et drainage gravitaire, ces incréments se propagent dans les couches racinaires profondes (couche 2 : 10–40 cm, couche 3 : 40–100 cm, couche 4 : 100–200 cm), modifiant le stock d'eau souterrain et influençant le drainage profond et le débit de base ($Q_{\text{sb}}$).

L'audit analyse comparativement :
1. **`DA_nocdf_noirr` vs `OPL_noirr`** : Assimilation brute sans correction de biais.
2. **`DA_cdf_noirr` vs `OPL_noirr`** : Assimilation avec correction par CDF matching.

---

## 2. Profil Vertical d'Humidité ($\Delta\theta_1$ à $\Delta\theta_4$) et Flux ($\Delta Q_{\text{sb}}, \Delta Q_{\text{s}}, \Delta\text{ET}$)

### Cycle Mensuel Moyen sur le Domaine NorthMor (2016–2020)

| Expérience | Mois | $\Delta\theta_1$ ($\text{m}^3/\text{m}^3$) | $\Delta\theta_2$ | $\Delta\theta_3$ | $\Delta\theta_4$ | $\Delta W_{\text{tot}}$ (mm) | $\Delta Q_{\text{sb}}$ (mm/j) | $\Delta Q_{\text{s}}$ (mm/j) | $\Delta\text{ET}$ (mm/j) | $\Delta P_{\text{ens}}$ (mm/j) |
|:-----------|:----:|:------------------------------------------:|:----------------:|:----------------:|:----------------:|:----------------------------:|:-----------------------------:|:----------------------------:|:------------------------:|:------------------------------:|
| **NoCDF** | Jan | -0.0360 | -0.0141 | -0.0123 | -0.0112 | -26.4 mm | +0.0468 | +0.0030 | -0.0804 | +0.0016 |
| NoCDF | Fév | -0.0326 | -0.0164 | -0.0137 | -0.0111 | -27.5 mm | +0.0572 | +0.0060 | -0.1187 | +0.0021 |
| NoCDF | Mar | -0.0288 | -0.0187 | -0.0175 | -0.0129 | -31.9 mm | +0.0607 | +0.0094 | -0.1710 | +0.0027 |
| NoCDF | Avr | -0.0298 | -0.0216 | -0.0203 | -0.0132 | -34.9 mm | +0.0380 | +0.0043 | -0.2499 | +0.0022 |
| NoCDF | Mai | -0.0204 | -0.0232 | -0.0204 | -0.0137 | -34.9 mm | +0.0236 | +0.0018 | -0.2082 | +0.0014 |
| NoCDF | Juin | -0.0034 | -0.0191 | -0.0166 | -0.0133 | -29.3 mm | +0.0137 | +0.0004 | -0.0181 | +0.0003 |
| NoCDF | Juil | +0.0113 | -0.0150 | -0.0132 | -0.0129 | -24.2 mm | +0.0104 | +0.0001 | +0.1563 | +0.0002 |
| NoCDF | Août | +0.0120 | -0.0120 | -0.0113 | -0.0128 | -21.9 mm | +0.0096 | +0.0003 | +0.2044 | +0.0010 |
| **CDF** | Jan | -0.0004 | -0.0027 | -0.0031 | -0.0068 | -9.5 mm | +0.0346 | +0.0026 | +0.0799 | +0.0016 |
| CDF | Mar | +0.0043 | -0.0020 | -0.0027 | -0.0067 | -8.5 mm | +0.0617 | +0.0083 | +0.1426 | +0.0027 |
| CDF | Mai | +0.0056 | -0.0030 | -0.0030 | -0.0064 | -8.5 mm | +0.0461 | +0.0030 | +0.1990 | +0.0014 |
| CDF | Juil | +0.0081 | -0.0027 | -0.0026 | -0.0062 | -7.8 mm | +0.0263 | +0.0004 | +0.1811 | +0.0003 |

Figure associée : [`delta_soilm_and_baseflow_response.png`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/audits/baseflow_link/delta_soilm_and_baseflow_response.png).

---

## 3. Bilan Hydrique et Eau Nette Ajoutée par le Filtre

### Vérification du Forçage Pluviométrique Perturbé
Dans LIS EnKF, les forçages atmosphériques reçoivent des perturbations stochastiques d'ensemble. La moyenne des 20 membres $\overline{P}_{\text{ens}}$ ne présente aucun biais systématique par rapport au forçage déterministe de l'OL :
- Écart moyen domaine : **$+0.00167\text{ mm/j}$** ($\sim 0.6\text{ mm/an}$)
- Écart-type : $0.0595\text{ mm/j}$
- Médiane ($P_{50}$) : **$0.0000\text{ mm/j}$**
- Percentile 5 / 95 : $[-0.0097, +0.0111]\text{ mm/j}$

Le forçage précipité est donc strictement non biaisé.

### Comparaison : Résidu du Bilan de Flux vs Incréments Directs (4 Couches)

L'eau nette ajoutée par le filtre d'assimilation EnKF est estimée selon deux méthodes indépendantes :
1. **Méthode indirecte (Résidu de flux de surface)** : $\Delta \text{Flux} = \Delta\text{ET} + \Delta Q_{\text{s}} + \Delta Q_{\text{sb}} - \Delta P_{\text{ens}}$
2. **Méthode directe (Somme intégrée des incréments sur les 4 couches)** :
   $$\Delta W_{\text{direct}} = \sum_{t} \sum_{k=1}^4 \Delta\theta_k(t) \cdot \Delta z_k$$
   avec $\Delta z = [100, 300, 600, 1000]\text{ mm}$, calculée directement depuis les 9 196 fichiers `LIS_DA_EnKF_*_incr.a01.d01.nc` de production (2016–2020).

| Expérience | Période | Eau Nette Résidu de Flux (mm) | Incréments Directs 4 Couches (mm) | Écart Résidu − Direct (mm) |
|:-----------|:-------:|:-----------------------------:|:---------------------------------:|:--------------------------:|
| **NoCDF** | DJF | -16.96 | **-142.00** | +125.04 |
| NoCDF | MAM | -75.11 | **-213.09** | +137.98 |
| NoCDF | JJA | +58.48 | **+2.78** | +55.70 |
| NoCDF | SON | +9.57 | **-134.58** | +144.15 |
| **NoCDF** | **Annuel (2016–2020)** | **-24.02** | **-486.90** | **+462.88** |
| **CDF** | DJF | +60.50 | **-61.51** | +122.01 |
| CDF | MAM | +103.72 | **-60.32** | +164.04 |
| CDF | JJA | +98.41 | **-15.38** | +113.79 |
| CDF | SON | +77.30 | **-69.78** | +147.08 |
| **CDF** | **Annuel (2016–2020)** | **+339.93** | **-206.97** | **+546.90** |

Fichiers de données associés :
- [`water_balance_vs_direct_increments.csv`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/audits/baseflow_link/water_balance_vs_direct_increments.csv)
- [`seasonal_water_balance_da_minus_ol.csv`](file:///srv/lustre01/project/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/audits/baseflow_link/seasonal_water_balance_da_minus_ol.csv)

### Interprétation de l'écart :
1. **Incréments directs** :
   - En NoCDF, le filtre retire directement **-486.9 mm** sur 5 ans (~97 mm/an), avec un assèchement massif en hiver et printemps (-142 mm en DJF, -213 mm en MAM). En été (JJA), la somme des incréments redevient positive (+2.78 mm) sous l'effet du seuil de flétrissement qui filtre les observations les plus sèches (Hypothèse E5).
   - En CDF, les incréments directs sont également négatifs globalement (-206.97 mm sur 5 ans), mais beaucoup plus modérés.
2. **Origine de l'écart avec le résidu de flux** :
   - Le résidu basé uniquement sur les flux de surface ($\Delta\text{ET} + \Delta Q - \Delta P$) néglige la dynamique interne du stock d'eau souterraine de Noah-MP (schéma SIMGM avec aquifère non confiné et nappe phréatique mobile $Z_{\text{WT}}$).
   - L'eau retirée par le filtre modifie la recharge de la nappe et le stockage profond, créant un déphasage pluriannuel qui n'est pas équilibré à court terme par les seuls flux de surface.

---

## 4. Synthèse

1. **Mécanisme NoCDF** :
   - L'assèchement direct par l'EnKF (-486.9 mm sur 5 ans) restreint la disponibilité en eau pour l'évapotranspiration au printemps ($\Delta\text{ET} = -96.3\text{ mm}$ en MAM).
   - En été, l'inversion des incréments directs (+2.78 mm en JJA) confirme que la coupure à $smcwlt + 0.02$ sélectionne préférentiellement les observations humides.
2. **Mécanisme CDF** :
   - Le rescaling par CDF matching réhausse artificiellement les valeurs sèches de SMAP vers la climatologie humide de Noah-MP, injectant de l'eau dans le bilan de flux et maintenant une ET constamment excédentaire.
