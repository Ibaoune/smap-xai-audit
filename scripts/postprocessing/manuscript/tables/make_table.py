import pandas as pd
from io import StringIO
import sys

csv_data = """baseflow_opl_lag1,Antecedent OPL Baseflow (t-1),Antecedent fluxes,lag 1 day,No,Yes,Yes,Yes,Yes,Yes,Yes
day_of_year,Day of year,Temporal context,temporal/calendar,Yes,Yes,Yes,Yes,Yes,Yes,Yes
days_since_finite_innovation_7d,Days since finite innovation (7 d),Assimilation history,temporal/calendar,No,Yes,Yes,Yes,Yes,No,No
delta_precip_forcing_pre3d_sum,Precipitation discrepancy (previous 3 d),Forcing-discrepancy controls,previous 3-day window,No,Yes,Yes,Yes,Yes,Yes,Yes
delta_precip_forcing_pre7d_sum,Precipitation discrepancy (previous 7 d),Forcing-discrepancy controls,previous 7-day window,No,Yes,Yes,Yes,Yes,Yes,Yes
delta_precip_forcing_t,Precipitation discrepancy (t),Forcing-discrepancy controls,same day t,No,Yes,Yes,Yes,Yes,Yes,Yes
doy_cos,DOY cosine,Temporal context,temporal/calendar,Yes,Yes,Yes,Yes,Yes,Yes,Yes
doy_sin,DOY sine,Temporal context,temporal/calendar,Yes,Yes,Yes,Yes,Yes,Yes,Yes
elevation,Elevation,Topography,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
et_opl_lag1,Antecedent OPL ET (t-1),Antecedent fluxes,lag 1 day,No,Yes,Yes,Yes,Yes,Yes,Yes
finite_innovation_count_pre3d,Finite innovation count (previous 3 d),Assimilation history,previous 3-day window,No,Yes,Yes,Yes,Yes,No,No
finite_innovation_count_pre7d,Finite innovation count (previous 7 d),Assimilation history,previous 7-day window,No,Yes,Yes,Yes,Yes,No,No
finite_innovation_fraction_pre3d_mean,Mean finite innovation fraction (previous 3 d),Assimilation history,previous 3-day window,No,No,No,No,No,Yes,Yes
finite_innovation_fraction_pre7d_mean,Mean finite innovation fraction (previous 7 d),Assimilation history,previous 7-day window,No,No,No,No,No,Yes,Yes
finite_innovation_fraction_t,Finite innovation fraction (t),Assimilation history,same day t,No,No,No,No,No,Yes,Yes
land_cover_fraction_1,Land-cover fraction 1,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_10,Land-cover fraction 10,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_11,Land-cover fraction 11,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_12,Land-cover fraction 12,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_13,Land-cover fraction 13,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_14,Land-cover fraction 14,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_16,Land-cover fraction 16,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_2,Land-cover fraction 2,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_3,Land-cover fraction 3,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_4,Land-cover fraction 4,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_5,Land-cover fraction 5,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_6,Land-cover fraction 6,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_7,Land-cover fraction 7,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_8,Land-cover fraction 8,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
land_cover_fraction_9,Land-cover fraction 9,Land cover,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
month,Month,Temporal context,temporal/calendar,Yes,Yes,Yes,Yes,Yes,Yes,Yes
observation_frequency,Observation frequency,Assimilation history,static,No,Yes,Yes,Yes,Yes,No,No
precip_lag1,Precipitation (t−1),Meteorological forcing,lag 1 day,Yes,Yes,Yes,Yes,Yes,Yes,Yes
precip_pre3d_sum,Precipitation (previous 3 d),Meteorological forcing,previous 3-day window,Yes,Yes,Yes,Yes,Yes,Yes,Yes
precip_pre7d_sum,Precipitation (previous 7 d),Meteorological forcing,previous 7-day window,Yes,Yes,Yes,Yes,Yes,Yes,Yes
precip_t,Precipitation (t),Meteorological forcing,same day t,No,Yes,Yes,Yes,Yes,Yes,Yes
rzsm_lag1,Antecedent RZSM (t−1),Antecedent soil moisture,lag 1 day,Yes,No,No,No,No,No,No
rzsm_opl_lag1,Antecedent OPL RZSM (t-1),Antecedent soil moisture,lag 1 day,No,Yes,Yes,Yes,Yes,Yes,Yes
soil_texture_fraction_1,Soil-texture fraction 1,Soil properties,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
soil_texture_fraction_12,Soil-texture fraction 12,Soil properties,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
soil_texture_fraction_3,Soil-texture fraction 3,Soil properties,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
soil_texture_fraction_4,Soil-texture fraction 4,Soil properties,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
soil_texture_fraction_6,Soil-texture fraction 6,Soil properties,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
soil_texture_fraction_7,Soil-texture fraction 7,Soil properties,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
soil_texture_fraction_9,Soil-texture fraction 9,Soil properties,static,Yes,Yes,Yes,Yes,Yes,Yes,Yes
source_absolute_increment_pre3d_sum,Absolute DA increment (previous 3 d),Assimilation history,previous 3-day window,No,Yes,Yes,Yes,Yes,Yes,Yes
source_absolute_increment_pre7d_sum,Absolute DA increment (previous 7 d),Assimilation history,previous 7-day window,No,Yes,Yes,Yes,Yes,Yes,Yes
source_absolute_increment_t,Absolute DA increment (t),Assimilation history,same day t,No,No,No,No,No,Yes,Yes
source_signed_increment_pre3d_sum,Signed DA increment (previous 3 d),Assimilation history,previous 3-day window,No,Yes,Yes,Yes,Yes,Yes,Yes
source_signed_increment_pre7d_sum,Signed DA increment (previous 7 d),Assimilation history,previous 7-day window,No,Yes,Yes,Yes,Yes,Yes,Yes
source_signed_increment_t,Signed DA increment (t),Assimilation history,same day t,No,Yes,Yes,Yes,Yes,Yes,Yes
ssm_lag1,Antecedent SSM (t−1),Antecedent soil moisture,lag 1 day,Yes,No,No,No,No,No,No
ssm_opl_lag1,Antecedent OPL SSM (t-1),Antecedent soil moisture,lag 1 day,No,Yes,Yes,Yes,Yes,Yes,Yes
surface_runoff_opl_lag1,Antecedent OPL surface runoff (t-1),Antecedent fluxes,lag 1 day,No,Yes,Yes,Yes,Yes,Yes,Yes
tair_lag1,Air temperature (t−1),Meteorological forcing,lag 1 day,Yes,Yes,Yes,Yes,Yes,Yes,Yes
tair_pre3d_mean,Air temperature (previous 3 d),Meteorological forcing,previous 3-day window,Yes,Yes,Yes,Yes,Yes,Yes,Yes
tair_pre7d_mean,Air temperature (previous 7 d),Meteorological forcing,previous 7-day window,Yes,Yes,Yes,Yes,Yes,Yes,Yes
tair_t,Air temperature (t),Meteorological forcing,same day t,No,Yes,Yes,Yes,Yes,Yes,Yes
"""

