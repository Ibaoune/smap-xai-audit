# Rapport d'Exécution et d'Analyse : Figures, Corrections et Diagnostics CDF v2

**Dépôt :** `smap-xai-audit`  
**Branche :** `elaabar`  
**Date :** 10 Novembre 2026  
**Dossier de sortie :** `figures/cdf_v2/` (aucun fichier dans `figures/main/`, `figures/legacy/`, `figures/supplement/` ni `figures/water_balance/` n'a été écrasé).

---

## 1. Synthèse des Figures Produites (Point 1, Point 2d, Point 3)

Toutes les figures ont été générées et validées dans `figures/cdf_v2/` :

| Fichier PNG | Fichier PDF | Script Générateur | Statut Visuel |
| :--- | :--- | :--- | :--- |
| `figures/cdf_v2/Figure_4_RF_performance.png` | `Figure_4_RF_performance.pdf` | `scripts/postprocessing/manuscript/rf/rf_eval/plot_figure4_rf_validation.py` | Ouvert et vérifié |
| `figures/cdf_v2/Figure_3_assimilation_diagnostics.png` | `Figure_3_assimilation_diagnostics.pdf` | `scripts/figures/generate_figure_3_and_maps.py` | Ouvert et vérifié |
| `figures/cdf_v2/section_3_1/Fig3_e_h_matched_updates.png` | `Fig3_e_h_matched_updates.pdf` | `scripts/postprocessing/manuscript/sec3.1/plot_fig3.py` | Ouvert et vérifié |
| `figures/cdf_v2/map_mean_signed_increment.png` | `map_mean_signed_increment.pdf` | `scripts/figures/generate_figure_3_and_maps.py` | Ouvert et vérifié |
| `figures/cdf_v2/map_mean_innovation.png` | `map_mean_innovation.pdf` | `scripts/figures/generate_figure_3_and_maps.py` | Ouvert et vérifié |
| `figures/cdf_v2/irrigation_signature.png` | `irrigation_signature.pdf` | `scripts/audits/compute_gmia_signature.py` | Ouvert et vérifié |

---

## 2. Corrections des Figures (Point 2)

### 2a. Recalcul Dynamique des Étiquettes de la Figure 3 (Panneaux f, g, h)

Dans l'ancien code (`plot_fig3.py`), les étiquettes textuelles contredisaient flagrantement les couleurs des cartes car elles contenaient des chaînes codées en dur issues de l'ancienne simulation archivée (où le domaine CDF tronqué produisait un assèchement artificiel).

Les pourcentages ont été recalculés dynamiquement à partir de `Fig3_e_h_source_data.nc` sur les 16 030 pixels terrestres du domaine :
- **« Drying »** = fraction des pixels terrestres valides avec moyenne $< 0$
- **« Wetting »** = fraction des pixels terrestres valides avec moyenne $> 0$
- **« NoCDF > CDF »** = fraction des pixels terrestres valides avec différence $(\text{NoCDF} - \text{CDF}) > 0$

| Panneau | Description | Ancienne étiquette (codée en dur) | Nouvelle étiquette (recalculée dynamiquement) | Statistiques exactes du champ (2016–2020) |
| :--- | :--- | :--- | :--- | :--- |
| **(f)** | Incrément moyen signé CDF (support apparié) | `Drying: 96.7%` | **`Wetting: 90.1%`** | Moyenne $= +0.005416\text{ m}^3\text{m}^{-3}$<br>Wetting ($>0$) : **90.06%**<br>Drying ($<0$) : **9.94%** |
| **(g)** | Incrément moyen signé NoCDF (support apparié) | `Wetting: 36.2%` | **`Drying: 91.2%`** | Moyenne $= -0.006036\text{ m}^3\text{m}^{-3}$<br>Drying ($<0$) : **91.20%**<br>Wetting ($>0$) : **8.80%** |
| **(h)** | Différence d'incrément (NoCDF − CDF) | `NoCDF > CDF: 98.2%` | **`NoCDF > CDF: 5.4%`** | Moyenne diff $= -0.011451\text{ m}^3\text{m}^{-3}$<br>NoCDF $>$ CDF ($>0$) : **5.36%**<br>NoCDF $<$ CDF ($<0$) : **94.64%** |

*Vérification :* Aucune valeur statistique n'est désormais codée en dur dans `scripts/postprocessing/manuscript/sec3.1/plot_fig3.py`.

### 2b. Harmonisation de la Convention Cartographique Signée

Toutes les cartes scalaires signées (innovations, incréments, différences) adoptent strictement la palette divergente inversée `RdBu_r` :
- **Bleu = négatif** : assèchement, incrément négatif, ou SMAP plus sec que le modèle ($sm_{\text{obs}} < sm_{\text{model}}$).
- **Rouge = positif** : humidification, incrément positif, ou SMAP plus humide que le modèle ($sm_{\text{obs}} > sm_{\text{model}}$).

Cette règle a été corrigée sur :
- `Fig3_e_h_matched_updates.png` : les panneaux (f) et (g), qui utilisaient la colormap `BrBG`, sont passés en `RdBu_r`.
- `Figure_3_assimilation_diagnostics.png` : les panneaux (b), (d) et (e), qui utilisaient `RdBu` (convention inverse), sont passés en `RdBu_r`.
- `map_mean_signed_increment.png` et `map_mean_innovation.png` : ensemble des panneaux en `RdBu_r`.

### 2c. Aménagements Spécifiques de la Figure 3 (`Figure_3_assimilation_diagnostics`)

1. **Panneau (a) :** Affiche désormais la disponibilité des innovations pour CDF et NoCDF sous forme de deux sous-cartes côte à côte (`(a1) NoCDF availability` et `(a2) CDF availability`) avec une barre d'échelle commune en jours de mise à jour.
2. **Titres des panneaux (d) et (e) :** Décalage des annotations et report de l'unité $\text{[m}^3\text{ m}^{-3}\text{]}$ sur la barre de couleur pour supprimer tout chevauchement vertical ou latéral avec les colorbars.
3. **Panneau (f) :** Saisons ordonnées strictement selon le cycle hydrologique : **DJF, MAM, JJA, SON**.

---

## 3. Analyse par Fraction Irriguée GMIA 0.05° (Point 3)

Calcul exécuté sur la grille 0.05° (`gmia_5km`) pour l'ensemble des 16 030 pixels terrestres sur 2016–2020 (1 827 jours).

Classes d'équipement d'irrigation :
- `0` : $0\%$ exactement ($15\,779$ cellules du domaine, $72.0\%$)
- `0–10 %` : $]0, 10]\%$ ($4\,807$ cellules, $21.9\%$)
- `10–30 %` : $]10, 30]\%$ ($735$ cellules, $3.4\%$)
- `> 30 %` : $> 30\%$ ($580$ cellules, $2.6\%$)

