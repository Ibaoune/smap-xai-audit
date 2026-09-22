"""
SMAP-XAI: Noah-MP Extraction Utilities

Purpose
-------
Provides core reusable functions for discovering, parsing, and extracting physical 
variables directly from daily Noah-MP LIS_HIST NetCDF output files.

Scientific conventions
----------------------
- LIS_HIST timestamp corresponds to the END of the 24-h averaging interval
- Canonical temporal support is daily (timestamp - 1 day)
- SSM = SoilMoist_tavg layer 1, 0-10 cm
- No regridding/interpolation is performed. Native grids must strictly match.

Inputs
------
Noah-MP LIS_HIST NetCDF files (`LIS_HIST_YYYYMMDD0000.d01.nc`)

Outputs
-------
Standardized in-memory xarray.DataArray and Dataset objects

Author
------
M. El Aabaribaoune (@um6p)
"""

__author__ = "M. El Aabaribaoune (@um6p)"

import os
from datetime import datetime, timedelta
import xarray as xr
import numpy as np
import pandas as pd

def discover_lis_hist_files(experiment_root, year):
    """
    Discover LIS_HIST daily output files for a given canonical year.
    
    Discovery is based on the canonical year (January 1 to December 31).
    Because the filename timestamp represents the end of the averaging interval, 
    the file representing canonical December 31 will bear the timestamp of 
    January 1 of the following year (YYYY+1).
    
    Parameters
    ----------
    experiment_root : str
        The absolute path to the root directory of the Noah-MP experiment.
    year : int
        The canonical year to discover files for.
        
    Returns
    -------
    list of tuple
        A list of (canonical_datetime, expected_file_path) tuples spanning the year.
    """
    files = []
    
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    
    current_date = start_date
    while current_date <= end_date:
        # File timestamp is canonical date + 1 day
        file_date = current_date + timedelta(days=1)
        
        # The top-level month folder is based on the canonical date
        yyyy_mm_dash = current_date.strftime("%Y-%m")
        
        # The inner folders and filename use the file date (timestamp)
        yyyymm = file_date.strftime("%Y%m")
        yyyymmdd = file_date.strftime("%Y%m%d")
        
        expected_path = os.path.join(
            experiment_root, 
            "output", 
            yyyy_mm_dash, 
            "SURFACEMODEL", 
            yyyymm, 
            f"LIS_HIST_{yyyymmdd}0000.d01.nc"
        )
        
        files.append((current_date, expected_path))
        current_date += timedelta(days=1)
        
    return files

def parse_lis_hist_timestamp(filename):
    """
    Parse canonical date from a LIS_HIST filename.
    
    LIS_HIST filename timestamps correspond to the END of the represented 24-h 
    averaging interval. The canonical analysis date is derived by subtracting 
    1 day from the timestamp embedded in the filename.
    
    Parameters
    ----------
    filename : str
        The LIS_HIST filename (e.g. LIS_HIST_201601020000.d01.nc).
        
    Returns
    -------
    datetime
        The canonical date represented by the data (timestamp - 1 day).
    """
    basename = os.path.basename(filename)
    timestamp_str = basename.split('_')[2][:8] # YYYYMMDD
    file_date = datetime.strptime(timestamp_str, "%Y%m%d")
    canonical_date = file_date - timedelta(days=1)
    return canonical_date

def extract_noahmp_variable(filepath, variable_name, layer_idx=None):
    """
    Extract a Noah-MP variable and map spatial dimensions to canonical names.
    
    Variables are extracted strictly as float32. Missing values (_FillValue) 
    are natively converted to NaN by xarray. Spatial dimensions ('north_south', 
    'east_west') are renamed to canonical ('lat', 'lon') to support standard 
    downstream workflows.
    
    Parameters
    ----------
    filepath : str
        The full path to the raw NetCDF source file.
    variable_name : str
        The exact string name of the target variable (e.g. "SoilMoist_tavg").
    layer_idx : int, optional
        The integer index of the layer to slice, if the variable has a vertical profile dimension.
        
    Returns
    -------
    tuple (xarray.DataArray, xarray.Dataset)
        var: The extracted and standardized DataArray layer.
        ds: The fully opened Dataset object for reference mapping.
    """
    ds = xr.open_dataset(filepath, engine='netcdf4')
    var = ds[variable_name]
    
    if layer_idx is not None:
        layer_dim = var.dims[0] # assuming first dim is layer (e.g. SoilMoist_profiles)
        var = var.isel({layer_dim: layer_idx})
        
    # Standardize dimensions to 'lat' and 'lon' if they are north_south, east_west
    if var.dims == ('north_south', 'east_west'):
        var = var.rename({'north_south': 'lat', 'east_west': 'lon'})
        
    return var, ds

def construct_canonical_coords(ds):
    """
    Construct canonical 1-D coordinate arrays from native LIS lat/lon mappings.
    
    Parameters
    ----------
    ds : xarray.Dataset
        The reference dataset containing native latitude and longitude grids.
        
    Returns
    -------
    tuple of numpy.ndarray
        (lat, lon) vectors representing the explicit coordinate positions.
    """
    lat = ds['lat'].values
    lon = ds['lon'].values
    return lat, lon

def validate_grid_consistency(ds, ref_lat, ref_lon):
    """
    Validate that the incoming dataset grid is numerically identical to a known reference.
    
    Consistency is strictly defined as `numpy.allclose` equivalence between the
    source coordinates and the reference coordinates. This acts as a robust 
    protective lock against spatial shifting or truncation over time.
    
    Parameters
    ----------
    ds : xarray.Dataset
        The dataset whose spatial grid must be tested.
    ref_lat : numpy.ndarray
        The known correct latitude vector.
    ref_lon : numpy.ndarray
        The known correct longitude vector.
        
    Returns
    -------
    bool
        True if the grids are numerically identical, False otherwise.
    """
    lat = ds['lat'].values
    lon = ds['lon'].values
    
    if not np.allclose(lat, ref_lat):
        return False
    if not np.allclose(lon, ref_lon):
        return False
        
    return True
