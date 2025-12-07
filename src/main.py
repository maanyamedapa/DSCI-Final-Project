#src/main.py
from pathlib import Path
from . import load, process, analyze
from .config import PROJECT_ROOT
import pandas as pd 

def main():
    print("--- Starting Analysis Pipeline ---")
    
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# 1. DATA LOADING
# ---------------------------------------------------------
    print("Loading ACS (Demographic Data)...")
    acs = load.fetch_acs_los_angeles()
    acs = process.add_vehicle_rate(acs)
    load.save_acs(acs)

    print("Loading CalEnviroScreen (Environmental Data)...")
    ces = load.load_calenviroscreen()

    print("Loading Census Tract Geometries...")
    tracts = load.load_census_tracts()

    print("Loading Bikeways...")
    bike = load.load_bikeways()
    
# ---------------------------------------------------------
    # 2. DATA MERGING & PROCESSING
# ---------------------------------------------------------
    print("Merging datasets...")
    merged = process.merge_layers(acs, ces, bike, tracts) 
    merged = process.add_bikeway_per_capita(merged)
    merged = process.add_bike_lane_area_density(merged)
    
# ---------------------------------------------------------
    # 3. STATISTICAL REGRESSION
# ---------------------------------------------------------
    print("\n--- Running Statistical Checks ---")
    
    predictors = ["bike_lane_density_sq_mi", "vehicle_rate", "median_income"]
    
    # Check for Multicollinearity (VIF)
    analyze.check_multicollinearity(merged, predictors)
    
    # Generate Correlation Matrix (Will now only show the 3 vars above)
    print("Generating Correlation Matrix...")
    analyze.plot_correlation_matrix(merged, predictors, results_dir / "correlation_matrix.png")

    print("\nRunning Regression (OLS)...")
    # This runs CES Score = Bike Density + Vehicle Rate + Income
    model = analyze.run_ols(
        merged,
        "ces_score",
        predictors 
    )
    
    if model:
        output_file = results_dir / "regression_results.txt"
        with open(output_file, "w") as f:
            f.write(model.summary().as_text())
        print(f"Regression results saved to {output_file}")

# ---------------------------------------------------------
    # 4. K-MEANS CLUSTERING
# ---------------------------------------------------------
    print("\n--- Running K-Means Clustering ---")
    # Clustering variables (Environmental + Transit + Infrastructure)
    # Note: Poverty/Unemployment are NOT included here either
    cluster_cols = ["bikeway_miles_per_1000", "ces_score", "pm25", "vehicle_rate"]
    
    merged = analyze.add_clusters(merged, cluster_cols, k=5)
    
    master_path = process.save_master(merged)
    print(f"Master dataset (with clusters) saved to: {master_path}")

# ---------------------------------------------------------
    # 5. MAPPING
# ---------------------------------------------------------
    print("\nAttaching Geometry for Mapping...")
    gdf = process.attach_geometry(tracts, merged)

    print("Generating Plots...")
    analyze.plot_scatter_relationships(merged, results_dir)
    
    print("Saving Maps...")
    analyze.save_choropleth(gdf, "bike_lane_density_sq_mi", results_dir / "map_bike_density.png", "Bike Lane Density (Miles/Sq Mi)")
    analyze.save_choropleth(gdf, "ces_score", results_dir / "map_ces_score.png", "CalEnviroScreen 4.0 Score")
    analyze.save_cluster_map(gdf, results_dir / "map_neighborhood_clusters.png")
    
    print("--- Pipeline Complete ---")

if __name__ == "__main__":
    main()# src/main.py
from pathlib import Path
from . import load, process, analyze
from .config import PROJECT_ROOT
import pandas as pd 

def main():
    print("--- Starting Analysis Pipeline ---")
    
    # Setup the results directory to store all output maps, plots, and tables
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)





