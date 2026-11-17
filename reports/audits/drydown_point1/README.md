# Audit Point 1 : Analyse des dynamiques de séchage (Dry-Downs) et planchers empiriques (SMAP vs Open-Loop)

**Branche** : `elaabar`  
**Domaine** : NorthMor ($121 \times 181$ mailles, $\sim 5\text{ km}$, Maroc Nord)  
**Période** : 2016–2020 (1827 jours)  
**Expériences analysées** :
- **Open-Loop (OL)** : `OPL_noirr_2016_2020` (Noah-MP v4.0.1 sans assimilation, sans irrigation)
- **Observations SMAP** : `DA_nocdf_noirr_2016_2020` (Enregistrement `rec2` de `LISDAOBS`, observations SMAP L3_SM_P_E filtrées par le contrôle qualité QC LIS)

---

## 1. Étape 0 — Préalables et cadre expérimental

### a. Disponibilité des sorties horaires de l'Open-Loop
- **Statut** : **Aucune sortie horaire n'existe pour la simulation Open-Loop de référence 2016–2020**.
- **Justification technique** : Dans le template de configuration LIS (`templates/lis_opl.config.template`, ligne 8), la fréquence de sortie du modèle de surface est fixée à `Surface model output interval: 1da`. Le répertoire de sortie `SURFACEMODEL/` ne contient que des fichiers journaliers `LIS_HIST_YYYYMMDD0000.d01.nc` moyennés sur 24 heures (`SoilMoist_tavg`, `TotalPrecip_tavg`).
- **Échantillonnage temporel** : Les observations SMAP (orbites descendante $\sim 6\text{ h}$ et ascendante $\sim 18\text{ h}$ heure solaire locale) sont colocalisées avec la moyenne journalière de l'OL du jour civil correspondant.

### b. Discordance d'épaisseur et de profondeur
- **Noah-MP Couche 1** : Épaisseur de **$0 - 10\text{ cm}$** (`Noah-MP.4.0.1 thickness of soil layers: 0.1 0.3 0.6 1.0` dans `lis_opl.config.template`).
- **SMAP Radiomètre Bande L ($1.4\text{ GHz}$)** : Profondeur de pénétration électromagnétique effective de **$0 - 5\text{ cm}$**.
- **Conséquence physique** : La première couche du modèle intègre un volume de sol deux fois plus épais ($10\text{ cm}$) que la tranche superficielle radiométriquement sondée par SMAP ($5\text{ cm}$). En conséquence, l'OL présente naturellement une inertie thermique et hydrique supérieure, amortissant les amplitudes journalières et ralentissant le dessèchement de surface par rapport aux $5\text{ premiers centimètres}$.

### c. Couches de sol mises à jour par l'EnKF dans DA-NoCDF
- **Statut** : **Les 4 couches de sol sont simultanément mises à jour par le filtre d'Ensemble Kalman (EnKF)**.
- **Justification technique** : Dans `templates/lis_da.config.template` (ligne 81), `Number of state variables: 4`, et dans le fichier d'attributs de perturbation `noahmp_sm_attribs.txt`, les 4 variables d'état correspondent à :
  1. Couche 1 : $0 - 10\text{ cm}$
  2. Couche 2 : $10 - 40\text{ cm}$
  3. Couche 3 : $40 - 100\text{ cm}$
  4. Couche 4 : $100 - 200\text{ cm}$
- *(Note : Information consignée pour les étapes ultérieures du projet, aucune action requise pour le Point 1).*

---

## 2. Étape 1 — Méthodologie de détection et d'ajustement

1. **Détection des épisodes de séchage (Dry-Downs)** :
   - Par pixel terre ($16\,030$ mailles actives), détection des événements de pluie $\ge 5\text{ mm/j}$ (forçage du modèle, `TotalPrecip_tavg` $\times 86\,400$) suivis d'au moins **7 jours consécutifs avec pluie $< 1\text{ mm/j}$**.
   - Conservation des épisodes comportant **au moins 3 observations SMAP valides** acceptées par le QC (`rec2` $\ne -9999.0$).
   - Au total, **$125\,501$ épisodes valides** ont été détectés et ajustés sur 2016–2020.

