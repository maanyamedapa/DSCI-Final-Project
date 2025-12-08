#src/load.py
import pandas as pd
import geopandas as gpd
from pathlib import Path
import requests
import warnings
from .config import (
    CALENVIROSCREEN_FILE, BIKEWAYS_FILE, TRACTS_FILE, 
    ACS_BASE_URL, PROJECT_ROOT
)

    #suppress user warnings for clean output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def get_processed_dir():
    """Ensures the processed data directory exists before saving."""
    out = PROJECT_ROOT / "data" / "processed"
    out.mkdir(parents=True, exist_ok=True)
    return out
#--------------------------------------------------------------------------------------------------------------------------------------------#
# DATA LOADING MODULE
# Handles fetching, cleaning, and spatial projection of all raw datasets
#--------------------------------------------------------------------------------------------------------------------------------------------#

def load_census_tracts():
    """
    Loads the geographic boundaries polygons for Los Angeles Census Tracts
    We need these shapes to visualize data and calculate the area of each neighborhood
    """
    print("Loading Census Tracts...")
    try:
        gdf = gpd.read_file(TRACTS_FILE)
    except Exception as e:
        print(f"Error loading GeoJSON for tracts: {e}")
        return gpd.GeoDataFrame(pd.DataFrame(columns=["GEOID", "GEOMETRY", "tract_area_sq_mi"]))

    # Standardize Column Names to avoid errors
    gdf.columns = gdf.columns.str.upper()
    
    # Set Geometry to upper case only
    if 'GEOMETRY' not in gdf.columns and 'geometry' in gdf.columns:
         gdf = gdf.rename_geometry('GEOMETRY')
    gdf = gdf.set_geometry("GEOMETRY")

    # Find GEOID Column
    geoid_col = None
    if 'CT20' in gdf.columns: geoid_col = 'CT20'
    elif 'GEOID' in gdf.columns: geoid_col = 'GEOID'
    elif 'GEOID10' in gdf.columns: geoid_col = 'GEOID10'
    else: 
        candidates = [c for c in gdf.columns if 'GEOID' in c]
        if candidates: geoid_col = candidates[0]
        else: raise KeyError(f"Could not find tract ID. Found: {list(gdf.columns)}")

    #Tract identifier (GEOID) often has different names in different files, so standardize GEOID to 11 chars (06037...)
    gdf['tract_suffix'] = gdf[geoid_col].astype(str).str.split('.').str[0].str.zfill(6)
    # Ensure we don't double-add the prefix if it exists
    gdf["GEOID"] = gdf['tract_suffix'].apply(lambda x: x if x.startswith('06037') else '06037' + x)
    
    #Fix Geometry (Valid for Polygons)
    gdf['GEOMETRY'] = gdf['GEOMETRY'].buffer(0)
    
    # Reproject to CA Albers, So we can calculate square miles accurately, Latitude/Longitude degrees are not consistent units for area calculations
    if gdf.crs != "EPSG:3310":
        gdf = gdf.to_crs("EPSG:3310")
        
    #Calculate Area in Sq Miles
    gdf['tract_area_sq_mi'] = gdf.area * 3.86102e-7
    
    print(f"Loaded {len(gdf)} census tracts.")
    return gdf[['GEOID', 'GEOMETRY', 'tract_area_sq_mi']]

#Load CalEnviroScreen dataset, provides our dependent variable (CES Score) and environmental health metrics.
def load_calenviroscreen():
    print("Loading CalEnviroScreen Data...")
    f = CALENVIROSCREEN_FILE
    df = None

    try:
        if Path(f).name == "CalEnviroScreenData.xlsx":
             f_name = "CalEnviroScreenData.xlsx"
             f = f.parent / f_name   
        df = pd.read_csv(f)
        if "Census Tract" not in df.columns:
            df = pd.read_csv(f, skiprows=1)
    except Exception:
        print(f"Reading {f.name} as Excel...")
        try:
            xl = pd.ExcelFile(f)
            found_sheet = False
            for sheet in xl.sheet_names:
                temp_df = pd.read_excel(f, sheet_name=sheet, nrows=5)
                if "Census Tract" in temp_df.columns:
                    df = pd.read_excel(f, sheet_name=sheet)
                    found_sheet = True
                    break
                temp_df_skip = pd.read_excel(f, sheet_name=sheet, skiprows=1, nrows=5)
                if "Census Tract" in temp_df_skip.columns:
                    df = pd.read_excel(f, sheet_name=sheet, skiprows=1)
                    found_sheet = True
                    break
            if not found_sheet: return pd.DataFrame()
        except Exception as e:
            print(f"Error reading CES data: {e}")
            return pd.DataFrame()

    if 'California County' in df.columns:
        df = df[df['California County'] == 'Los Angeles'].copy()

#Rename variables, ces_score: The composite pollution burden score, pm25: Particulate matter concentration      
    df.columns = df.columns.str.strip()
    rename_map = {
        "Census Tract": "GEOID", "CES 4.0 Score": "ces_score", 
        "PM2.5": "pm25", "CES 4.0 Percentile Range": "ces_percentile_range",     
    }
    df = df.rename(columns=rename_map)
