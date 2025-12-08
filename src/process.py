
# src/process.py
import pandas as pd
from .load import get_processed_dir
import geopandas as gpd

#--------------------------------------------------------------------------------------------------------------------------------------------#
# DATA PROCESSING MODULE
# Contains logic for how we operationalized and computed variables and merged datasets
#--------------------------------------------------------------------------------------------------------------------------------------------#
def add_vehicle_rate(df):
    """
    Calculates the 'Vehicle Rate', which is the percentage of households 
    that do not own a car. 
    
    Significance: This variable serves as a proxy for 'Transit Dependency'.
    High values suggest a population that relies on public transit, walking or biking, higlighting higher need for transit infrastructure 
    """
    #divide by population to normalize the rate across different tract sizes

    r = df.copy()
    if "households_no_vehicle" in r.columns and "population" in r.columns:
        r["vehicle_rate"] = r["households_no_vehicle"] / r["population"].replace(0, pd.NA)
    else:
        r["vehicle_rate"] = pd.NA
    return r

def add_bikeway_per_capita(df):
    """
    Calculates bikeway miles per 1,000 residents.
    This is an 'Equity Metric' - showing how much infrastructure exists relative to the people served.
    """
    r = df.copy()
    if "bikeway_miles" not in r.columns:
        r["bikeway_miles"] = 0.0
    else:
        r["bikeway_miles"] = r["bikeway_miles"].fillna(0.0)
        
    pop = r["population"].replace(0, pd.NA)
    r["bikeway_miles_per_1000"] = (r["bikeway_miles"] / pop) * 1000
    return r

def add_bike_lane_area_density(df):
    """
    Calculates bikeway miles per Square Mile of land area.
    This is an 'Infrastructure Metric'. 
    
    We calculate this as comparing raw miles is unfair. Some tracts are huge (Valley) and some are tiny (downtown).
    Density normalizes the infrastructure availability by the physical size of the neighborhood.
    """
    r = df.copy()
    # 1. Fill NaNs
    if "bikeway_miles" not in r.columns:
        r["bikeway_miles"] = 0.0
    r["bikeway_miles"] = r["bikeway_miles"].fillna(0.0)
    
    # 2. Check Area
    if "tract_area_sq_mi" not in r.columns:
        print("CRITICAL WARNING: 'tract_area_sq_mi' missing. Density will be NA.")
        r["bike_lane_density_sq_mi"] = pd.NA
        return r

    # 3. Calculate
    area_safe = r["tract_area_sq_mi"].replace(0, pd.NA)
    r["bike_lane_density_sq_mi"] = r["bikeway_miles"] / area_safe
    return r

def merge_layers(acs, ces, bike, tracts=None):
    """
    Merges the Demographic (ACS), Environmental (CES), and Infrastructure (Bike)
    dataframes into a single Master DataFrame for analysis.
    
    Join Key: 'GEOID' (11-digit FIPS code)
    """
    print("Merging layers...")
    m = acs.copy()
    # Ensure Master GEOID is string
    m["GEOID"] = m["GEOID"].astype(str)
    
    if not ces.empty: 
        ces["GEOID"] = ces["GEOID"].astype(str)
        m = m.merge(ces, on="GEOID", how="left")
    
    if not bike.empty: 
        # Ensure Bike GEOID is string to match Master, left join ensures we keep all demographic tracts even if they are missing environmental data
        bike["GEOID"] = bike["GEOID"].astype(str)
        m = m.merge(bike, on="GEOID", how="left")
        # Bring in the tract area for density calculations
    if tracts is not None and not tracts.empty:
        if 'tract_area_sq_mi' in tracts.columns:
            tract_area = tracts[['GEOID', 'tract_area_sq_mi']].copy()
            tract_area = tract_area.drop_duplicates(subset=['GEOID'])
            tract_area["GEOID"] = tract_area["GEOID"].astype(str)
            m = m.merge(tract_area, on="GEOID", how="left")

    # Final fill for miles
    if "bikeway_miles" in m.columns:
        m["bikeway_miles"] = m["bikeway_miles"].fillna(0)
    else:
        # If merge failed completely, create column of 0s
        m["bikeway_miles"] = 0.0
        
    return m

def attach_geometry(tracts, df):
    """
    Re-joins the Master DataFrame with the polygon geometries.
    This creates a GeoDataFrame required for generating choropleth maps.
    """
    r = df.copy()
    r["GEOID"] = r["GEOID"].astype(str)
    
    geo_data = tracts[['GEOID', 'GEOMETRY']].copy()
    geo_data = geo_data.drop_duplicates(subset=['GEOID'])
    
    merged_gdf = geo_data.merge(r, on="GEOID", how="inner")
    
    if 'GEOMETRY' in merged_gdf.columns:
        return gpd.GeoDataFrame(merged_gdf, geometry="GEOMETRY", crs=tracts.crs)
    elif 'geometry' in merged_gdf.columns:
        return gpd.GeoDataFrame(merged_gdf, geometry="geometry", crs=tracts.crs)
        
    return merged_gdf

def save_master(df):
    """Saves the final clean dataset."""
    path = get_processed_dir() / "master_analysis_data.csv"
    df.to_csv(path, index=False)
    return path