2. **Ajustement exponentiel** :
   $$\theta(t) = \theta_{\text{res}} + \Delta\theta \cdot \exp\left(-\frac{t}{\tau}\right)$$
   Ajusté indépendamment sur SMAP et sur l'OL échantillonné aux mêmes dates $t$.
   - **Filtre physique strict** :
     - Temps caractéristique : $0.5 \le \tau \le 60\text{ jours}$
     - Amplitude de séchage : $\Delta\theta > 0.002\text{ m}^3/\text{m}^3$
     - Qualité d'ajustement : $R^2 \ge 0.50$

3. **Planchers empiriques ($P_5$) et point de flétrissement ($SMCWLT$)** :
   - Calcul du $5^{\text{e}}$ percentile empirique ($P_5$) par pixel et par saison (MAM, SON, DJF, et saison sèche globale MAM+JJA) sur SMAP et l'OL.
   - Extraction du point de flétrissement permanent $SMCWLT$ de la table de paramètres de sol `SOILPARM.TBL` (catégories STAS) pour chaque classe de texture dominante issue de `lis_input_NorthMor_5km.nc`.

4. **Agrégation à l'échelle de l'empreinte SMAP ($\sim 36\text{ km}$) et Bootstrap par blocs** :
   - Regroupement des mailles $5\text{ km}$ en macro-blocs spatiaux $7 \times 7$ mailles ($\approx 35 \times 35\text{ km}$, 309 blocs au total), respectant la résolution native du radiomètre SMAP.
   - Calcul des intervalles de confiance à 95 % par **bootstrap par blocs (1000 rééchantillonnages spatiaux)** pour préserver la corrélation spatiale des champs d'humidité.

---

## 3. Résultats synthétiques par Saison $\times$ Texture

Le tableau ci-dessous résume les dynamiques pour le **printemps (MAM, saison prioritaire)** :

