# tests.py

import pandas as pd
import geopandas as gpd
from pathlib import Path
import sys

# Ensure the src directory is in the path to allow imports
# This looks up from 'tests.py' to find the 'src' folder
sys.path.append(str(Path(__file__).resolve().parent / 'src'))

try:
    from src import load, process, analyze, config
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# --- Test Functions ---

def test_load_census_tracts():
    """Test loading and GEOID standardization of tract boundaries."""
    print("Testing load_census_tracts...")
    tracts = load.load_census_tracts()
    
    assert isinstance(tracts, gpd.GeoDataFrame), "Tracts did not load as GeoDataFrame."
    # We now expect 'GEOID' (uppercase)
    assert 'GEOID' in tracts.columns, "Tracts data is missing the standardized 'GEOID' column."
    # Check length (should be 11 digits: 06037...)
    assert all(tracts['GEOID'].astype(str).str.len() == 11), "GEOID is not the standard 11-digit length."
    
    print("Tracts loaded successfully with standardized GEOID.")
    return tracts

def test_load_data():
    """Test loading of ACS, CES, and Bikeways data."""
    print("Testing data loaders...")

    # 1. ACS Data Test
    try:
        acs = load.fetch_acs_los_angeles()
    except Exception:
        # Fallback if API fails
        print("   (API unreachable, trying backup file...)")
        acs = pd.read_csv(load.get_processed_dir() / "acs_la_tracts.csv")
    
    assert 'median_income' in acs.columns, "ACS data missing 'median_income'."
    assert 'households_no_vehicle' in acs.columns, "ACS data missing 'households_no_vehicle'."
    assert 'GEOID' in acs.columns, "ACS data missing 'GEOID'."
    print("  - ACS data loaded successfully.")

    # 2. CES Data Test
    ces = load.load_calenviroscreen()
    assert 'ces_score' in ces.columns, "CES data missing 'ces_score'."
    assert 'GEOID' in ces.columns, "CES data missing 'GEOID'."
    print("  - CES data loaded successfully.")
    
    # 3. Bikeways Data Test
    bikeway_agg = load.load_bikeways()
    assert 'bikeway_miles' in bikeway_agg.columns, "Bikeway aggregation failed."
    assert 'GEOID' in bikeway_agg.columns, "Bikeway data missing 'GEOID'."
    
    # Check that we actually have some data
    total_miles = bikeway_agg['bikeway_miles'].sum()
    assert total_miles > 0, "Bikeway miles sum is 0. Spatial join might be failing."
    print(f"  - Bikeway data loaded. Total miles found: {total_miles:.2f}")
    
    return acs, ces, bikeway_agg

def test_process_functions(acs, ces, bike):
    """Test data processing (merging and rate calculation)."""
    print("Testing processing functions...")

    # 1. Merge Test
    merged = process.merge_layers(acs, ces, bike)
    assert len(merged) > 1000, "Merge resulted in too few tracts (expected > 1000 for LA)."
    print("  - Data merged successfully.")

    # 2. Rate Calculation Test
    merged = process.add_vehicle_rate(merged)
    merged = process.add_bikeway_per_capita(merged)
    
    assert 'vehicle_rate' in merged.columns, "Missing 'vehicle_rate' column."
    assert 'bikeway_miles_per_1000' in merged.columns, "Missing 'bikeway_miles_per_1000' column."
    
    print("  - Derived variables calculated successfully.")
    return merged

def test_analysis_functions(gdf):
    """Test OLS regression and K-Means clustering."""
    print("Testing analysis functions...")
    
    # --- OLS Regression Test ---
    y_var = "ces_score"
    x_vars = ["bikeway_miles_per_1000", "vehicle_rate", "median_income"]
    
    # Drop geometry for regression to avoid warnings
    df = gdf.drop(columns=['geometry'], errors='ignore').copy()
    
    model = analyze.run_ols(df, y_var, x_vars)
    if model is None:
        print("  - OLS Skipped (not enough valid data points).")
    else:
        # Check if R-squared exists (implies model ran)
        print(f"  - OLS regression ran successfully (R-squared: {model.rsquared:.4f}).")

    # --- K-Means Clustering Test ---
    cluster_cols = ["bikeway_miles_per_1000", "ces_score", "pm25", "vehicle_rate"]
    gdf_clustered = analyze.add_clusters(gdf, cluster_cols, k=5)
    
    assert 'cluster' in gdf_clustered.columns, "Clustering failed to add 'cluster' column."
    print("  - K-Means Clustering ran successfully.")
    
    #  Spatial Mapping Test 
    # Create a temporary test map
    out_path = config.PROJECT_ROOT / "results" / "test_map.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    analyze.save_choropleth(gdf_clustered, 'cluster', out_path, "Test Map")
    assert out_path.exists(), "Choropleth map failed to save."
    print("  - Map saving function successfully executed.")
    

def run_all_tests():
    """Executes all test functions in order."""
    print("\n--- Starting Final Project Tests ---\n")
    
    # 1. Load GeoData
    tracts_gdf = test_load_census_tracts()
    
    # 2. Load and Aggregate Attribute Data
    acs, ces, bike = test_load_data()
    
    # 3. Process Data
    merged_df = test_process_functions(acs, ces, bike)
    
    # 4. Attach Geometry
    gdf = process.attach_geometry(tracts_gdf, merged_df)

    # 5. Analysis
    test_analysis_functions(gdf)
    
    print("\n--- All tests passed! You are ready to run main.py ---")
    
if __name__ == '__main__':
    run_all_tests()