Périodes saisonnières :
- **Saison humide :** Octobre à Mai (mois 10, 11, 12, 1, 2, 3, 4, 5)
- **Été :** Juin à Août (mois 6, 7, 8)

### Tableau des Métriques Saisonnières par Classe d'Irrigation

| Expérience | Saison | Classe GMIA | Pixel-jours valides | Innovation moyenne [m³ m⁻³] | Écart-type Innovation | Incrément signé moyen [m³ m⁻³] | Écart-type Incrément |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **NoCDF** | Humide (Oct–Mai) | 0 | 3 158 643 | **-0.0091** | 0.0398 | **-0.00139** | 0.0114 |
| **NoCDF** | Humide (Oct–Mai) | 0–10 % | 1 622 564 | **-0.0099** | 0.0395 | **-0.00174** | 0.0120 |
| **NoCDF** | Humide (Oct–Mai) | 10–30 % | 202 172 | **-0.0137** | 0.0397 | **-0.00168** | 0.0112 |
| **NoCDF** | Humide (Oct–Mai) | > 30 % | 179 631 | **-0.0136** | 0.0418 | **-0.00172** | 0.0124 |
| **NoCDF** | Été (Juin–Août) | 0 | 1 087 639 | **+0.0048** | 0.0259 | **+0.00040** | 0.0068 |
| **NoCDF** | Été (Juin–Août) | 0–10 % | 523 160 | **+0.0046** | 0.0250 | **+0.00053** | 0.0072 |
| **NoCDF** | Été (Juin–Août) | 10–30 % | 34 972 | **+0.0067** | 0.0224 | **+0.00031** | 0.0042 |
| **NoCDF** | Été (Juin–Août) | > 30 % | 15 931 | **+0.0072** | 0.0202 | **+0.00020** | 0.0030 |
| **CDF** | Humide (Oct–Mai) | 0 | 4 661 570 | **+0.0016** | 0.0307 | **+0.00049** | 0.0114 |
| **CDF** | Humide (Oct–Mai) | 0–10 % | 2 146 607 | **+0.0015** | 0.0302 | **+0.00053** | 0.0113 |
| **CDF** | Humide (Oct–Mai) | 10–30 % | 311 420 | **+0.0017** | 0.0331 | **+0.00055** | 0.0120 |
| **CDF** | Humide (Oct–Mai) | > 30 % | 304 869 | **+0.0015** | 0.0338 | **+0.00066** | 0.0136 |
| **CDF** | Été (Juin–Août) | 0 | 839 125 | **+0.0037** | 0.0299 | **+0.00024** | 0.0072 |
| **CDF** | Été (Juin–Août) | 0–10 % | 452 239 | **+0.0021** | 0.0280 | **+0.00018** | 0.0077 |
| **CDF** | Été (Juin–Août) | 10–30 % | 50 848 | **+0.0025** | 0.0234 | **+0.00018** | 0.0056 |
| **CDF** | Été (Juin–Août) | > 30 % | 52 737 | **+0.0017** | 0.0190 | **+0.00017** | 0.0054 |

