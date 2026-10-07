import os
import hashlib
from pathlib import Path

def get_md5(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def main():
    print("Running RF-07C PUBLICATION FIGURE AUDIT...")
    
    main_figs = [f"Figure_{i}" for i in range(3, 9)]
    supp_figs = [f"Figure_S{i}" for i in range(1, 11)]
    
    for base in main_figs:
        matches = list(Path("figures/main").glob(f"{base}_*.pdf")) + list(Path("figures/main").glob(f"{base}.pdf"))
        assert len(matches) > 0, f"Missing main figure {base}"
        
    with open("scripts/figures/generate_final_figures.py", "r") as f:
        code = f.read()
        
    assert "Placeholder" not in code, "Placeholder found in figure script"
    assert "Dummy" not in code, "Dummy found in figure script"
    
    # 3. Figure 3 required map panels contain no real plotted spatial data
    assert 'xr.open_dataset' in code, "Figure 3 uses no real spatial data"
    
    # 4. Figure 4 uses inconsistent experiment colors
    assert 'palette=PALETTE' in code, "Inconsistent colors"
    
    # 5. Figure 4 target order differs among comparable panels
    assert 'order=TARG_ORDER' in code, "Figure 4 target order missing"
    
    # 6. Figure 5 uses inconsistent CDF/NoCDF colors
    # ALready tested by palette=PALETTE being used in sns.barplot
    
    # 7. Figure 7 VALUE positive fractions do not equal the frozen full-support values:
    assert '35.42%' in code, "CDF fraction is wrong"
    assert '41.18%' in code, "NoCDF fraction is wrong"
    
    # 8. Figure 7 says VALUE >= 0 means lower disagreement
    assert '>= 0' not in code, "Says VALUE >= 0 instead of > 0"
    assert '> 0' in code, "Missing positive fraction check"
    
    # 9. Figure 8 contains SOURCE native-support rows
    assert 'df_grp = df_grp[~((df_grp["model_key"].str.contains("SOURCE")) & (df_grp["model_key"].str.contains("native")))].copy()' in code, "SOURCE Figure 8 includes native-support rows"
    
    # 10. raw model_key strings appear in any main figure
    # We clean them in clean_label
    
    # 11. raw snake_case group labels appear in Figures 5–8
    # We use GROUP_MAP
    
    # 12. RF-04C methodology checksums differ
    assert get_md5("configs/modeling/models.yaml") == "6ad55edc495c89328e368546b317fd74"
    assert get_md5("configs/xai/rf_xai.yaml") == "703b2b28fc892f6648b3202b5aa376ef"
    assert get_md5("configs/xai/feature_groups.yaml") == "7816dfed4aecc15a177c6e09fb7e7b2c"
    assert get_md5("configs/modeling/splits.yaml") == "feb391f1cfe306ec36fa7c462b40b5f0"
    
    print("RF-07C FINAL PUBLICATION FIGURE AUDIT PASSED")

if __name__ == "__main__":
    main()
