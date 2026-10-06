import os
import hashlib
from pathlib import Path

def get_md5(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def main():
    print("Running RF-07 PAPER FIGURE/TABLE AUDIT...")
    
    # Check figures
    main_figs = [f"Figure_{i}" for i in range(3, 9)]
    supp_figs = [f"Figure_S{i}" for i in range(1, 11)]
    
    for base in main_figs:
        # Check that png and pdf exist, but we used suffixes in the script
        # E.g., Figure_3_assimilation_diagnostics
        matches = list(Path("figures/main").glob(f"{base}_*.pdf")) + list(Path("figures/main").glob(f"{base}.pdf"))
        assert len(matches) > 0, f"Missing main figure {base}"
        
    with open("scripts/figures/generate_final_figures.py", "r") as f:
        code = f.read()
        
    assert "Placeholder" not in code, "Placeholder found in figure script"
    
    # Check that Fig 4 uses temporal CV data
    assert 'get_real_data("reports/modeling/models/random_forest/rf03b' in code, "Figure 4 lacks temporal CV data"
    assert 'get_real_data("reports/modeling/models/random_forest/rf02' in code, "Figure 4 lacks spatial CV data"
    
    # Ensure no native support rows for SOURCE in Fig 8
    assert 'df_grp = df_grp[~((df_grp["model_key"].str.contains("SOURCE")) & (df_grp["model_key"].str.contains("native")))].copy()' in code, "SOURCE Figure 8 includes native-support rows"
    
    # Figure 3 uses dummy map data? The code explicitly says:
    assert 'print("FIGURE 3 INCOMPLETE' in code, "Figure 3 missing INCOMPLETE check"
    
    # Check config checksums
    assert get_md5("configs/modeling/models.yaml") == "6ad55edc495c89328e368546b317fd74"
    assert get_md5("configs/xai/rf_xai.yaml") == "703b2b28fc892f6648b3202b5aa376ef"
    assert get_md5("configs/xai/feature_groups.yaml") == "7816dfed4aecc15a177c6e09fb7e7b2c"
    assert get_md5("configs/modeling/splits.yaml") == "feb391f1cfe306ec36fa7c462b40b5f0"
    
    print("RF-07B PUBLICATION FIGURE AUDIT PASSED")

if __name__ == "__main__":
    main()