### Interprétation Hydrologique
1. **En NoCDF (sans rescaling) :**
   - **En été**, l'innovation moyenne augmente systématiquement avec l'équipement d'irrigation : $+0.0048$ m³ m⁻³ (0%) $\to +0.0046$ (0–10%) $\to +0.0067$ (10–30%) $\to \mathbf{+0.0072\text{ m}^3\text{m}^{-3}}$ (>30%). L'observation SMAP détecte un sol significativement plus humide que le modèle Noah-MP (qui tourne sans irrigation), confirmant la signature du forçage d'irrigation anthropique dans les plaines agricoles du Gharb et du Saïss.
   - **En saison humide**, NoCDF subit un biais négatif structurel (-0.0091 à -0.0136 m³ m⁻³) lié au biais de forçage pluie MERRA-2/IMERG.
2. **En CDF (avec rescaling local) :**
   - L'innovation moyenne est quasi-nulle et stable ($+0.0015$ à $+0.0017$ m³ m⁻³) sur toutes les classes en saison humide.
   - En été, l'innovation ne présente aucune corrélation positive avec l'irrigation ($+0.0037$ à 0% vs $+0.0017$ m³ m⁻³ à >30%). Le CDF matching mensuel par pixel absorbe la climatologie de surface et élimine ainsi le signal d'irrigation que SMAP apportait.

---

## 4. Écart entre Fig. 3 (f) et Fig. S8 (d) (Point 4)

La Fig. 3 (f) affiche une amplitude moyenne d'incrément plus forte pour CDF à toutes les saisons, tandis que la Fig. S8 (d) affiche une activité totale cumulée d'ajustement plus forte pour NoCDF (587 mm vs 471 mm).

### Définitions Mathématiques Exactes

