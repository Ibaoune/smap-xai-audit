#!/usr/bin/env python3
"""
generate_point_c_reports.py
----------------------------
Génère tous les artefacts pour l'audit Point C (GMIA & Diff-in-Diff) :
1. Sauvegarde de la sortie brute texte
2. CSV détaillés :
   - Écarts SMAP - OL en JA (2016-2020) : toutes obs et QC acceptées
   - Différence de différences (JA - MA) pour 2016-2020 et 2018 par sous-ensemble
3. Tests statistiques non-paramétriques de Mann-Whitney U (classe 0-1% vs autres)
4. Intervalles de confiance bootstrap à 95%
5. Figure de synthèse haute résolution (PNG 300 DPI et PDF)
"""

import os
import sys
import datetime
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Importer les fonctions du script d'audit existant sans le modifier
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from scripts.audits.point_c_gmia_and_diff_in_diff import (
    load_static, load_gmia_36km, compute_season_bias
)

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../reports/audits/point_c_gmia"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

def bootstrap_ci(data, n_boot=10000, ci=95, statistic=np.mean, seed=42):
    """Calcule l'intervalle de confiance bootstrap percentile."""
    if len(data) == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(data), size=(n_boot, len(data)))
    boot_samples = data[indices]
    boot_stats = statistic(boot_samples, axis=1)
    alpha = (100.0 - ci) / 2.0
    low = np.percentile(boot_stats, alpha)
    high = np.percentile(boot_stats, 100.0 - alpha)
    return low, high

