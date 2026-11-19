#!/usr/bin/env python3
"""
generate_clean_report.py

Génère un README.md 100% propre et dynamique pour diag2018_e6_clean/
Règles strictes :
1. Tableaux seulement, aucune interprétation narrative.
2. Tous les tableaux sont extraits directement des CSVs.
3. Formats Markdown natifs et liens.
"""

import os
import pandas as pd
import numpy as np

REPORT_DIR = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/smap-xai-audit/reports/audits/diag2018_e6_clean"
README_PATH = os.path.join(REPORT_DIR, "README.md")

def df_to_markdown(df):
    headers = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(str(h) for h in headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        row_str = []
        for val in row:
            if pd.isna(val):
                row_str.append("-")
            elif isinstance(val, (float, np.floating)):
                if abs(val) < 1e-4 and val != 0:
                    row_str.append(f"{val:.6f}")
                elif abs(val) < 1:
                    row_str.append(f"{val:.4f}")
                else:
                    row_str.append(f"{val:.2f}")
            elif isinstance(val, (int, np.integer)):
                row_str.append(str(val))
            else:
                row_str.append(str(val))
        lines.append("| " + " | ".join(row_str) + " |")
    return "\n".join(lines)

# Chargement des CSVs
df_e6_monthly  = pd.read_csv(os.path.join(REPORT_DIR, "e6_ensemble_effect_monthly.csv"))
df_e6_trunc    = pd.read_csv(os.path.join(REPORT_DIR, "e6_boundary_truncation_ens_opl.csv"))
df_e6_memtrunc = pd.read_csv(os.path.join(REPORT_DIR, "e6_member_truncation_restarts.csv"))
df_e5_obs      = pd.read_csv(os.path.join(REPORT_DIR, "e5_censorship_obs_count_monthly.csv"))
df_e5_texture  = pd.read_csv(os.path.join(REPORT_DIR, "e5_nowilt_impact_by_texture.csv"))
df_drydown     = pd.read_csv(os.path.join(REPORT_DIR, "ol_hourly_drydown_comparison.csv"))
df_diurnal     = pd.read_csv(os.path.join(REPORT_DIR, "ol_smap_overpass_sampling_bias.csv"))
df_wb_da       = pd.read_csv(os.path.join(REPORT_DIR, "water_balance_da_minus_ens_monthly.csv"))
df_wb_ens      = pd.read_csv(os.path.join(REPORT_DIR, "water_balance_ens_minus_daic_monthly.csv"))
df_wb_internal = pd.read_csv(os.path.join(REPORT_DIR, "internal_water_balance_monthly.csv"))

# Table 1: E6 Monthly
t1 = df_e6_monthly[['month', 'delta_SM1_ENS_OPL', 'delta_SM1_DAnocdf', 'delta_SM1_DAcdf', 'fraction_SM1_explained_nocdf_pct',
                    'Precip_OPL_mm', 'Precip_ENS_mm', 'delta_Precip_ENS_OPL_mm',
                    'delta_ET_ENS_OPL_mm', 'delta_ET_DAnocdf_mm', 'delta_ET_DAcdf_mm']].copy()
t1.columns = ['Mois', 'ΔSM1 (ENS - OPL)', 'ΔSM1 (DAnocdf - OPL)', 'ΔSM1 (DAcdf - OPL)', 'Fraction Ens (%)',
              'P OPL (mm)', 'P ENS (mm)', 'ΔP ENS (mm)',
              'ΔET ENS (mm)', 'ΔET DAnocdf (mm)', 'ΔET DAcdf (mm)']
md_t1 = df_to_markdown(t1)

# Table 2: E6 Truncation per member
t2 = df_e6_memtrunc[df_e6_memtrunc['simulation'] == 'ENS_OPL'][['month', 'layer', 'total_member_tiles', 'pct_below_002', 'pct_above_smcmax', 'pct_below_smcwlt', 'min_smc', 'max_smc']].copy()
t2.columns = ['Mois', 'Couche', 'Nb Tuiles Membres', 'Part ≤ 0.02 (%)', 'Part ≥ SMCMAX (%)', 'Part ≤ SMCWLT (%)', 'Min SMC', 'Max SMC']
md_t2 = df_to_markdown(t2)

# Table 3: E5 Obs Count
t3 = df_e5_obs[['month', 'raw_obs', 'accepted_DA_nocdf', 'accepted_DA_nowilt', 'uncensored_gain', 'uncensored_gain_pct', 'predicted_censored_obs', 'reconciliation_match_pct']].copy()
t3.columns = ['Mois', 'Obs Brutes', 'Obs DA_nocdf', 'Obs DA_nowilt', 'Surplus Obs', 'Hausse (%)', 'Censure Théorique', 'Concordance (%)']
md_t3 = df_to_markdown(t3)

# Table 4a: E5 Texture - Bilan Annuel
t4_ann = df_e5_texture[df_e5_texture['month'] == 'Annuel'][['soil_id', 'texture_name', 'clay_pct', 'smcwlt',
                                                            'delta_SM1_nowilt_minus_nocdf', 'delta_SMcol_nowilt_minus_nocdf',
                                                            'delta_ET_nowilt_minus_nocdf_mm', 'delta_Qsb_nowilt_minus_nocdf_mm',
                                                            'delta_SM1_nowilt_minus_ENS', 'delta_ET_nowilt_minus_ENS_mm',
                                                            'incr1_nowilt', 'incr1_nocdf', 'delta_incr1_nowilt_minus_nocdf']].copy().sort_values('clay_pct')
t4_ann.columns = ['ID', 'Texture', 'Argile (%)', 'SMCWLT',
                  'ΔSM1 (nowilt-nocdf)', 'ΔSMcol (m³/m³)', 'ΔET (mm/an)', 'ΔQsb (mm/an)',
                  'ΔSM1 (nowilt-ENS)', 'ΔET (nowilt-ENS, mm/an)',
                  'Incr1 nowilt', 'Incr1 nocdf', 'ΔIncr1']
md_t4_ann = df_to_markdown(t4_ann)

# Table 4b: E5 Texture - Bilan JJA (Été)
t4_jja = df_e5_texture[df_e5_texture['month'] == 'JJA'][['soil_id', 'texture_name', 'clay_pct', 'smcwlt',
                                                        'delta_SM1_nowilt_minus_nocdf', 'delta_SMcol_nowilt_minus_nocdf',
                                                        'delta_ET_nowilt_minus_nocdf_mm', 'delta_Qsb_nowilt_minus_nocdf_mm',
                                                        'delta_SM1_nowilt_minus_ENS', 'delta_ET_nowilt_minus_ENS_mm',
                                                        'incr1_nowilt', 'incr1_nocdf', 'delta_incr1_nowilt_minus_nocdf']].copy().sort_values('clay_pct')
t4_jja.columns = ['ID', 'Texture', 'Argile (%)', 'SMCWLT',
                  'ΔSM1 (nowilt-nocdf)', 'ΔSMcol (m³/m³)', 'ΔET (mm/saison)', 'ΔQsb (mm/saison)',
                  'ΔSM1 (nowilt-ENS)', 'ΔET (nowilt-ENS, mm/saison)',
                  'Incr1 nowilt', 'Incr1 nocdf', 'ΔIncr1']
md_t4_jja = df_to_markdown(t4_jja)

# Table 5: Drydown OL
t5 = df_drydown[['texture_name', 'clay_pct', 'smcwlt', 'tau_ctrl_median', 'tau_rsf2_median', 'delta_tau_median', 'theta_res_ctrl_median', 'theta_res_rsf2_median', 'P5_ctrl', 'P5_rsf2', 'freq_below_wlt_ctrl_pct', 'freq_below_wlt_rsf2_pct']].copy()
t5.columns = ['Texture', 'Argile (%)', 'SMCWLT', 'τ ctrl (j)', 'τ rsf2 (j)', 'Δτ (j)', 'θres ctrl', 'θres rsf2', 'P5 ctrl', 'P5 rsf2', '≤WLT ctrl (%)', '≤WLT rsf2 (%)']
md_t5 = df_to_markdown(t5)

# Table 6: Diurnal SMAP
t6 = df_diurnal[df_diurnal['season'] == 'MAM'][['texture_name', 'clay_pct', 'bias_06h_mean', 'bias_18h_mean', 'diurnal_amplitude']].copy()
t6.columns = ['Texture', 'Argile (%)', 'Biais 06h UTC (MAM)', 'Biais 18h UTC (MAM)', 'Amplitude Diurne (MAM)']
md_t6 = df_to_markdown(t6)

# Table 7: Water Balance DA_nocdf - ENS_OPL
t7 = df_wb_da[['month', 'P_ENS_mm', 'P_DA_mm', 'delta_P_mm', 'delta_ET_mm', 'delta_Qs_mm', 'delta_Qsb_mm',
               'delta_Stock_ENS_mm', 'delta_Stock_DA_mm', 'delta_delta_Stock_mm', 'flux_balance_diff_mm', 'residue_mm', 'EnKF_increment_mm', 'unaccounted_discrepancy_mm']].copy()
t7.columns = ['Mois', 'P ENS (mm)', 'P DA (mm)', 'ΔP (mm)', 'ΔET (mm)', 'ΔQs (mm)', 'ΔQsb (mm)', 'ΔStock ENS (mm)', 'ΔStock DA (mm)', 'Δ(ΔStock) (mm)', 'Bilan Flux (mm)', 'Résidu (mm)', 'Incrément EnKF (mm)', 'Écart (mm)']
md_t7 = df_to_markdown(t7)

# Table 8: Internal Water Balance Summary (Résidus et Incréments)
t8_sum = df_wb_internal[['month', 'Residu_ENS', 'Residu_DA', 'Incr_EnKF', 'Residu_DA_nowilt', 'Incr_EnKF_nowilt', 'Residu_OL_DAIC']].copy()
t8_sum.columns = ['Mois', 'Résidu ENS (mm)', 'Résidu DA_nocdf (mm)', 'Incr EnKF DA_nocdf (mm)', 'Résidu DA_nowilt (mm)', 'Incr EnKF nowilt (mm)', 'Résidu OL_DAIC (mm)']
md_t8_sum = df_to_markdown(t8_sum)

# Table 8b: Detailed Internal Water Balance for DA_nocdf_nowilt
t8_nowilt = df_wb_internal[['month', 'P_DA_nowilt', 'ET_DA_nowilt', 'Qs_DA_nowilt', 'Qsb_DA_nowilt', 'dStock_DA_nowilt', 'Residu_DA_nowilt', 'Incr_EnKF_nowilt']].copy()
t8_nowilt.columns = ['Mois', 'P nowilt (mm)', 'ET nowilt (mm)', 'Qs nowilt (mm)', 'Qsb nowilt (mm)', 'ΔStock nowilt (mm)', 'Résidu nowilt (mm)', 'Incr EnKF nowilt (mm)']
md_t8_nowilt = df_to_markdown(t8_nowilt)

# Table 9: Water Balance ENS_OPL - OL_DAIC
t9 = df_wb_ens[['month', 'P_ENS_mm', 'P_OL_DAIC_mm', 'delta_P_mm', 'delta_ET_mm', 'delta_Qs_mm', 'delta_Qsb_mm',
                'delta_Stock_ENS_mm', 'delta_Stock_OL_DAIC_mm', 'delta_delta_Stock_mm', 'flux_balance_diff_mm', 'residue_mm']].copy()
t9.columns = ['Mois', 'P ENS (mm)', 'P OL_DAIC (mm)', 'ΔP (mm)', 'ΔET (mm)', 'ΔQs (mm)', 'ΔQsb (mm)', 'ΔStock ENS (mm)', 'ΔStock OL_DAIC (mm)', 'Δ(ΔStock) (mm)', 'Bilan Flux (mm)', 'Résidu (mm)']
md_t9 = df_to_markdown(t9)

content = f"""# Diagnostic et Bilans Hydriques — Année 2018 (Janvier–Décembre)

**Génération** : Automatisée par script (`generate_clean_report.py`).  
**Contenu** : Tableaux de données brutes issues des CSVs d'audit, sans interprétation narrative.

---

## 1. Effet d'Ensemble Mensuel (E6)

{md_t1}

---

## 2. Troncature des Bornes Physiques par Membre (ENS_OPL)

{md_t2}

---

## 3. Censure du Point de Flétrissement (E5)

### 3.1. Comptage des Observations SMAP Acceptées (DA_nocdf vs DA_nocdf_nowilt)

{md_t3}

### 3.2. Impact par Classe Texturale — Bilan Annuel 2018

{md_t4_ann}

### 3.3. Impact par Classe Texturale — Bilan Estival (JJA 2018)

{md_t4_jja}

---

## 4. Séchage et Biais d'Échantillonnage Diurne

### 4.1. Dynamique de Ressuyage (OL_rsf2 vs OL_ctrl)

{md_t5}

### 4.2. Biais Diurne SMAP (Passages 06h / 18h UTC vs Moyenne Journalière - MAM)

{md_t6}

---

## 5. Bilans d'Eau et Conservation des Masses (2018)

### 5.1. Bilan Différentiel DA_nocdf − ENS_OPL

{md_t7}

### 5.2. Bilans Internes par Simulation Seule (Résidus et Incréments EnKF)

{md_t8_sum}

### 5.3. Bilan Interne Détaillé : DA_nocdf_nowilt

{md_t8_nowilt}

### 5.4. Bilan Différentiel ENS_OPL − OL_DAIC (Effet d'Ensemble Pur)

{md_t9}

---

## 6. Liste des Fichiers CSV Sources

1. `internal_water_balance_monthly.csv`
2. `water_balance_da_minus_ens_monthly.csv`
3. `water_balance_ens_minus_daic_monthly.csv`
4. `e5_censorship_obs_count_monthly.csv`
5. `e5_nowilt_impact_by_texture.csv`
6. `e6_ensemble_effect_monthly.csv`
7. `e6_boundary_truncation_ens_opl.csv`
8. `e6_member_truncation_restarts.csv`
9. `ol_hourly_drydown_comparison.csv`
10. `ol_smap_overpass_sampling_bias.csv`
"""

with open(README_PATH, "w") as f:
    f.write(content)

print(f"[SUCCÈS] README régénéré avec succès dans : {README_PATH}")