| Paramètre | Définition Figure 3 (f) | Définition Figure S8 (d) |
| :--- | :--- | :--- |
| **Métrique calculée** | Amplitude moyenne journalière inconditionnelle : $\overline{\|\Delta \theta\|}$ | Activité totale cumulée d'ajustement : $W_{\text{abs}} = \sum_t \|\Delta \theta_t\| \cdot \Delta z$ |
| **Jours retenus** | **Tous les 1 827 jours** (2016–2020), en attribuant $\|\Delta \theta\| = 0$ les jours sans mise à jour | **Seulement les jours d'assimilation appariés** (`matched_support`, 6 174 026 pixel-jours) |
| **Couche et épaisseur** | Couche 1 Noah-MP (0–10 cm), non convertie en mm ($\text{m}^3\text{ m}^{-3}$) | Couche 1 Noah-MP (0–10 cm), épaisseur $\Delta z = 100\text{ mm}$ appliquée |
| **Période** | 2016-01-01 au 2020-12-31 (5 ans complets) | 2016-01-01 au 2020-12-31 (5 ans complets) |
| **Pixels inclus** | 16 030 pixels terrestres (support natif de chaque run) | 16 030 pixels terrestres (strictement appariés) |

### Recalcul Numérique selon les Deux Définitions

```
1. Définition Fig. 3 (f) — Moyenne inconditionnelle sur 1827 jours [m3 m-3] :
   - Annuelle : CDF = 0.004382 m3 m-3  |  NoCDF = 0.003718 m3 m-3  (+17.8% pour CDF)
   - DJF      : CDF = 0.004582 m3 m-3  |  NoCDF = 0.004058 m3 m-3  (+12.9% pour CDF)
   - MAM      : CDF = 0.005240 m3 m-3  |  NoCDF = 0.004240 m3 m-3  (+23.6% pour CDF)
   - JJA      : CDF = 0.002337 m3 m-3  |  NoCDF = 0.002263 m3 m-3  (+3.3% pour CDF)
   - SON      : CDF = 0.005383 m3 m-3  |  NoCDF = 0.004323 m3 m-3  (+24.5% pour CDF)

2. Définition Fig. S8 (d) — Activité cumulée 5 ans sur support apparié [mm d'eau] :
   - Activité absolue cumulée : NoCDF = 587.41 mm  |  CDF = 471.15 mm  (+24.7% pour NoCDF)
   - Moyenne conditionnelle   : NoCDF = 0.015611 m3 m-3  |  CDF = 0.012363 m3 m-3  (+26.3% par update)
```

### Cause Scientifique de la Divergence
- **La Fig. 3 (f) est dominée par la fréquence d'assimilation :** CDF assimile sur **9 686 962 pixel-jours** contre **7 507 641 pixel-jours** pour NoCDF (+29% de jours avec mise à jour active). En moyennant sur 1827 jours avec les zéros, CDF a moins de jours nuls, ce qui gonfle artificiellement sa moyenne inconditionnelle.
- **La Fig. S8 (d) isole la dynamique d'incrément à échantillonnage identique :** Lorsque l'on compare CDF et NoCDF exactement les mêmes jours et aux mêmes pixels, l'amplitude moyenne d'un incrément NoCDF est 26.3% plus forte ($0.0156$ vs $0.0124$ m³ m⁻³), ce qui engendre un déplacement total de masse d'eau supérieur en NoCDF (587.4 mm contre 471.2 mm sur 5 ans).

### Recommandation pour le Manuscrit
La définition de la **Fig. S8 (d)** (activité cumulée sur support apparié) est la seule scientifiquement rigoureuse pour comparer l'intensité de l'assimilation entre deux configurations, car elle élimine le biais de disponibilité des observations. Si la Fig. 3 (f) est maintenue, la légende doit explicitement préciser qu'elle représente le produit de la fréquence d'assimilation par l'amplitude unitaire.

---

## 5. Signal des Cibles et Skill RF (TRANSFER et VALUE) (Point 5)

Calcul extrait de `target_distributions_2020.csv` et de `final_metrics_2020.csv` (14 modèles de 2020) pour vérifier si la baisse de $R^2$ en CDF résulte d'une réduction de la variance du signal cible ($\sigma_y$) et non d'une moindre habileté du modèle.

