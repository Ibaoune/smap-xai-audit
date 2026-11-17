#!/usr/bin/env python3
import os
import glob
import zipfile
import tempfile
import numpy as np
import netCDF4 as nc
from scipy.interpolate import RegularGridInterpolator

LIS_INPUT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/lis_input/lis_input_NorthMor_5km.nc"
BASE_CTRL = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/experiments/NorthMor/matrix_2016_2020/DA_nocdf_noirr_2016_2020/output"
DIR_ESACCI = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/validation/soil_moisture/ESA_CCI/raw"
DIR_ASCAT = "/home/mohammad.elaabaribao/lustre/empowermed-ahl6xm8o7mg/users/mohammad.elaabaribao/NoahMP_Morocco/data/validation/soil_moisture/ASCAT/raw"

TEXTURE_NAMES = {
    1: "Sand", 2: "Loamy Sand", 3: "Sandy Loam", 4: "Silt Loam", 5: "Silt",
    6: "Loam", 7: "Sandy Clay Loam", 8: "Silty Clay Loam", 9: "Clay Loam",
    10: "Sandy Clay", 11: "Silty Clay", 12: "Clay"
}

with nc.Dataset(LIS_INPUT) as ds:
    landmask = ds.variables["LANDMASK"][:].squeeze().astype(int)
    texture = ds.variables["TEXTURE"][:]
    landcover = ds.variables["LANDCOVER"][:]
    lat = ds.variables["lat"][:]
    lon = ds.variables["lon"][:]
soiltype = np.argmax(texture, axis=0) + 1
vegt = np.argmax(landcover, axis=0) + 1
land_bool = (landmask == 1)
non_forest = land_bool & (vegt > 4)

lat_min, lat_max = lat.min(), lat.max()
lon_min, lon_max = lon.min(), lon.max()

# 1. OL JA 2018
f_sm_c = sorted(glob.glob(f"{BASE_CTRL}/2018-0[78]/SURFACEMODEL/20180[78]/LIS_HIST_*.nc"))
ol_sum = np.zeros((121, 181), dtype=float)
for fc in f_sm_c:
    with nc.Dataset(fc) as ds:
        ol_sum += ds.variables["SoilMoist_tavg"][0, :, :].squeeze()
ol_ja = ol_sum / len(f_sm_c)

# 2. SMAP brut JA 2018
def read_daobs(fpath):
    with open(fpath, "rb") as f:
        _ = np.fromfile(f, dtype=">i4", count=1)
        rec1 = np.fromfile(f, dtype=">f4", count=21901)
        _ = np.fromfile(f, dtype=">i4", count=2)
        rec2 = np.fromfile(f, dtype=">f4", count=21901)
    return rec1.reshape(121, 181), rec2.reshape(121, 181)

f_daobs = sorted(glob.glob(f"{BASE_CTRL}/2018-0[78]/DAOBS/20180[78]/LISDAOBS_*.1gs4r"))
smap_sum = np.zeros((121, 181), dtype=float)
smap_cnt = np.zeros((121, 181), dtype=int)
for f in f_daobs:
    r1, _ = read_daobs(f)
    v = (r1 != -9999.0) & np.isfinite(r1) & land_bool
    smap_sum[v] += r1[v]
    smap_cnt[v] += 1
smap_ja = np.full((121, 181), np.nan)
v_smap = smap_cnt >= 10
smap_ja[v_smap] = smap_sum[v_smap] / smap_cnt[v_smap]

# 3. ESA CCI Combined JA 2018
f_esacci = sorted(glob.glob(f"{DIR_ESACCI}/ESACCI-SOILMOISTURE-*-20180[78]*.nc"))
esacci_sum = np.zeros((121, 181), dtype=float)
esacci_cnt = np.zeros((121, 181), dtype=int)

if f_esacci:
    with nc.Dataset(f_esacci[0]) as ds0:
        cci_lat = ds0.variables['lat'][:]
        cci_lon = ds0.variables['lon'][:]
    r_box = np.where((cci_lat >= lat_min - 0.2) & (cci_lat <= lat_max + 0.2))[0]
    c_box = np.where((cci_lon >= lon_min - 0.2) & (cci_lon <= lon_max + 0.2))[0]
    sub_lat = cci_lat[r_box]
    sub_lon = cci_lon[c_box]
    
    for f in f_esacci:
        with nc.Dataset(f) as ds:
            sm = ds.variables['sm'][0, r_box[0]:r_box[-1]+1, c_box[0]:c_box[-1]+1]
            sm_val = np.where((sm >= 0.0) & (sm <= 1.0), sm, np.nan)
        if sub_lat[0] > sub_lat[-1]:
            interp = RegularGridInterpolator((sub_lat[::-1], sub_lon), sm_val[::-1, :], bounds_error=False, fill_value=np.nan)
        else:
            interp = RegularGridInterpolator((sub_lat, sub_lon), sm_val, bounds_error=False, fill_value=np.nan)
        pts = np.stack([lat.ravel(), lon.ravel()], axis=-1)
        sm_5k = interp(pts).reshape(lat.shape)
        v = land_bool & np.isfinite(sm_5k)
        esacci_sum[v] += sm_5k[v]
        esacci_cnt[v] += 1

