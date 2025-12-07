# src/process.py
import pandas as pd
from .load import get_processed_dir
import geopandas as gpd

def add_vehicle_rate(df):
    """
    Calculates the percentage of households that do not own a vehicle.
    Formula: No_Vehicle_Households / Total_Population (Proxy).
    """
    r = df.copy()
    if "households_no_vehicle" in r.columns and "population" in r.columns:
        r["vehicle_rate"] = r["households_no_vehicle"] / r["population"].replace(0, pd.NA)
    else:
        r["vehicle_rate"] = pd.NA
    return r

def add_bikeway_per_capita(df):
    """
    Calculates bikeway miles per 1,000 residents (Equity Metric).
    """
    r = df.copy()
    # Ensure column exists and fill NaNs (0 miles)
    if "bikeway_miles" not in r.columns:
        r["bikeway_miles"] = 0.0
    else:
        r["bikeway_miles"] = r["bikeway_miles"].fillna(0.0)
        
    # Avoid division by zero for population
    pop = r["population"].replace(0, pd.NA)
    r["bikeway_miles_per_1000"] = (r["bikeway_miles"] / pop) * 1000
    return r

def add_bike_lane_area_density(df):
    """
    Calculates bikeway miles per square mile (Physical Density Metric).
    This is our primary independent variable for the analysis.
    """
    r = df.copy()
    
    # 1. Ensure miles exist
    if "bikeway_miles" not in r.columns:
        r["bikeway_miles"] = 0.0
    r["bikeway_miles"] = r["bikeway_miles"].fillna(0.0)
    
    # 2. Ensure area exists (Critical check)
    if "tract_area_sq_mi" not in r.columns:
        print("CRITICAL WARNING: 'tract_area_sq_mi' missing in dataframe. Density will be NA.")
        r["bike_lane_density_sq_mi"] = pd.NA
        return r

    # 3. Calculate density
    area_safe = r["tract_area_sq_mi"].replace(0, pd.NA)
    r["bike_lane_density_sq_mi"] = r["bikeway_miles"] / area_safe
    
    return r

def merge_layers(acs, ces, bike, tracts=None):
    """
    Merges all separate data layers into a single Master DataFrame based on GEOID.
    CRITICAL: Accepts 'tracts' argument to include the tract area calculation.
    """
    print("Merging layers...")
    m = acs.copy()
    m["GEOID"] = m["GEOID"].astype(str)
    
    # Merge CalEnviroScreen
    if not ces.empty: 
        ces["GEOID"] = ces["GEOID"].astype(str)
        m = m.merge(ces, on="GEOID", how="left")
    
    # Merge Bikeway Miles
    if not bike.empty: 
        bike["GEOID"] = bike["GEOID"].astype(str)
        m = m.merge(bike, on="GEOID", how="left")
    
    # Merge Tract Area (Required for density calculation)
    if tracts is not None and not tracts.empty:
        if 'tract_area_sq_mi' in tracts.columns:
            tract_area = tracts[['GEOID', 'tract_area_sq_mi']].copy()
            tract_area = tract_area.drop_duplicates(subset=['GEOID'])
            tract_area["GEOID"] = tract_area["GEOID"].astype(str)
            m = m.merge(tract_area, on="GEOID", how="left")
        else:
            print("Warning: 'tract_area_sq_mi' not found in tracts GeoDataFrame.")

    # Fill NaN miles with 0 (assuming tracts with no match have 0 bike lanes)
    if "bikeway_miles" in m.columns:
        m["bikeway_miles"] = m["bikeway_miles"].fillna(0)
        
    return m

def attach_geometry(tracts, df):
    """
    Re-attaches geometry to the dataframe for mapping purposes.
    Returns a GeoDataFrame.
    """
    r = df.copy()
    r["GEOID"] = r["GEOID"].astype(str)
    
    geo_data = tracts[['GEOID', 'GEOMETRY']].copy()
    geo_data = geo_data.drop_duplicates(subset=['GEOID'])
    
    # Inner join: Map only what we have data for
    merged_gdf = geo_data.merge(r, on="GEOID", how="inner")
    
    # Handle geometry column naming variations
    if 'GEOMETRY' in merged_gdf.columns:
        return gpd.GeoDataFrame(merged_gdf, geometry="GEOMETRY", crs=tracts.crs)
    elif 'geometry' in merged_gdf.columns:
        return gpd.GeoDataFrame(merged_gdf, geometry="geometry", crs=tracts.crs)
        
    return merged_gdf

def save_master(df):
    """Saves the final master dataframe to CSV."""
    path = get_processed_dir() / "master_analysis_data.csv"
    df.to_csv(path, index=False)
    return path