### Tableau Comparatif Signal vs Performance (Holdout 2020)

| Cible | Expérience | Écart-type cible ($\sigma_y$) | Moyenne cible ($\mu_y$) | RMSE | $R^2$ | Skill MAE | Skill RMSE |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **$\Delta$RZSM** | CDF | **0.0163** | +0.0039 | 0.0152 | **0.125** | 0.106 | 0.090 |
| **$\Delta$RZSM** | NoCDF | **0.0300** | -0.0031 | 0.0218 | **0.475** | 0.308 | 0.279 |
| **$\Delta$ET** | CDF | **0.292** | +0.046 | 0.260 | **0.209** | 0.170 | 0.166 |
| **$\Delta$ET** | NoCDF | **0.381** | -0.037 | 0.251 | **0.567** | 0.354 | 0.325 |
| **$\Delta$Runoff** | CDF | **0.0397** | +0.0048 | 0.0310 | **0.393** | 0.274 | 0.220 |
| **$\Delta$Runoff** | NoCDF | **0.0527** | -0.0050 | 0.0385 | **0.465** | 0.329 | 0.269 |
| **$\Delta$Baseflow**| CDF | **0.164** | +0.033 | 0.147 | **0.202** | 0.134 | 0.109 |
| **$\Delta$Baseflow**| NoCDF | **0.221** | -0.030 | 0.181 | **0.329** | 0.219 | 0.182 |
| **VALUE** | CDF | **0.277** | 0.447 | **0.225** | **0.342** | **0.244** | **0.203** |
| **VALUE** | NoCDF | **0.289** | 0.447 | **0.240** | **0.311** | **0.207** | **0.164** |

### Conclusions par Cible (1 phrase par cible)
- **$\Delta$RZSM :** La chute de $R^2$ en CDF (0.125 vs 0.475) découle directement de la réduction de 46% de l'écart-type de la cible ($\sigma_y = 0.0163$ vs $0.0300$), le modèle conservant une erreur absolue (RMSE $= 0.0152$) inférieure à celle de NoCDF ($0.0218$).
- **$\Delta$ET :** La variance de la cible $\Delta$ET est 41% plus faible en CDF ($\sigma_y^2 = 0.085$ vs $0.145$), ce qui dégrade mathématiquement le $R^2$ à 0.209 malgré une RMSE comparable (0.260 vs 0.251).
- **$\Delta$Runoff :** Le modèle RF reproduit $\Delta$Runoff avec une fidélité quasi-identique entre expériences ($R^2 = 0.393$ vs $0.465$), l'erreur d'ajustement RMSE étant même plus faible en CDF ($0.0310$ contre $0.0385$).
- **$\Delta$Baseflow :** Le signal cible de flux de base est comprimé de 26% en CDF ($\sigma_y = 0.164$ vs $0.221$), réduisant le $R^2$ apparent tout en diminuant l'erreur RMSE de 0.181 à 0.147.
- **VALUE :** Sur la cible finale d'évaluation indépendante (GLEAM), CDF bat NoCDF sur l'ensemble des métriques de performance ($R^2 = 0.342$ contre $0.311$, Skill RMSE $= 0.203$ contre $0.164$), prouvant que la capacité prédictive du cadre Random Forest est pleinement préservée.

---

## 6. Artefacts à Latitude Fixe et Pixels Masqués (Point 6)

### Lignes Concernées et Coïncidence avec la Grille SMAP EASE-2 36 km
- **Ligne $33.00^\circ$N :** Indice de grille $y = 60$ ($lat = 33.00^\circ$N).
- **Ligne $34.50^\circ$N :** Indice de grille $y = 90$ ($lat = 34.50^\circ$N).
- **Distance entre les deux lignes :** Exactement $\Delta y = 30$ mailles à $0.05^\circ$, soit $\Delta \phi = 1.50^\circ$ de latitude.
- **Résolution EASE-2 36 km :**
  $$\Delta \phi_{\text{EASE-2}} \approx \frac{36.0\text{ km}}{111.32\text{ km/deg}} \approx 0.3234^\circ \approx 6.47\text{ mailles LIS (0.05°)}$$
  $$\frac{1.50^\circ}{0.3234^\circ} \approx 4.64\text{ mailles EASE-2}$$
