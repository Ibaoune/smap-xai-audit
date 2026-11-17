# Scripts de Construction des Datasets (`scripts/datasets/`)

**Auteur :** M. El Aabaribaoune (@um6p)
**Rôle :** Transformation des champs spatio-temporels NetCDF standardisés en tables d'apprentissage tabulaires au format Parquet pour les modèles Machine Learning (SOURCE, TRANSFER, VALUE).

---

## 1. Objectif scientifique

Le répertoire `scripts/datasets/` assure la passerelle entre la modélisation géophysique spatiale (grilles 2D/3D NetCDF à résolution $0{,}05^\circ \approx 5\text{ km}$) et l'apprentissage automatique statistique (matrices d'exemples $\times$ caractéristiques).

Chaque script répond à un objectif scientifique ciblé :
1. **`01_build_source_dataset.py` (SOURCE) :** Construire la matrice d'apprentissage pour prédire l'amplitude de l'incrément EnKF de surface à partir des conditions environnementales et météorologiques antécédentes.
2. **`02_build_transfer_dataset.py` (TRANSFER) :** Construire la matrice d'apprentissage continue pour modéliser la propagation verticale et latérale de la perturbation d'assimilation vers l'humidité racinaire et les flux de surface ($\Delta\text{RZSM}$, $\Delta\text{ET}$, $\Delta\text{Runoff}$, $\Delta\text{Baseflow}$).
3. **`03_build_value_dataset.py` (VALUE) :** Construire la matrice d'apprentissage agrégée à l'échelle $0{,}25^\circ$ pour prédire la concordance avec le produit indépendant GLEAM v4.3a.

---

## 2. Logique méthodologique et étanchéité causale

La construction des jeux de données applique un protocole rigoureux de **prévention des fuites d'information (*data leakage*)** :

- **Causalité temporelle stricte :** Tous les prédicteurs dynamiques d'états (humidité du sol) et de flux (ET, ruissellement) sont strictement décalés d'au moins un pas de temps ($t-1$).
- **Fenêtrage antécédent standardisé :** Les forçages atmosphériques et les incréments historiques sont intégrés sous forme de cumuls ou moyennes mobiles sur des fenêtres glissantes passées ($t-1$, $t-3$ à $t-1$, $t-7$ à $t-1$).
- **Interdiction des variables contemporaines :** Pour prédire une cible à la date $t$, aucune variable contemporaine issue de la simulation cible n'est autorisée en entrée, éliminant tout risque de relation circulaire ou tautologique.
- **Régimes de support spatial et d'échantillonnage :**
  - *SOURCE (Support conditionné) :* Restreint aux seuls pixel-jours où une observation SMAP a été effectivement acceptée par le filtre EnKF (`observation_frequency == 1` et innovation finie).
  - *TRANSFER (Support continu) :* Couvre l'intégralité des 16 030 pixels continentaux sur les 1 827 jours, car les processus d'infiltration et d'évaporation perdurent même en l'absence d'observation satellitaire le jour $t$.
  - *VALUE (Support macro-échelle) :* Rééchantillonné et moyenné par conservation surfacique sur la grille $0{,}25^\circ$ GLEAM (4 110 mailles continentales actives).

---

## 3. Données, variables et contrats de caractéristiques

Les caractéristiques autorisées, obligatoires et interdites sont rigoureusement spécifiées dans les configurations YAML associées :

| Script | Fichier de configuration | Cible modélisée | Nombre de prédicteurs actifs | Fichier Parquet produit |
|---|---|---|:---:|---|
| `01_build_source_dataset.py` | [`configs/datasets/source.yaml`](../../configs/datasets/source.yaml) | `daily_absolute_increment` | 35 (`context_only`) | `data/processed/modeling/source/<exp>/source_<year>.parquet` |
| `02_build_transfer_dataset.py` | [`configs/datasets/transfer.yaml`](../../configs/datasets/transfer.yaml) | $\Delta\text{RZSM}$, $\Delta\text{ET}$, $\Delta\text{Runoff}$, $\Delta\text{Baseflow}$ | 52 (`source_context`) | `data/processed/modeling/transfer/<exp>/transfer_<year>.parquet` |
| `03_build_value_dataset.py` | [`configs/datasets/value.yaml`](../../configs/datasets/value.yaml) | `value_ae` | 52 (`value_context`) | `data/processed/modeling/value/<exp>/value_<year>.parquet` |

### Focus méthodologique sur SOURCE
- **[Implémenté & Vérifié]** Le dataset SOURCE ne conserve que les pixel-jours où :
  $$\text{observation\_frequency} == 1 \quad \text{et} \quad \text{isfinite}(\text{daily\_innovation})$$
  Sur le domaine NorthMor ($0{,}05^\circ$), chaque pixel reçoit au plus un passage SMAP valide par jour civil UTC (`obs_freq` est strictement binaire $\{0, 1\}$).
- **[Implémenté & Vérifié]** Les prédicteurs actifs (`context_only_feature_set`, 35 variables) excluent délibérément l'innovation ($y - Hx^f$) et la variance de prévision ($HPH^T$) pour forcer la régression à auditer la réceptivité du sol préexistant plutôt que d'inverser le gain de Kalman.
- **[Proposé]** Variantes cibles préparées pour les expériences méthodologiques :
  1. *Signe de l'incrément :* $\text{signe}(\Delta\theta_1^a)$ avec exclusion d'une bande morte $[-\epsilon, +\epsilon]$ ($\epsilon = 0{,}002\text{ m}^3\,\text{m}^{-3}$) pour filtrer le bruit d'échantillonnage de l'ensemble EnKF.
  2. *Amplitude normalisée :* $|\Delta\theta_1^a| / \theta_{\text{fc}}$ (normalisation exploratoire par la capacité au champ).

---

## 4. Fonctionnement technique et options CLI

Chaque script s'exécute par année et par expérience :

```bash
# 1. Construction du dataset SOURCE
python scripts/datasets/01_build_source_dataset.py --experiment da_nocdf --year 2018

# 2. Construction du dataset TRANSFER
python scripts/datasets/02_build_transfer_dataset.py --experiment da_nocdf --year 2018

# 3. Construction du dataset VALUE
python scripts/datasets/03_build_value_dataset.py --experiment da_nocdf --year 2018
```

---

## 5. Validation et contrôle d'intégrité

Avant d'être transmis à la modélisation, chaque fichier Parquet généré est validé par des assertions strictes :
1. **Complétude des colonnes :** Conformité stricte avec la liste de prédicteurs définie dans le contrat YAML correspondant.
2. **Absence de valeurs manquantes :** Aucun `NaN` ou `Inf` sur les prédicteurs actifs sur l'ensemble du domaine continental valide.
3. **Contrôle d'absence de fuite :** Vérification programmatique de l'absence totale de variables contemporaines ou de références d'évaluation dans les colonnes prédictives.
4. **Cohérence du volume d'échantillons :** Vérification que le nombre de lignes correspond exactement au nombre de mailles actives multiplié par les jours du support.

---

## 6. Statut des jeux de données et références internes

- **[Vérifié]** Les tables Parquet pour l'expérience **DA-NoCDF** (2016–2020) ont été générées et validées sur le support natif.
- **[En attente]** Les tables Parquet pour la **DA-CDF corrigée** seront générées dès l'exécution finale des scripts de transfert `25` à `32`.
- **Documentation détaillée :** Consulter [`docs/datasets/`](../../docs/datasets/) pour les protocoles détaillés de standardisation et [`configs/datasets/`](../../configs/datasets/) pour les spécifications de colonnes.
