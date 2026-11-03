# Scripts d'Audit Scientifique et Diagnostique (`scripts/audits/`)

**Auteur :** M. El Aabaribaoune (@um6p)
**Rôle :** Scripts spécialisés pour l'audit approfondi des simulations d'assimilation, la vérification des anomalies géométriques et physiques, et la traçabilité des métriques figées.

---

## 1. Objectif scientifique

Le répertoire `scripts/audits/` centralise les scripts d'investigation développés pour tester la robustesse physique et méthodologique des données d'assimilation et des modèles de surface. Il a notamment permis :
1. De détecter et documenter formellement la discordance de grille géographique qui a conduit à l'invalidation de l'ancienne simulation DA-CDF.
2. D'analyser le comportement de Noah-MP en conditions de stress hydrique sévère (texture du sol, point de flétrissement, cycles diurnes).
3. D'évaluer l'impact de l'irrigation (GMIA) et la structure des innovations SMAP.
4. D'exporter de manière déterministe et reproductible les métriques vérifiées de la chaîne DA-NoCDF sur le banc d'essai scellé 2020.

---

## 2. Thématiques d'audit et scripts associés

### A. Géométrie du domaine et validité de la correction CDF
- **`check_cdf_domain.py` & `audit_cdf_validity.py` :** Vérifient les bornes spatiales ($121 \times 181$ NorthMor vs grilles historiques) et inspectent les fichiers de paramètres CDF de LIS (`cdf_param_*.nc`).
- **`eval_da_cdf_test.py` :** Compare le comportement statistique préliminaire des innovations avant et après correction.

### B. Propriétés texturales et physique de l'assèchement
- **`audit_soil_texture_and_wilt_analysis.py` :** Analyse détaillée de la cohérence entre les classes de texture STATSGO, la porosité et le point de flétrissement volumique ($\theta_{\text{wilt}}$) dans Noah-MP.
- **`point_d_compare_nowilt_vs_control.py` :** Évalue la sensibilité des flux d'évaporation lorsque le seuil de flétrissement est modifié ou neutralisé.

### C. Dynamique temporelle et signaux anthropiques
- **`point_b_hourly_diurnal_analysis.py` :** Diagnostic de la décomposition sous-journalière (horaire) des flux d'évapotranspiration et d'énergie.
- **`point_c_gmia_and_diff_in_diff.py` :** Analyse en double différence (*Difference-in-Differences*) sur les zones irriguées répertoriées dans la base GMIA (*Global Map of Irrigation Areas*) pour quantifier l'impact de l'irrigation non modélisée dans Noah-MP.
- **`point_c_truncation_analysis.py` & `audit_innovations.py` :** Examen des bornes physiques d'innovation et de l'asymétrie statistique des incréments EnKF.

### D. Bilans de masse et validation indépendante
- **`reproduce_aud05_water_balance.py` :** Reproduction déterministe des calculs de bilan hydrique cumulé en couche de surface ($0\text{--}10\text{ cm}$).
- **`complements_water_balance_and_validation.py` & `calc_section4_validation.py` :** Diagnostics complémentaires de validation face aux précipitations et références externes.

### E. Traçabilité des métriques figées
- **`export_nocdf_native_rf_metrics.py` :** Script déterministe officiel qui lit les artefacts Random Forest scellés pour DA-NoCDF natif (Holdout 2020), recalcule les métriques d'erreur et génère la table [`tables/audit/nocdf_native_rf_2020_metrics.csv`](../../tables/audit/nocdf_native_rf_2020_metrics.csv) ainsi que la figure associée.

---

## 3. Guide d'exécution type

Chaque script d'audit est autonome et peut être exécuté en ligne de commande :

```bash
# Exemple : Exporter les métriques vérifiées NoCDF natif 2020
python scripts/audits/export_nocdf_native_rf_metrics.py

# Exemple : Vérifier les bornes géographiques des CDF LIS
python scripts/audits/check_cdf_domain.py
```

---

## 4. Statut et références internes

- Les résultats d'audit ayant conduit à l'invalidation de l'ancienne simulation DA-CDF sont consignés dans [`docs/invalidated_legacy_cdf_results.md`](../../docs/invalidated_legacy_cdf_results.md).
- Les métriques officielles vérifiées pour DA-NoCDF natif sont documentées dans [`docs/nocdf_native_rf_results.md`](../../docs/nocdf_native_rf_results.md).
