# Rapport Vague 2 : Régénération des Réponses Dynamiques et des Datasets ML DA-CDF (v2)

**Branche Git** : `elaabar`  
**Dépôt** : `smap-xai-audit`  
**Domaine d'étude** : Nord du Maroc (16 030 pixels terrestres)  
**Date d'exécution** : 5 novembre 2026  
**Auteur** : Antigravity (Assistant IA Pair-Programming) & M. El Aabaribaoune  

---

## 1. Contexte et Objectifs de la Vague 2

À la suite de la validation des contrôles physiques de premier niveau de la simulation corrigée DA-CDF (Vague 1), la **Vague 2** consiste à régénérer l'ensemble des variables de réponse aval (deltas transferts hydrologiques, références d'évapotranspiration et datasets d'apprentissage machine pour les blocs SOURCE, TRANSFER et VALUE).

Les objectifs spécifiques exécutés de manière autonome sont :
1. **Sauvegarde des sommes de contrôle NoCDF** avant toute écriture pour garantir la traçabilité.
2. **Exécution des étapes de prétraitement** : deltas transferts 25, 26, 27, 28, référence GLEAM 30, métriques d'erreur d'évaporation 31, 31b et forçages 32.
3. **Génération des datasets structurés Parquet** : `01_build_source_dataset.py`, `02_build_transfer_dataset.py`, et `03_build_value_dataset.py`.
4. **Test de non-régression strict NoCDF** : vérification bit-exacte des empreintes d'entraînement de NoCDF natif par rapport aux valeurs scellées dans `docs/modeling/05_final_rf_refit.md`.
5. **Régénération du support apparié** (`scripts/modeling/04_create_matched_support.py`) pour remplacer le fichier obsolète de septembre 2026.
6. **Arrêt formel avant la Vague 3** : aucun modèle Random Forest n'a été ré-entraîné.

---

## 2. Sauvegarde Préalable des Empreintes NoCDF

Avant de lancer les recalculs, les sommes de contrôle MD5 et tailles de fichier de toutes les sorties NoCDF existantes (étapes 25–28, 30–31b et les partitions Parquet NoCDF existantes) ont été calculées et enregistrées :
- **Fichier de sauvegarde** : `checksums_nocdf_before_vague2.json`
- **Nombre de fichiers NoCDF recensés** : 153 fichiers
- **Volume total vérifié** : 6.03 Go
- **Durée de calcul** : 32.6 secondes

---

## 3. Durées d'Exécution par Étape (Temps Réel / Wall Time)

| Étape | Script Exécuté | Description / Bloc | Durée (Wall Time) | Statut |
| :--- | :--- | :--- | :--- | :--- |
| **25** | `scripts/preprocessing/25_derive_delta_rzsm.py` | $\Delta	ext{RZSM}$ (DA - OPL, 2016–2020) | 28.2 s | Succès (code 0) |
| **26** | `scripts/preprocessing/26_derive_delta_et.py` | $\Delta	ext{ET}$ (DA - OPL, 2016–2020) | 15.3 s | Succès (code 0) |
| **27** | `scripts/preprocessing/27_derive_delta_surface_runoff.py` | $\Delta	ext{Runoff}_{	ext{surface}}$ (2016–2020) | 16.8 s | Succès (code 0) |
| **28** | `scripts/preprocessing/28_derive_delta_baseflow.py` | $\Delta	ext{Baseflow}$ (2016–2020) | 13.1 s | Succès (code 0) |
| **30** | `scripts/preprocessing/30_prepare_gleam_value_reference.py` | Harmonisation ET sur grille GLEAM (4110 cellules) | 1 min 39.9 s | Succès (code 0) |
| **31** | `scripts/preprocessing/31_derive_value_ae.py` | Erreur absolue ET vs GLEAM | 5.8 s | Succès (code 0) |
| **31b**| `scripts/preprocessing/31b_derive_assimilated_fraction.py`| Fraction assimilée projetée sur grille GLEAM | 23.3 s | Succès (code 0) |
| **32** | `scripts/preprocessing/32_derive_da_precip_forcing_difference.py` | $\Delta	ext{Precip}_{	ext{forcing}}$ (LIS EnKF bruit) | 6 min 43.0 s | Succès (code 0) |
| **DS-01**| `scripts/datasets/01_build_source_dataset.py` | Construction Parquet Bloc SOURCE (CDF & NoCDF) | 9 min 44.1 s | Succès (code 0) |
| **DS-02**| `scripts/datasets/02_build_transfer_dataset.py` | Construction Parquet Bloc TRANSFER (CDF & NoCDF) | 6 min 47.1 s | Succès (code 0) |
| **DS-03**| `scripts/datasets/03_build_value_dataset.py` | Construction Parquet Bloc VALUE (CDF & NoCDF) | 5 min 16.4 s | Succès (code 0) |
| **04** | `scripts/modeling/04_create_matched_support.py` | Résolution clés support apparié SOURCE (2016–2020) | 2 min 14.0 s | Succès (code 0) |
| **Total**| — | **Ensemble de la Vague 2** | **~35 min** | **100% Réussi** |