def main():
    print(f"[INFO] Initialisation des calculs Point C...")
    landmask, soiltype, vegt, smcwlt_grid, lat, lon = load_static()
    land_bool = (landmask == 1)
    non_forest = land_bool & (vegt > 4)
    
    gmia_5km, gmia_36km = load_gmia_36km(lat, lon, landmask)
    
    classes_36km = [
        ("0–1 %", (gmia_36km >= 0.0) & (gmia_36km <= 1.0)),
        ("1–10 %", (gmia_36km > 1.0) & (gmia_36km <= 10.0)),
        ("10–30 %", (gmia_36km > 10.0) & (gmia_36km <= 30.0)),
        ("> 30 %", (gmia_36km > 30.0)),
    ]
    
    # 1. Calculs JA 2016-2020
    print("[INFO] Calcul des biais JA (2016-2020)...")
    mean_a_ja, mean_b_ja, cnt_a_ja, cnt_b_ja = compute_season_bias([2016, 2017, 2018, 2019, 2020], [7, 8], landmask)
    
    # 2. Calculs MA 2016-2020
    print("[INFO] Calcul des biais MA (2016-2020)...")
    mean_a_ma, mean_b_ma, cnt_a_ma, cnt_b_ma = compute_season_bias([2016, 2017, 2018, 2019, 2020], [3, 4], landmask)
    
    diff_in_diff = mean_a_ja - mean_a_ma
    valid_did = land_bool & np.isfinite(diff_in_diff) & (cnt_a_ja >= 10) & (cnt_a_ma >= 10)
    
    # 3. Calculs 2018
    print("[INFO] Calcul des biais 2018 (JA et MA)...")
    mean_a_ja_18, _, cnt_ja_18, _ = compute_season_bias([2018], [7, 8], landmask)
    mean_a_ma_18, _, cnt_ma_18, _ = compute_season_bias([2018], [3, 4], landmask)
    did_18 = mean_a_ja_18 - mean_a_ma_18
    valid_did_18 = land_bool & np.isfinite(did_18) & (cnt_ja_18 >= 10) & (cnt_ma_18 >= 10)

    # Sauvegarde des grilles au format NPZ
    np.savez_compressed(
        os.path.join(OUTPUT_DIR, "point_c_pixel_distributions.npz"),
        lat=lat, lon=lon, landmask=landmask, vegt=vegt, gmia_36km=gmia_36km,
        mean_a_ja=mean_a_ja, mean_b_ja=mean_b_ja,
        mean_a_ma=mean_a_ma, mean_b_ma=mean_b_ma,
        diff_in_diff_2016_2020=diff_in_diff,
        diff_in_diff_2018=did_18
    )
    print(f"[INFO] Grilles sauvegardées dans point_c_pixel_distributions.npz")

    # -------------------------------------------------------------
    # TABLE 1 : Écarts JA (2016-2020) par classe GMIA
    # -------------------------------------------------------------
    records_bias = []
    for scope_name, scope_mask in [("Non-forêt (vegt > 4)", non_forest), ("Tous pixels terre valides", land_bool)]:
        for c_name, c_mask in classes_36km:
            m = c_mask & scope_mask & np.isfinite(mean_a_ja) & np.isfinite(mean_b_ja)
            n_p = int(np.sum(m))
            if n_p > 0:
                va = mean_a_ja[m]
                vb = mean_b_ja[m]
                ci_a = bootstrap_ci(va, statistic=np.mean)
                ci_b = bootstrap_ci(vb, statistic=np.mean)
                records_bias.append({
                    "domaine": scope_name,
                    "classe_gmia_36km": c_name,
                    "n_pixels": n_p,
                    "smap_ol_toutes_obs_moy": va.mean(),
                    "smap_ol_toutes_obs_ci95_bas": ci_a[0],
                    "smap_ol_toutes_obs_ci95_haut": ci_a[1],
                    "smap_ol_toutes_obs_med": np.median(va),
                    "smap_ol_qc_acc_moy": vb.mean(),
                    "smap_ol_qc_acc_ci95_bas": ci_b[0],
                    "smap_ol_qc_acc_ci95_haut": ci_b[1],
                    "smap_ol_qc_acc_med": np.median(vb),
                    "delta_qc_minus_toutes_moy": vb.mean() - va.mean(),
                })
    df_bias = pd.DataFrame(records_bias)
    df_bias.to_csv(os.path.join(OUTPUT_DIR, "smap_ol_bias_ja_2016_2020.csv"), index=False, float_format="%.5f")
    print("[INFO] smap_ol_bias_ja_2016_2020.csv généré.")

    # -------------------------------------------------------------
    # MASQUES D'OCCUPATION DU SOL
    # -------------------------------------------------------------
    is_crop_pure = (vegt == 12)
    is_crop_all = (vegt == 12) | (vegt == 14)
    is_crop_grass = (vegt == 12) | (vegt == 10)
    is_crop_grass_all = (vegt == 12) | (vegt == 14) | (vegt == 10)

    subsets_2016_2020 = [
        ("CULTURES SEULEMENT (Classe 12)", is_crop_pure),
        ("CULTURES + MOSAÏQUE (Classes 12 + 14)", is_crop_all),
        ("CULTURES + PRAIRIES (Classes 12 + 10)", is_crop_grass),
        ("CULTURES + MOSAÏQUE + PRAIRIES (Classes 12 + 14 + 10)", is_crop_grass_all),
        ("TOUTES OCCUPATIONS NON-FORÊT (vegt > 4)", non_forest),
    ]

    # -------------------------------------------------------------
    # TABLE 2 : Diff-in-Diff 2016-2020
    # -------------------------------------------------------------
    records_did_5yr = []
    for s_name, s_mask in subsets_2016_2020:
        for c_name, c_mask in classes_36km:
            m = valid_did & s_mask & c_mask
            n_p = int(np.sum(m))
            if n_p > 0:
                vals_d = diff_in_diff[m]
                vals_ja = mean_a_ja[m]
                vals_ma = mean_a_ma[m]
                ci_d = bootstrap_ci(vals_d, statistic=np.mean)
                records_did_5yr.append({
                    "sous_ensemble_occupation": s_name,
                    "classe_gmia_36km": c_name,
                    "n_pixels": n_p,
                    "diff_in_diff_moy": vals_d.mean(),
                    "diff_in_diff_ci95_bas": ci_d[0],
                    "diff_in_diff_ci95_haut": ci_d[1],
                    "diff_in_diff_med": np.median(vals_d),
                    "smap_ol_ja_moy": vals_ja.mean(),
                    "smap_ol_ma_moy": vals_ma.mean(),
                })
            else:
                records_did_5yr.append({
                    "sous_ensemble_occupation": s_name,
                    "classe_gmia_36km": c_name,
                    "n_pixels": 0,
                    "diff_in_diff_moy": np.nan,
                    "diff_in_diff_ci95_bas": np.nan,
                    "diff_in_diff_ci95_haut": np.nan,
                    "diff_in_diff_med": np.nan,
                    "smap_ol_ja_moy": np.nan,
                    "smap_ol_ma_moy": np.nan,
                })
    df_did_5yr = pd.DataFrame(records_did_5yr)
    df_did_5yr.to_csv(os.path.join(OUTPUT_DIR, "diff_in_diff_2016_2020.csv"), index=False, float_format="%.5f")
    print("[INFO] diff_in_diff_2016_2020.csv généré.")

    # -------------------------------------------------------------
    # TABLE 3 : Diff-in-Diff 2018
    # -------------------------------------------------------------
    subsets_2018 = [
        ("CULTURES SEULEMENT (Classe 12)", is_crop_pure),
        ("CULTURES + PRAIRIES (Classes 12 + 10)", is_crop_grass),
    ]
    records_did_18 = []
    for s_name, s_mask in subsets_2018:
        for c_name, c_mask in classes_36km:
            m = valid_did_18 & s_mask & c_mask
            n_p = int(np.sum(m))
            if n_p > 0:
                vals_d = did_18[m]
                vals_ja = mean_a_ja_18[m]
                vals_ma = mean_a_ma_18[m]
                ci_d = bootstrap_ci(vals_d, statistic=np.mean)
                records_did_18.append({
                    "sous_ensemble_occupation": s_name,
                    "classe_gmia_36km": c_name,
                    "n_pixels": n_p,
                    "diff_in_diff_moy": vals_d.mean(),
                    "diff_in_diff_ci95_bas": ci_d[0],
                    "diff_in_diff_ci95_haut": ci_d[1],
                    "diff_in_diff_med": np.median(vals_d),
                    "smap_ol_ja_moy": vals_ja.mean(),
                    "smap_ol_ma_moy": vals_ma.mean(),
                })
            else:
                records_did_18.append({
                    "sous_ensemble_occupation": s_name,
                    "classe_gmia_36km": c_name,
                    "n_pixels": 0,
                    "diff_in_diff_moy": np.nan,
                    "diff_in_diff_ci95_bas": np.nan,
                    "diff_in_diff_ci95_haut": np.nan,
                    "diff_in_diff_med": np.nan,
                    "smap_ol_ja_moy": np.nan,
                    "smap_ol_ma_moy": np.nan,
                })
    df_did_18 = pd.DataFrame(records_did_18)
    df_did_18.to_csv(os.path.join(OUTPUT_DIR, "diff_in_diff_2018.csv"), index=False, float_format="%.5f")
    print("[INFO] diff_in_diff_2018.csv généré.")

    # -------------------------------------------------------------
    # TABLE 4 : Tests non-paramétriques de Mann-Whitney U
    # Comparaison de la classe de référence 0-1% avec chaque classe
    # -------------------------------------------------------------
    mw_records = []
    
    # 4.1 Sur Diff-in-Diff 2016-2020
    for s_name, s_mask in subsets_2016_2020:
        # Référence 0-1%
        m_ref = valid_did & s_mask & classes_36km[0][1]
        vals_ref = diff_in_diff[m_ref]
        n_ref = len(vals_ref)
        med_ref = np.median(vals_ref) if n_ref > 0 else np.nan
        
        for c_name, c_mask in classes_36km[1:]:
            m_comp = valid_did & s_mask & c_mask
            vals_comp = diff_in_diff[m_comp]
            n_comp = len(vals_comp)
            med_comp = np.median(vals_comp) if n_comp > 0 else np.nan
            
            if n_ref > 0 and n_comp > 0:
                stat, pval = mannwhitneyu(vals_comp, vals_ref, alternative='two-sided')
                # Effet rank-biserial r = 1 - 2*U / (n1*n2)
                r_rb = 1.0 - (2.0 * stat) / (n_ref * n_comp)
                mw_records.append({
                    "periode": "2016-2020",
                    "variable": "Diff-in-Diff (JA - MA)",
                    "sous_ensemble_occupation": s_name,
                    "classe_reference": "0–1 %",
                    "n_ref": n_ref,
                    "mediane_ref": med_ref,
                    "classe_comparee": c_name,
                    "n_comp": n_comp,
                    "mediane_comp": med_comp,
                    "delta_medianes": med_comp - med_ref,
                    "mann_whitney_u": stat,
                    "p_value": pval,
                    "significatif_p05": pval < 0.05,
                    "significatif_p01": pval < 0.01,
                    "correlation_rang_biserielle": r_rb
                })

    # 4.2 Sur Diff-in-Diff 2018
    for s_name, s_mask in subsets_2018:
        m_ref = valid_did_18 & s_mask & classes_36km[0][1]
        vals_ref = did_18[m_ref]
        n_ref = len(vals_ref)
        med_ref = np.median(vals_ref) if n_ref > 0 else np.nan
        
        for c_name, c_mask in classes_36km[1:]:
            m_comp = valid_did_18 & s_mask & c_mask
            vals_comp = did_18[m_comp]
            n_comp = len(vals_comp)
            med_comp = np.median(vals_comp) if n_comp > 0 else np.nan
            
            if n_ref > 0 and n_comp > 0:
                stat, pval = mannwhitneyu(vals_comp, vals_ref, alternative='two-sided')
                r_rb = 1.0 - (2.0 * stat) / (n_ref * n_comp)
                mw_records.append({
                    "periode": "2018",
                    "variable": "Diff-in-Diff (JA - MA)",
                    "sous_ensemble_occupation": s_name,
                    "classe_reference": "0–1 %",
                    "n_ref": n_ref,
                    "mediane_ref": med_ref,
                    "classe_comparee": c_name,
                    "n_comp": n_comp,
                    "mediane_comp": med_comp,
                    "delta_medianes": med_comp - med_ref,
                    "mann_whitney_u": stat,
                    "p_value": pval,
                    "significatif_p05": pval < 0.05,
                    "significatif_p01": pval < 0.01,
                    "correlation_rang_biserielle": r_rb
                })

    # 4.3 Sur biais brut JA (2016-2020) non-forêt
    m_ref_ja = non_forest & classes_36km[0][1] & np.isfinite(mean_a_ja)
    vals_ref_ja = mean_a_ja[m_ref_ja]
    for c_name, c_mask in classes_36km[1:]:
        m_comp_ja = non_forest & c_mask & np.isfinite(mean_a_ja)
        vals_comp_ja = mean_a_ja[m_comp_ja]
        stat, pval = mannwhitneyu(vals_comp_ja, vals_ref_ja, alternative='two-sided')
        r_rb = 1.0 - (2.0 * stat) / (len(vals_ref_ja) * len(vals_comp_ja))
        mw_records.append({
            "periode": "2016-2020",
            "variable": "Biais JA (SMAP - OL, toutes obs)",
            "sous_ensemble_occupation": "Non-forêt (vegt > 4)",
            "classe_reference": "0–1 %",
            "n_ref": len(vals_ref_ja),
            "mediane_ref": np.median(vals_ref_ja),
            "classe_comparee": c_name,
            "n_comp": len(vals_comp_ja),
            "mediane_comp": np.median(vals_comp_ja),
            "delta_medianes": np.median(vals_comp_ja) - np.median(vals_ref_ja),
            "mann_whitney_u": stat,
            "p_value": pval,
            "significatif_p05": pval < 0.05,
            "significatif_p01": pval < 0.01,
            "correlation_rang_biserielle": r_rb
        })

    df_mw = pd.DataFrame(mw_records)
    df_mw.to_csv(os.path.join(OUTPUT_DIR, "mann_whitney_tests.csv"), index=False, float_format="%.5f")
    print("[INFO] mann_whitney_tests.csv généré.")

    # -------------------------------------------------------------
    # 5. FIGURE DE SYNTHÈSE
    # -------------------------------------------------------------
    print("[INFO] Tracé de la figure haute résolution...")
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharey=True)
    fig.patch.set_facecolor("#FFFFFF")
    
    # Palette soignée
    colors = {
        "0–1 %": "#2b5c8f",
        "1–10 %": "#3690c0",
        "10–30 %": "#df65b0",
        "> 30 %": "#980043"
    }

    # Panel A : 2016-2020
    ax1 = axes[0]
    ax1.set_facecolor("#FAFAFA")
    
    subsets_plot_5yr = [
        ("Cultures seules\n(Classe 12)", is_crop_pure),
        ("Cultures + Prairies\n(Classes 12+10)", is_crop_grass),
        ("Toutes non-forêt\n(vegt > 4)", non_forest),
    ]
    
    x_base = np.arange(len(subsets_plot_5yr)) * 1.5
    bar_width = 0.28
    
    for i, (c_name, c_mask) in enumerate(classes_36km):
        means = []
        ci_err_low = []
        ci_err_high = []
        ns = []
        for s_label, s_mask in subsets_plot_5yr:
            m = valid_did & s_mask & c_mask
            vals = diff_in_diff[m]
            n_p = len(vals)
            ns.append(n_p)
            if n_p > 0:
                mean_val = vals.mean()
                ci_l, ci_h = bootstrap_ci(vals, statistic=np.mean)
                means.append(mean_val)
                ci_err_low.append(mean_val - ci_l)
                ci_err_high.append(ci_h - mean_val)
            else:
                means.append(0.0)
                ci_err_low.append(0.0)
                ci_err_high.append(0.0)
                
        offsets = x_base + (i - 1.5) * bar_width
        bars = ax1.bar(offsets, means, width=bar_width*0.9, color=colors[c_name],
                       label=f"GMIA {c_name}", edgecolor="black", linewidth=0.8, alpha=0.9)
        ax1.errorbar(offsets, means, yerr=[ci_err_low, ci_err_high], fmt='none',
                     ecolor="#1A1A1A", elinewidth=1.2, capsize=3.5, capthick=1.0)
        
        # Annotation N
        for x_pos, m_val, n_val in zip(offsets, means, ns):
            if n_val > 0:
                y_pos = m_val + (0.003 if m_val >= 0 else -0.006)
                ax1.annotate(f"N={n_val}", (x_pos, y_pos),
                             rotation=90, ha='center', va='bottom' if m_val >= 0 else 'top',
                             fontsize=7.5, fontweight='bold', color="#2A2A2A")
                
    ax1.axhline(0, color="gray", linestyle="--", linewidth=1.0)
    ax1.set_xticks(x_base)
    ax1.set_xticklabels([s[0] for s in subsets_plot_5yr], fontsize=10.5, fontweight='semibold')
    ax1.set_ylabel(r"Différence de Différences : $\Delta\Delta$ (JA − MA) [$\mathrm{m^3/m^3}$]", fontsize=11, fontweight='bold')
    ax1.set_title("(a) Période pluriannuelle 2016–2020 (5 ans)", fontsize=12, fontweight='bold', pad=12)
    ax1.legend(title="Fraction irriguée GMIA (~36 km)", frameon=True, facecolor="white", edgecolor="#CCCCCC", fontsize=9.5)
    ax1.set_ylim(-0.02, 0.095)

    # Panel B : 2018
    ax2 = axes[1]
    ax2.set_facecolor("#FAFAFA")
    
    subsets_plot_18 = [
        ("Cultures seules\n(Classe 12)", is_crop_pure),
        ("Cultures + Prairies\n(Classes 12+10)", is_crop_grass),
    ]
    x_base_18 = np.arange(len(subsets_plot_18)) * 1.5
    
    for i, (c_name, c_mask) in enumerate(classes_36km):
        means = []
        ci_err_low = []
        ci_err_high = []
        ns = []
        for s_label, s_mask in subsets_plot_18:
            m = valid_did_18 & s_mask & c_mask
            vals = did_18[m]
            n_p = len(vals)
            ns.append(n_p)
            if n_p > 0:
                mean_val = vals.mean()
                ci_l, ci_h = bootstrap_ci(vals, statistic=np.mean)
                means.append(mean_val)
                ci_err_low.append(mean_val - ci_l)
                ci_err_high.append(ci_h - mean_val)
            else:
                means.append(0.0)
                ci_err_low.append(0.0)
                ci_err_high.append(0.0)
                
        offsets = x_base_18 + (i - 1.5) * bar_width
        bars = ax2.bar(offsets, means, width=bar_width*0.9, color=colors[c_name],
                       label=f"GMIA {c_name}", edgecolor="black", linewidth=0.8, alpha=0.9)
        ax2.errorbar(offsets, means, yerr=[ci_err_low, ci_err_high], fmt='none',
                     ecolor="#1A1A1A", elinewidth=1.2, capsize=3.5, capthick=1.0)
        
        # Annotation N
        for x_pos, m_val, n_val in zip(offsets, means, ns):
            if n_val > 0:
                y_pos = m_val + (0.003 if m_val >= 0 else -0.006)
                ax2.annotate(f"N={n_val}", (x_pos, y_pos),
                             rotation=90, ha='center', va='bottom' if m_val >= 0 else 'top',
                             fontsize=7.5, fontweight='bold', color="#2A2A2A")

    ax2.axhline(0, color="gray", linestyle="--", linewidth=1.0)
    ax2.set_xticks(x_base_18)
    ax2.set_xticklabels([s[0] for s in subsets_plot_18], fontsize=10.5, fontweight='semibold')
    ax2.set_title("(b) Année spécifique 2018 (saison sèche estivale)", fontsize=12, fontweight='bold', pad=12)
    ax2.legend(title="Fraction irriguée GMIA (~36 km)", frameon=True, facecolor="white", edgecolor="#CCCCCC", fontsize=9.5)

    fig.suptitle(r"Audit Point C : Accroissement estival SMAP − OL ($\Delta\Delta$ = JA − MA) selon l'irrigation GMIA",
                 fontsize=14, fontweight='heavy', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    
    fig_png = os.path.join(OUTPUT_DIR, "diff_in_diff_by_gmia_class.png")
    fig_pdf = os.path.join(OUTPUT_DIR, "diff_in_diff_by_gmia_class.pdf")
    plt.savefig(fig_png, dpi=300, bbox_inches="tight")
    plt.savefig(fig_pdf, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Figures enregistrées dans {fig_png} et {fig_pdf}.")

if __name__ == "__main__":
    main()
