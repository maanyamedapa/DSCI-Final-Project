# src/main.py
from pathlib import Path
from . import load, process, analyze
from .config import PROJECT_ROOT
import pandas as pd 

def main():
    print("--- Starting Analysis Pipeline ---")
    
    # Setup the results directory to store all output maps, plots, and tables
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # 1. LOAD DATA
    # ---------------------------------------------------------
    print("Loading Demographic Data (ACS)...")
    acs = load.fetch_acs_los_angeles()
    
    # We calculate the vehicle non-ownership rate here because it's a importanrt indicator of who needs bike infrastructure the most
    acs = process.add_vehicle_rate(acs) 
    load.save_acs(acs)

    print("Loading Environmental Data (CES 4.0)...")
    ces = load.load_calenviroscreen()

    print("Loading Spatial Data (Tracts & Bikeways)...")
    tracts = load.load_census_tracts()
    bike = load.load_bikeways()
    
    # ---------------------------------------------------------
    # 2. PROCESS & MERGE
    # ---------------------------------------------------------
    print("Merging Data Layers...")
    # This combines our demographics, environment, and infrastructure data into a single master table keyed by Census Tract ID
    merged = process.merge_layers(acs, ces, bike, tracts) 
    
    # Normalize bike lanes by area (Miles per Sq Mile) so large rural tracts
    # don't skew the comparison against small urban tracts.
    merged = process.add_bike_lane_area_density(merged)
    
    # Save the clean dataset for transparency
    process.save_master(merged)

    # ---------------------------------------------------------
    # 3. STATISTICAL ANALYSIS
    # ---------------------------------------------------------
    print("Running Regression (OLS)...")
    # We want to see if bike lane density predicts lower pollution scores,
    # holding income and car access constant
    model = analyze.run_ols(
        merged,
        "ces_score", 
        ["bike_lane_density_sq_mi", "median_income", "vehicle_rate"]
    )
    
    if model:
        with open(results_dir / "regression_results.txt", "w") as f:
            f.write(model.summary().as_text())
        print("Regression results saved.")

    # ---------------------------------------------------------
    # 4. CLUSTERING
    # ---------------------------------------------------------
    print("Running K-Means Clustering...")
    # Group neighborhoods based on their combined characteristics
    cluster_cols = ["bike_lane_density_sq_mi", "ces_score", "vehicle_rate"]
    merged = analyze.add_clusters(merged, cluster_cols, k=5)

    # --- SAVE CLUSTERS TO CSV ---
    # We save a specific file for the clusters as requested
    # This file includes the Tract ID, the Cluster Label (0-4), and the variables used
    cluster_out = results_dir / "neighborhood_clusters.csv"
    merged[["GEOID", "cluster"] + cluster_cols].to_csv(cluster_out, index=False)
    print(f"Cluster assignments saved to: {cluster_out}")

    # ---------------------------------------------------------
    # 5. VISUALIZATION
    # ---------------------------------------------------------
    print("Generating Maps & Plots...")
    
    # We need to re-attach the polygon shapes to our data to make maps
    gdf = process.attach_geometry(tracts, merged)
    
    # A. Box Plot
    # Shows if bike lanes are generally in areas with cleaner or dirtier air
    analyze.save_boxplot_comparison(merged, results_dir / "boxplot_density_vs_ces.png")
    
    # B. Maps (Using custom  red-green color code for easier interpretation)
    
    # Bike Density: Red = Low Density (Bad), Green = High Density (Good)
    analyze.save_choropleth(
        gdf, 
        "bike_lane_density_sq_mi", 
        results_dir / "map_bike_density.png", 
        "Bike Lane Density (Miles/Sq Mi)",
        cmap="RdYlGn"
    )
    
    # CES Score: Green = Low Pollution (Good), Red = High Pollution (Bad)
    # Note: 'RdYlGn_r' reverses the color scale so high numbers are Red
    analyze.save_choropleth(
        gdf, 
        "ces_score", 
        results_dir / "map_ces_score.png", 
        "CalEnviroScreen 4.0 Score",
        cmap="RdYlGn_r"
    )
    
    # Vehicle Rate: Green = Low % No-Car (Good access), Red = High % No-Car (transit dependence)
    analyze.save_choropleth(
        gdf, 
        "vehicle_rate", 
        results_dir / "map_vehicle_rate.png", 
        "Households without Vehicle Access (%)",
        cmap="RdYlGn_r"
    )
    
    # Clusters: Sorted Gradient (Red=Worst -> Green=Best)
    analyze.save_cluster_map(gdf, results_dir / "map_clusters.png")
    
    print("--- Pipeline Complete ---")

if __name__ == "__main__":
    main()