---

## 4. Effectifs par Bloc et par Expérience

### 4.1. Bloc SOURCE (Incréments EnKF de Surface)
Cible principale : `daily_absolute_increment`  
Grille Noah-MP : 16 030 pixels valides au Nord du Maroc.

| Échantillon | DA-CDF (v2 Régénéré) | DA-NoCDF (Figé) | Support Apparié (`matched`) | Commentaire / Évolution |
| :--- | :--- | :--- | :--- | :--- |
| **Année 2016** | 1 907 537 | 1 485 893 | — | — |
| **Année 2017** | 1 860 857 | 1 375 266 | — | — |
| **Année 2018** | 1 877 138 | 1 611 015 | — | — |
| **Année 2019** | 1 907 310 | 1 409 357 | — | — |
| **Année 2020 (Test scellé)** | 2 092 311 | 1 596 590 | — | Test 2020 scellé |
| **Période Entraînement (2016–2019)**| **7 552 842** | **5 881 531** | **4 832 928** | CDF v2 compte +28.4% d'échantillons que NoCDF |
| **Total Période Complète (2016–2020)**| **9 645 153** | **7 478 121** | **6 145 830** | vs 2 452 789 dans l'ancien parquet legacy (**x3.93**) |

### 4.2. Bloc TRANSFER (Propagation Aval des Flux et Réserves)
Cibles : `delta_rzsm`, `delta_et`, `delta_surface_runoff`, `delta_baseflow`  
Support : Évaluation continue sur la totalité des 16 030 pixels terrestres pour chaque jour valide.

| Grandeur | DA-CDF (v2) | DA-NoCDF |
| :--- | :--- | :--- |
| **Pixels par pas de temps** | 16 030 | 16 030 |
| **Jours 2016–2019 (Entraînement : 1454 j)** | **23 307 620 lignes** | **23 307 620 lignes** |
| **Jours 2020 (Test : 366 j)** | 5 866 980 lignes | 5 866 980 lignes |
| **Total 2016–2020 (1827 j)** | **29 286 810 lignes** | **29 286 810 lignes** |

### 4.3. Bloc VALUE (Impact Évapotranspiration vs GLEAM)
Cibles : `value_ae` (erreur absolue), `value_re` (erreur relative)  
Support : Évaluation sur les 4 110 cellules canoniques GLEAM à intersection spatiale validée.

| Grandeur | DA-CDF (v2) | DA-NoCDF |
| :--- | :--- | :--- |
| **Cellules GLEAM actives par jour** | 4 110 | 4 110 |
| **Jours 2016–2019 (Entraînement : 1454 j)** | **5 975 940 lignes** | **5 975 940 lignes** |
| **Jours 2020 (Test : 366 j)** | 1 504 260 lignes | 1 504 260 lignes |
| **Total 2016–2020 (1827 j)** | **7 508 970 lignes** | **7 508 970 lignes** |

---

## 5. Test de Non-Régression Strict NoCDF

Conformément aux exigences de rigueur scientifique, les empreintes MD5 des jeux d'entraînement natifs DA-NoCDF régénérés ont été comparées terme à terme avec les valeurs officielles scellées dans [`docs/modeling/05_final_rf_refit.md`](file:///home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/docs/modeling/05_final_rf_refit.md) (lignes 37–53).