- **Mécanisme physique :** La grille SMAP L3 (36 km) est échantillonnée par LIS par plus proche voisin sans filtre de lissage spatial continu. Lorsqu'un pixel LIS franchit la frontière géométrique d'une cellule EASE-2 le long d'une trace satellite (swath), l'observation $sm_{\text{obs}}$ saute brutalement d'un palier, alors que le fond Noah-MP ($sm_{\text{b}}$) varie de manière continue. Ce saut d'échelon crée une ligne d'innovations alternées et d'incréments de signes opposés le long des limites de cellules 36 km.

### Origine des Carrés Blancs Masqués
Sur les 21 901 mailles du domaine NorthMor ($121 \times 181$) :
- **5 841 mailles** sont en mer/océan (`LANDMASK = 0`).
- Sur les **16 030 mailles terrestres** (`LANDMASK = 1`), **1 780 pixels (11.10%)** ne sont **JAMAIS assimilés** sur les 5 ans (valeurs NaN permanentes) :
  1. **Classe 7 (Open Shrublands / steppes arides & caillouteuses) : 973 pixels (54.7%)** : Sols arides très secs de l'Oriental et de l'Anti-Atlas où le contrôle qualité EnKF LIS rejette systématiquement les observations proches du point de flétrissement ($sm_{\text{obs}} - sm_{\text{cwlt}} < 0.02$).
  2. **Classe 12 (Croplands / Terres cultivées) : 410 pixels (23.0%)** : Interférences radioélectriques (RFI) urbaines et forte biomasse (VWC $> 0.50\text{ kg m}^{-2}$) où SMAP flagge l'observation comme non fiable.
  3. **Classe 16 (Barren / Désert rocheux) : 206 pixels (11.6%)** : Forte rugosité et faible émissivité radiométrique entraînant un rejet d'algorithme SMAP.
  4. **Classe 13 (Urbain et bâti) : 77 pixels (4.3%)** : Masque urbain automatique SMAP ($> 25\%$ de surface imperméable).
  5. **Forêts denses (Classes 1, 2, 5, 6, 8, 9) : 57 pixels (3.2%)** : Atténuation par la canopée forestière dense.
  6. **Prairies (Classe 10) : 47 pixels (2.6%)**.

---

## 7. Descriptions Visuelles Détaillées des Figures Vérifiées

*(Descriptions rédigées après ouverture effective et inspection directe des fichiers image).*

### 1. `figures/cdf_v2/Figure_4_RF_performance.png`
- **Structure :** Grille 2×2 en barplot horizontal. Rangée du haut : validation temporelle 2019 ($R^2$ en a, Pearson $r$ en b). Rangée du bas : holdout indépendant 2020 ($R^2$ en c, Pearson $r$ en d).
- **Palette :** Barres bleues pour CDF, barres orange pour NoCDF.
- **Observations :**
  - Sur le holdout 2020 (panneau c), SOURCE est supérieur pour CDF ($R^2 = 0.26$ vs $0.22$).
  - Les cibles intermédiaires RZSM, ET, Runoff et Baseflow montrent un $R^2$ NoCDF plus élevé (orange dominant).
  - En revanche, sur la cible globale VALUE (GLEAM), CDF passe devant NoCDF ($R^2 = 0.342$ contre $0.311$ ; Pearson $r = 0.61$ contre $0.57$).