esacci_ja = np.full((121, 181), np.nan)
v_cci = esacci_cnt >= 5
esacci_ja[v_cci] = esacci_sum[v_cci] / esacci_cnt[v_cci]

# 4. ASCAT SWI JA 2018 (extraire temporairement chaque NetCDF depuis le zip)
f_ascat_zips = sorted(glob.glob(f"{DIR_ASCAT}/c_gls_SWI_20180[78]*_nc"))
ascat_sum = np.zeros((121, 181), dtype=float)
ascat_cnt = np.zeros((121, 181), dtype=int)

print(f"Extraction et traitement de {len(f_ascat_zips)} granules ASCAT...")

with tempfile.TemporaryDirectory() as tmpdir:
    # Récupérer la grille à partir du premier fichier
    first_zip = f_ascat_zips[0]
    with zipfile.ZipFile(first_zip, 'r') as z:
        nc_names = [n for n in z.namelist() if n.endswith('.nc')]
        extracted = z.extract(nc_names[0], path=tmpdir)
        with nc.Dataset(extracted) as ds0:
            a_lat = ds0.variables['lat'][:]
            a_lon = ds0.variables['lon'][:]
            r_box_a = np.where((a_lat >= lat_min - 0.2) & (a_lat <= lat_max + 0.2))[0]
            c_box_a = np.where((a_lon >= lon_min - 0.2) & (a_lon <= lon_max + 0.2))[0]
            sub_lat_a = a_lat[r_box_a]
            sub_lon_a = a_lon[c_box_a]
            
    for fz in f_ascat_zips:
        try:
            with zipfile.ZipFile(fz, 'r') as z:
                nc_names = [n for n in z.namelist() if n.endswith('.nc')]
                if not nc_names: continue
                target_nc = os.path.join(tmpdir, os.path.basename(nc_names[0]))
                with open(target_nc, 'wb') as f_out:
                    f_out.write(z.read(nc_names[0]))
                with nc.Dataset(target_nc) as ds:
                    varname = 'SWI_001' if 'SWI_001' in ds.variables else 'SWI_005'
                    swi = ds.variables[varname][0, r_box_a[0]:r_box_a[-1]+1, c_box_a[0]:c_box_a[-1]+1]
                    swi_val = np.where((swi >= 0.0) & (swi <= 100.0), swi, np.nan)
                os.remove(target_nc)
                
            if sub_lat_a[0] > sub_lat_a[-1]:
                interp_a = RegularGridInterpolator((sub_lat_a[::-1], sub_lon_a), swi_val[::-1, :], bounds_error=False, fill_value=np.nan)
            else:
                interp_a = RegularGridInterpolator((sub_lat_a, sub_lon_a), swi_val, bounds_error=False, fill_value=np.nan)
            pts = np.stack([lat.ravel(), lon.ravel()], axis=-1)
            swi_5k = interp_a(pts).reshape(lat.shape)
            v = land_bool & np.isfinite(swi_5k)
            ascat_sum[v] += swi_5k[v]
            ascat_cnt[v] += 1
        except Exception as e:
            continue

ascat_ja = np.full((121, 181), np.nan)
v_asc = ascat_cnt >= 5
ascat_ja[v_asc] = ascat_sum[v_asc] / ascat_cnt[v_asc]

print("\n==================================================================")
print(" TABLEAU COMPARATIF FINAL : HUMIDITÉ DU SOL PAR TEXTURE (JA 2018)")
print("==================================================================")
print(f"{'Cat':<4} | {'Nom Texture':<16} | {'N px':<6} | {'SMAP brut (m3)':<15} | {'OL couche1 (m3)':<16} | {'ESA CCI (m3)':<15} | {'ASCAT SWI (%)':<15}")
print("-" * 95)

for c in [1, 3, 4, 6, 7, 9, 12]:
    m_c = non_forest & (soiltype == c)
    if np.sum(m_c) == 0: continue
    
    smap_val = np.nanmean(smap_ja[m_c])
    ol_val = np.nanmean(ol_ja[m_c])
    cci_val = np.nanmean(esacci_ja[m_c])
    asc_val = np.nanmean(ascat_ja[m_c])
    name = TEXTURE_NAMES.get(c, "Inconnu")
    print(f"{c:<4} | {name:<16} | {np.sum(m_c):<6} | {smap_val:15.4f} | {ol_val:16.4f} | {cci_val:15.4f} | {asc_val:14.1f}%")

print("-" * 95)
all_smap = np.nanmean(smap_ja[non_forest])
all_ol = np.nanmean(ol_ja[non_forest])
all_cci = np.nanmean(esacci_ja[non_forest])
all_asc = np.nanmean(ascat_ja[non_forest])
print(f"{'ALL':<4} | {'Ensemble':<16} | {np.sum(non_forest):<6} | {all_smap:15.4f} | {all_ol:16.4f} | {all_cci:15.4f} | {all_asc:14.1f}%")