| Bloc | Expérience | Cible | Support | Lignes Entraînement | Empreinte Attendue (`05_final_rf_refit.md`) | Empreinte Obtenue (Vague 2) | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SOURCE** | `da_nocdf` | `daily_absolute_increment` | native | 5 881 531 | `211550cc63ce17146cc4ff31ee602b86` | `211550cc63ce17146cc4ff31ee602b86` | **BIT-EXACT (PASS)** |
| **TRANSFER** | `da_nocdf` | `delta_baseflow` / toutes | native | 23 307 620 | `9967a50e8efe0075fd17b2748430e883` | `9967a50e8efe0075fd17b2748430e883` | **BIT-EXACT (PASS)** |
| **VALUE** | `da_nocdf` | `value_ae` | native | 5 975 940 | `3728b9e1ce23267764330503c60bf51a` | `3728b9e1ce23267764330503c60bf51a` | **BIT-EXACT (PASS)** |

**Conclusion du test de non-régression** :  
Les trois empreintes NoCDF natives correspondent au bit près. **Aucune régression ni modification accidentelle n'a affecté la chaîne NoCDF.**

---

## 6. Régénération du Support Apparié (`source_matched_support.parquet`)

Le script `scripts/modeling/04_create_matched_support.py --workspace-root .` a été ré-exécuté sur les nouveaux datasets Parquet SOURCE, remplaçant la version obsolète de septembre 2026 :

- **Lignes SOURCE DA-CDF chargées** : **9 645 153** (contre 2 452 789 dans la version obsolète, soit un facteur 3.93x)
- **Lignes SOURCE DA-NoCDF chargées** : **7 478 121** (parfaitement inchangé)
- **Intersection appariée (`matched_support`) 2016–2020** : **6 145 830 lignes** (contre 2 438 396 dans la version obsolète, soit un gain de **+152.0%** d'échantillons appariés).
- **Fichier produit** : `data/processed/modeling/splits/source_matched_support.parquet` (taille : 3.4 Mo).

---

## 7. Nouvelles Empreintes d'Entraînement DA-CDF (v2)

Pour servir de référence scellée lors de la future Vague 3 (ré-entraînement des modèles RF), les empreintes des jeux d'entraînement corrigés DA-CDF (2016–2019) sont les suivantes :

| Bloc | Expérience | Support | Nombre de Lignes (2016–2019) | Nouvelle Empreinte MD5 | Référence Historique Invalidée |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SOURCE** | `da_cdf` | native | **7 552 842** | `3710c76444e9e6d1314f656b54b510e5` | `ce91915d11055713ef307ad12b2e6192` (1 853 127 lig.) |
| **SOURCE** | `da_cdf` / `da_nocdf` | matched | **4 832 928** | `4e4a5723e8e5a2e2e69ee21871961a41` | `332ce20783aed1dcf90593a1ddc10bfa` (1 841 519 lig.) |
| **TRANSFER** | `da_cdf` | native | **23 307 620** | `9967a50e8efe0075fd17b2748430e883` | `9967a50e8efe0075fd17b2748430e883` (identique) |
| **VALUE** | `da_cdf` | native | **5 975 940** | `3728b9e1ce23267764330503c60bf51a` | `3728b9e1ce23267764330503c60bf51a` (identique) |

*(Note : Dans TRANSFER et VALUE, les empreintes de support coordonnées sont partagées car tous les pixels du domaine terrestre et toutes les cellules GLEAM communes sont évalués à chaque pas de temps).*

---

## 8. Respect des Limites : Vague 3 Non Lancée

Conformément à l'instruction stricte :
- **Aucun modèle Random Forest n'a été ré-entraîné** (`scripts/modeling/05_refit_final_rf_2016_2019.py` n'a pas été lancé pour l'entraînement).
- **Les artefacts dans `artifacts/models/` et `reports/modeling/models/` n'ont pas été modifiés.**
- La chaîne est prête pour l'exécution ordonnancée de la Vague 3 sous contrôle explicite.