def get_role(row):
    lbl = row["Publication Label"].lower()
    if "fraction" in lbl and "land" in lbl: return "Grid cell land-cover composition"
    if "fraction" in lbl and "soil" in lbl: return "Grid cell soil-texture composition"
    if "precip" in lbl and "discrepancy" in lbl: return "Captures mismatch between forcing and actual precip"
    if "precip" in lbl: return "Meteorological water input"
    if "tair" in lbl or "air temperature" in lbl: return "Atmospheric thermal state"
    if "doy" in lbl or "month" in lbl or "day" in lbl: return "Seasonal/climatological timing"
    if "elevation" in lbl: return "Topographic height"
    if "increment" in lbl: return "Historical magnitude/sign of soil moisture correction"
    if "innovation" in lbl: return "Availability/frequency of assimilation corrections"
    if "rzsm" in lbl: return "Root-zone soil moisture state"
    if "ssm" in lbl: return "Surface soil moisture state"
    if "baseflow" in lbl: return "Baseflow flux state"
    if "et" in lbl: return "Evapotranspiration flux state"
    if "runoff" in lbl: return "Surface runoff flux state"
    return "Physical property or state"

df = pd.read_csv(StringIO("Repository Name,Publication Label,Group,Temporal Definition,SOURCE,TRANSFER_rzsm,TRANSFER_et,TRANSFER_sr,TRANSFER_bf,VALUE_CDF,VALUE_NoCDF\n" + csv_data.strip()))
df["Role"] = df.apply(get_role, axis=1)

# All TRANSFER the same?
df["TRANSFER"] = df.apply(lambda r: "Yes" if (r["TRANSFER_rzsm"]=="Yes" and r["TRANSFER_et"]=="Yes" and r["TRANSFER_sr"]=="Yes" and r["TRANSFER_bf"]=="Yes") else "No", axis=1)
# All VALUE the same?
df["VALUE"] = df.apply(lambda r: "Yes" if (r["VALUE_CDF"]=="Yes" and r["VALUE_NoCDF"]=="Yes") else "No", axis=1)

final_df = df[["Repository Name", "Publication Label", "Group", "Temporal Definition", "SOURCE", "TRANSFER", "VALUE", "Role"]]

print(final_df.to_csv(index=False))
print("\n")
print(final_df.to_markdown(index=False))

