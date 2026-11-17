#!/usr/bin/env python
import pandas as pd
import json

dir_path = 'data/processed/modeling/xai/outputs/value/'
df = pd.read_csv(dir_path + 'tidy_predictor_summary.csv')

print('=== Top-10 CDF ===')
print(df[df['experiment'] == 'da_cdf'].head(10)[['feature', 'mean_abs_shap']])

print('\n=== Top-10 NoCDF ===')
print(df[df['experiment'] == 'da_nocdf'].head(10)[['feature', 'mean_abs_shap']])

g = pd.read_csv(dir_path + 'cdf_nocdf_group_detail.csv')
print('\n=== Grouped Importance CDF ===')
for _, r in g.iterrows(): 
    print(f"{r['group']:<40} {r['cdf']:.4f}")

print('\n=== Grouped Importance NoCDF ===')
for _, r in g.iterrows(): 
    print(f"{r['group']:<40} {r['nocdf']:.4f}")

print('\n=== DJF / JJA (CDF) ===')
d_c = pd.read_csv(dir_path + 'seasonal_djf_group_da_cdf.csv')
j_c = pd.read_csv(dir_path + 'seasonal_jja_group_da_cdf.csv')
print(f"CDF DJF top group: {d_c.iloc[0]['group']} ({d_c.iloc[0]['normalized_group_importance']:.4f})")
print(f"CDF JJA top group: {j_c.iloc[0]['group']} ({j_c.iloc[0]['normalized_group_importance']:.4f})")

print('\n=== Spatial Stability (CDF) ===')
s = pd.read_csv(dir_path + 'spatial_stability_da_cdf.csv')
print(s.head(3))

print('\n=== Dependence Predictors ===')
with open(dir_path + 'dependence_features.json', 'r') as f:
    print(json.load(f))