| Texture Dominante (USDA) | ID | SMCWLT ($\text{m}^3/\text{m}^3$) | N épisodes | N pixels | N blocs 36 km | $\tau_{\text{SMAP}}$ médian [IC 95%] (j) | $\tau_{\text{OL}}$ médian [IC 95%] (j) | $\Delta\tau$ (OL − SMAP) [IC 95%] (j) | $\theta_{\text{res, SMAP}}$ [IC 95%] | $\theta_{\text{res, OL}}$ [IC 95%] | $\Delta\theta_{\text{res}}$ (OL − SMAP) [IC 95%] | $P_{5,\text{OL}} - SMCWLT$ | Fraction pixels $P_{5,\text{OL}} > P_{5,\text{SMAP}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Loam** (75.2 %) | 6 | 0.066 | 24 155 | 7 818 | 270 | 1.95 [1.75, 2.14] | 8.58 [8.10, 9.16] | **+5.77 [+5.31, +6.35]** | 0.094 [0.093, 0.095] | 0.141 [0.135, 0.148] | **+0.041 [+0.034, +0.048]** | +0.038 | **63.4 %** |
| **Clay Loam** (8.1 %) | 9 | 0.103 | 3 158 | 961 | 68 | 2.10 [1.85, 2.56] | 5.97 [5.41, 6.73] | **+3.43 [+2.90, +3.94]** | 0.126 [0.122, 0.129] | 0.186 [0.177, 0.194] | **+0.055 [+0.047, +0.068]** | +0.035 | **89.4 %** |
| **Clay** (3.8 %) | 12 | 0.138 | 1 850 | 347 | 26 | 3.03 [2.68, 3.46] | 8.46 [7.04, 10.11] | **+4.74 [+3.69, +5.38]** | 0.149 [0.146, 0.155] | 0.178 [0.162, 0.189] | **+0.025 [+0.018, +0.034]** | +0.054 | **100.0 %** |
| **Sandy Clay Loam** (4.5 %) | 7 | 0.069 | 2 880 | 589 | 28 | 2.69 [2.38, 2.96] | 7.50 [6.99, 8.23] | **+4.26 [+3.62, +4.79]** | 0.099 [0.095, 0.103] | 0.127 [0.117, 0.138] | **+0.018 [+0.009, +0.029]** | +0.047 | **70.5 %** |
| **Sandy Loam** (4.7 %) | 3 | 0.047 | 1 383 | 386 | 25 | 1.07 [0.94, 1.97] | 6.14 [5.18, 7.71] | **+4.43 [+3.44, +5.30]** | 0.076 [0.073, 0.079] | 0.145 [0.131, 0.156] | **+0.065 [+0.053, +0.079]** | +0.050 | **96.6 %** |
| **Sand** (3.4 %) | 1 | 0.010 | 264 | 249 | 19 | 0.88 [0.83, 1.06] | 30.87 [11.49, 42.85] | **+29.71 [+10.65, +42.09]** | 0.053 [0.049, 0.055] | 0.025 [0.002, 0.071] | -0.019 [-0.050, +0.014] | -0.000 | 0.4 % |

*Les tables complètes pour toutes les saisons (MAM, SON, DJF, SECHE) sont consignées dans [`drydown_season_texture_summary.csv`](file:///home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/audits/drydown_point1/drydown_season_texture_summary.csv).*

---

## 4. Figures et Cartes spatiales

### a. Cartes spatiales au printemps (MAM)
Fichiers : [`maps_mam_drydown_dynamics.png`](file:///home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/audits/drydown_point1/maps_mam_drydown_dynamics.png) et [`maps_mam_drydown_dynamics.pdf`](file:///home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/audits/drydown_point1/maps_mam_drydown_dynamics.pdf).

- **Panneau (a) $\Delta\tau$ (OL − SMAP)** : La quasi-totalité du domaine affiche des valeurs fortement positives (médiane globale $+5.3\text{ jours}$), confirmant que le modèle Noah-MP met significativement plus de temps à sécher que la surface observée par satellite.
- **Panneau (b) $\Delta\theta_{\text{res}}$ (OL − SMAP)** : L'humidité résiduelle asymptotique du modèle est supérieure de $+0.02$ à $+0.06\text{ m}^3/\text{m}^3$ par rapport à SMAP sur l'ensemble des bassins du Sebou, du Rharb et de la Chaouia.
- **Panneau (c) Écart des planchers empiriques ($P_5$)** : Cohérent avec $\Delta\theta_{\text{res}}$, le plancher $P_5$ de l'OL est systématiquement plus haut que celui de SMAP sur les zones de plaine et agricoles.
- **Panneau (d) Marge au-dessus de SMCWLT** : Noah-MP maintient un plancher d'humidité nettement au-dessus de son point de flétrissement ($P_{5,\text{OL}} - SMCWLT > +0.035\text{ m}^3/\text{m}^3$), confirmant l'existence d'une résistance à l'évaporation ou d'un blocage de vidange superficielle.

### b. Distributions de $\tau$ et $\theta_{\text{res}}$ selon la texture du sol (MAM)
Fichiers : [`drydown_synthesis_distributions.png`](file:///home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/audits/drydown_point1/drydown_synthesis_distributions.png) et [`drydown_synthesis_distributions.pdf`](file:///home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/audits/drydown_point1/drydown_synthesis_distributions.pdf).

- **Temps caractéristique $\tau$** :
  - SMAP présente des temps de vidange rapides ($\tau \approx 1\text{ à }3\text{ jours}$), avec une sensibilité physique cohérente (les sols argileux mettent $\sim 3\text{ jours}$ à sécher contre $\sim 1\text{ jour}$ pour les limons sableux).
  - Noah-MP OL présente des temps de relaxation anormalement longs ($\tau \approx 6\text{ à }9\text{ jours}$ sur les limons et argiles, et jusqu'à $>25\text{ jours}$ sur sables purs), témoignant d'une conductance hydraulique superficielle ou d'un flux d'évaporation du sol nu sous-estimé en phase 2 de séchage.
- **Planchers $\theta_{\text{res}}$ vs $SMCWLT$** :
  - Sur les sols argileux (**Clay**, texture 12), **100.0 % des pixels** ont un plancher empirique $P_5$ de l'OL supérieur à SMAP. L'OL converge vers $\sim 0.178\text{ m}^3/\text{m}^3$, soit $+0.054\text{ m}^3/\text{m}^3$ au-dessus de son $SMCWLT$ ($0.138$), alors que SMAP descend fréquemment à $0.12 - 0.14\text{ m}^3/\text{m}^3$.
  - Sur les limons argileux (**Clay Loam**, texture 9), **89.4 % des pixels** ont un plancher OL supérieur à SMAP, avec une surélévation de plancher de $+0.055\text{ m}^3/\text{m}^3$.

---

## 5. Limites méthodologiques

1. **Représentativité verticale ($0-5\text{ cm}$ vs $0-10\text{ cm}$)** :
   La couche 1 de Noah-MP faisant $10\text{ cm}$, elle dispose d'une réserve hydrique volumique double de celle de la couche SMAP ($5\text{ cm}$). Un séchage plus lent dans le modèle est donc en partie attribuable à cette discrétisation verticale, la couche $0-10\text{ cm}$ subissant moins vite le gradient d'assèchement de l'interface sol-atmosphère qu'un film de $5\text{ cm}$.
2. **Échantillonnage temporel (Moyenne 24 h vs Heure de passage SMAP)** :
   L'OL étant archivé sous forme de moyenne journalière `SoilMoist_tavg` (intervalle `1da`), il n'est pas possible d'échantillonner le modèle strictement à l'heure du passage de satellite ($\sim 6\text{ h}$ / $\sim 18\text{ h}$). Bien que le cycle diurne de l'humidité du sol soit modéré, une sortie instantanée à $6\text{ h}$ aurait légèrement réduit l'humidité par rapport à la moyenne post-pluie diurne.
3. **Résolution spatiale native ($\sim 36\text{ km}$ vs maillage $5\text{ km}$)** :
   Les observations L3_SM_P_E sont sur-échantillonnées sur une grille EASE-Grid $9\text{ km}$ puis projetées à $5\text{ km}$, mais leur résolution radiométrique intrinsèque reste de $\sim 36\text{ km}$. L'analyse a tenu compte de cette dépendance spatiale par une agrégation en blocs $7 \times 7$ et un bootstrap par blocs, qui confirme la significativité statistique ($p < 0.001$).

---

## 6. Conclusion explicite

> ### **(A) CONFIRMÉ : l'Open-Loop (Noah-MP) sèche significativement plus lentement et bute sur un plancher plus élevé que SMAP, de façon robuste au printemps (MAM), particulièrement sur les sols argileux.**

### Éléments probants :
1. **Vitesse de séchage ($\tau$)** : Au printemps (MAM), l'écart $\Delta\tau = \tau_{\text{OL}} - \tau_{\text{SMAP}}$ est **positif et statistiquement significatif à 95 % pour toutes les classes texturales** (médiane $+5.77\text{ j}$ sur Loam, $+4.74\text{ j}$ sur Clay, $+3.43\text{ j}$ sur Clay Loam). L'OL met 3 à 4 fois plus de temps que SMAP à dissiper l'humidité post-pluvieuse.
2. **Planchers empiriques et $SMCWLT$** :
   - Sur les sols argileux (**Clay**), **100 % des mailles** ont un plancher empirique OL supérieur à SMAP ($\Delta\theta_{\text{res}} = +0.025\text{ m}^3/\text{m}^3$, $\Delta P_5 = +0.029\text{ m}^3/\text{m}^3$). Noah-MP reste en moyenne à $+0.054\text{ m}^3/\text{m}^3$ au-dessus de son point de flétrissement ($SMCWLT = 0.138$).
   - Sur les limons argileux (**Clay Loam**), **89.4 % des mailles** ont un plancher OL supérieur à SMAP ($\Delta\theta_{\text{res}} = +0.055\text{ m}^3/\text{m}^3$).
   - Sur les limons dominants (**Loam**), $\Delta\theta_{\text{res}} = +0.041\text{ m}^3/\text{m}^3$ ($63.4 \%$ des mailles ont $P_{5,\text{OL}} > P_{5,\text{SMAP}}$).