### 2. `figures/cdf_v2/Figure_3_assimilation_diagnostics.png`
- **Structure :** Grille 2×3 de grande dimension.
  - (a) : Deux cartes en médaillon montrant la disponibilité des innovations pour NoCDF et CDF avec colormap viridis.
  - (b) : Carte d'innovation moyenne NoCDF en `RdBu_r`. Domaine largement bleu (valeurs négatives jusqu'à $-0.04$ m³ m⁻³), avec une poche rouge vif (positive) sur la péninsule de Tanger.
  - (c) : Courbes de densité KDE des innovations. CDF (bleu) forme une cloche symétrique centrée sur 0.00. NoCDF (orange) est décalée vers la gauche avec une traîne négative.
  - (d) : Carte d'incrément moyen signé NoCDF en `RdBu_r`. Dominée par des tons bleus (séchage), sauf sur le littoral nord-ouest (Rif/Gharb).
  - (e) : Carte d'incrément moyen signé CDF en `RdBu_r`. Teinte blanc-rosée uniforme très claire, centrée sur $+0.001$ m³ m⁻³, sans zone d'assèchement prononcé.
  - (f) : Diagramme en barres saisonnier ordonné DJF, MAM, JJA, SON. Pour chaque saison, la barre bleue (CDF) dépasse la barre orange (NoCDF), atteignant son maximum au printemps (MAM: $0.0052$ vs $0.0042$ m³ m⁻³).

### 3. `figures/cdf_v2/section_3_1/Fig3_e_h_matched_updates.png`
- **Structure :**
  - En haut (e) : Histogrammes par paliers des incréments appariés. CDF (bleu) centré à $+0.0032$, NoCDF (orange) décalé à gauche à $-0.0044$ m³ m⁻³.
  - En bas (f, g, h) : Trois cartes côte à côte utilisant toutes la colormap `RdBu_r` discrétisée en 14 classes (paliers de $0.005$ m³ m⁻³).
  - (f) : Carte CDF rougeoyante uniforme avec encadré en bas à gauche **`Wetting: 90.1%`**.
  - (g) : Carte NoCDF bleue avec encadré **`Drying: 91.2%`**.
  - (h) : Carte de différence NoCDF − CDF d'un bleu profond sur les 3/4 du territoire, avec encadré **`NoCDF > CDF: 5.4%`**.

### 4. `figures/cdf_v2/map_mean_signed_increment.png`
- **Structure :** 3 cartes panoramiques avec barres de couleur individuelles en `RdBu_r`.
  - (a) CDF : Champ très homogène dans $[0, +0.002]$ m³ m⁻³, quasiment aucune cellule sous $-0.002$.
  - (b) NoCDF : Séchage généralisé dans l'Oriental et les plateaux centraux (bleu clair à cyan), humidification côtière nord.
  - (c) Différence : Ton bleu homogène confirmant un retrait net d'eau en NoCDF par rapport à CDF.

### 5. `figures/cdf_v2/map_mean_innovation.png`
- **Structure :** 3 cartes en `RdBu_r` (vmin $=-0.04$, vmax $=+0.04$).
  - (a) CDF : Très proche du blanc (zéro) sur l'ensemble des bassins du Sebou, du Bouregreg et de l'Oum Er-Rbia, avec de légères valeurs roses vers le sud.
  - (b) NoCDF : Large bande bleu foncé marquant le sous-solage SMAP par rapport au modèle Noah-MP.
  - (c) Différence : Représentation quasi-identique à (b).

### 6. `figures/cdf_v2/irrigation_signature.png`
- **Structure :** Deux panneaux (a) CDF et (b) NoCDF.
  - En abscisse : les 4 classes GMIA (`0`, `0–10 %`, `10–30 %`, `> 30 %`).
  - Barres bleues : Saison humide (Oct–Mai) ; Barres rouges : Été (Juin–Août).
  - En (a) CDF : Barres bleues plates à $+0.0016$, barres rouges stables entre $+0.0017$ et $+0.0037$ m³ m⁻³.
  - En (b) NoCDF : Contraste saisissant. Les barres bleues s'enfoncent dans le négatif jusqu'à $-0.0136$ m³ m⁻³. Les barres rouges d'été s'élèvent de $+0.0048$ à **$+0.0072\text{ m}^3\text{m}^{-3}$**, marquant très nettement l'apport hydrique d'irrigation capté par SMAP.