#clean the GEOID column to ensure it matches the Census Tracts file
    df['GEOID'] = df['GEOID'].astype(str).str.split('.').str[0]
    df['GEOID'] = df['GEOID'].apply(lambda x: '0' + x if len(x) == 10 else x)
    df = df[df['GEOID'].str.startswith('06037')]

    cols = ["ces_score", "pm25"] 
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    final_cols = ["GEOID"] + [c for c in cols if c in df.columns]
    if "ces_percentile_range" in df.columns: final_cols.append("ces_percentile_range")
        
    print(f"Loaded CES data for {len(df)} tracts.")
    return df[final_cols]

def load_bikeways():
    """
    Loads the LA County Bikeways shapefile and performs a spatial intersection
    The Bikeways file is organized by 'Segment' ID, on a county level not by 'Census Tract' ID 
    To assign bike lanes to tracts, we must physically overlay the lines onto
    the tract polygons and split them at the boundaries.
    """
    print("Loading Bikeways Shapefile...")
    try:
        bike_gdf = gpd.read_file(BIKEWAYS_FILE)
    except Exception as e:
        print(f"Error loading bikeways Shapefile: {e}")
        return pd.DataFrame(columns=["GEOID", "bikeway_miles"])
    
    tracts = load_census_tracts()
    if tracts.empty: return pd.DataFrame(columns=["GEOID", "bikeway_miles"])

# Ensure both files share the same projection before intersecting
    if bike_gdf.crs is None:
        print("Warning: Bikeways Shapefile has no CRS. (Lat/Lon).")
        bike_gdf.set_crs(epsg=4326, inplace=True)
    
    print(f"Bikeways CRS: {bike_gdf.crs}")

# Reproject both to CA Albers
    if bike_gdf.crs != "EPSG:3310": 
        bike_gdf = bike_gdf.to_crs("EPSG:3310")
    if tracts.crs != "EPSG:3310": 
        tracts = tracts.to_crs("EPSG:3310")
        
# --- DO NOT BUFFER LINES ---
    # Buffering (0) on lines can sometimes make them disappear or become invalid polygons.
    # We only buffer the TRACTS (Polygons).
    tracts['GEOMETRY'] = tracts['GEOMETRY'].buffer(0)
    
    print("Performing Spatial Overlay (Intersection)...")
    try:
# We rename to 'geometry' because overlay expects matching active geometry columns usually
        tracts_renamed = tracts.rename_geometry('geometry')
        
# Calculate Intersection
        joined = gpd.overlay(
            bike_gdf[['geometry']], 
            tracts_renamed[['GEOID', 'geometry']], 
            how='intersection', 
            keep_geom_type=False # Allow it to split lines
        )
    except Exception as e:
        print(f"Spatial Overlay failed: {e}")
        joined = gpd.GeoDataFrame()

    if joined.empty:
        print("Warning: Exact spatial intersection returned 0 matches.")
        print("Attempting 'Centroid' fallback (Less accurate, but saves the run)...")
        
        bike_centroids = bike_gdf.copy()
        bike_centroids['geometry'] = bike_centroids.geometry.centroid
        
        joined = gpd.sjoin(
            bike_centroids, 
            tracts.rename_geometry('geometry')[['GEOID', 'geometry']], 
            predicate='within'
        )
        
        if joined.empty:
             print("CRITICAL ERROR: No bike lanes overlapped with tracts. Check your Input Data CRS.")
             all_tracts = tracts[['GEOID']].drop_duplicates()
             all_tracts['bikeway_miles'] = 0.0
             return all_tracts
        
# Use original length for fallback
        joined['length_m'] = bike_gdf.loc[joined.index].geometry.length
    else:
# Calculate length of the CUT pieces
        joined['length_m'] = joined.geometry.length

# Convert Meters to Miles
    joined['bikeway_miles'] = joined['length_m'] * 0.000621371
    
# Aggregate
    aggregated = joined.groupby("GEOID", as_index=False)["bikeway_miles"].sum()
    
# Merge back to ALL tracts to ensure 0s are present for tracts with no bikes
    all_tracts = tracts[['GEOID']].drop_duplicates()
    final_df = all_tracts.merge(aggregated, on='GEOID', how='left').fillna({'bikeway_miles': 0})
    
    print(f"Total LA Bike Miles Calculated: {final_df['bikeway_miles'].sum():.2f}")
    return final_df

def fetch_acs_los_angeles():
    """
    Fetches demographic data from the US Census API.
    
    Variables fetched:
    - B19013_001E: Median Household Income
    - B01001_001E: Total Population
    - B08201_002E: Households with NO vehicle available
    """
    print("Fetching ACS Data...")
    v = ["B19013_001E", "B01001_001E", "B08201_002E","B08201_001E"]
    url = (f"{ACS_BASE_URL}?get=NAME,{','.join(v)}&for=tract:*&in=state:06+county:037")
    
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()
    except Exception:
        backup = get_processed_dir() / "acs_la_tracts.csv"
        if backup.exists():
            print("Loading local ACS backup.")
            return pd.read_csv(backup)
        print("Warning: API failed and no backup found.")
        return pd.DataFrame(columns=["GEOID", "median_income", "population", "households_no_vehicle", "total_households"])

    cols = ["NAME", "median_income", "population", "households_no_vehicle", "total_households", "state", "county", "tract"]
    df = pd.DataFrame(data[1:], columns=cols)
    df["GEOID"] = df["state"] + df["county"] + df["tract"]
    
    df = df[["GEOID", "median_income", "population", "households_no_vehicle", "total_households"]]
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

def save_acs(df, name="acs_la_tracts.csv"):
    path = get_processed_dir() / name
    df.to_csv(path, index=False)
    return path
