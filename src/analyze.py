# src/analyze.py
import pandas as pd
import statsmodels.api as sm
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

#--------------------------------------------------------------------------------------------------------------------------------------------#
# ANALYSIS & VISUALIZATION MODULE
# Contains the core statistical models and plotting functions.
#--------------------------------------------------------------------------------------------------------------------------------------------#

# --- STATISTICAL CHECKS ---

def check_multicollinearity(df, features):
    """
    Calculates Variance Inflation Factor (VIF). If VIF is =1 NO multicollinearity is found amongst variables.
    VIF >5 OR >10, multicollinearity is present and we need to regress each variable against CES Score individually
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    d = df[features].copy()
    for col in features:
        d[col] = pd.to_numeric(d[col], errors='coerce')
    d = d.dropna()
    
    if d.empty: return
    
    X = sm.add_constant(d)
    vif = pd.DataFrame()
    vif["feature"] = X.columns
    vif["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    
    print("\n--- Multicollinearity Check (VIF) ---")
    print(vif.round(2))


#  --- ANALYSIS TOOLS ---

def run_ols(df, y, x):
    """
    Runs an Ordinary Least Squares (OLS) regression
    
    Objective: Quantify the relationship between Bike Lane Density and Environmental Score,
    while controlling for socioeconomic factors like Income and Vehicle Access
    
    We use Heteroscedasticity-Consistent standard errors
    This is standard practice for geographic data because variance usually changes 
    across different regions, especially significant in LA County where income disparities are high
    """
    d = df.copy()
    cols_to_process = [y] + x
    for col in cols_to_process:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors='coerce')
    
    d = d.dropna(subset=cols_to_process)
    
    if len(d) < 20: 
        print(f"Not enough valid data for regression (n={len(d)}). Check your input columns.")
        return None
    
    try:
        X = sm.add_constant(d[x])
        model = sm.OLS(d[y], X).fit(cov_type='HC1')
        return model
    except Exception as e:
        print(f"Regression failed: {e}")
        return None

def add_clusters(df, cols, k=5):
    """
    Performs K-Means clustering to identify neighborhood typologies. 
    
    SORTING LOGIC ADDED:
    To ensure the map colors make sense (Red=Worst, Green=Best), we sort the 
    clusters based on their Environmental Score (CES Score).
    
    Cluster 0 = Highest Pollution (Worst) -> Maps to Red
    Cluster 4 = Lowest Pollution (Best)   -> Maps to Green
    """
    d = df.copy()
    for col in cols:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors='coerce')
            
    # Create an explicit copy to avoid SettingWithCopyWarning
    fit_data = d.dropna(subset=cols).copy()
    
    if len(fit_data) < 20: 
        print("Not enough data to cluster.")
        return df
        
    # We must scale the data using Z-score normalization before clustering
    scaler = StandardScaler()
    s = scaler.fit_transform(fit_data[cols])
    
    km = KMeans(n_clusters=k, random_state=42).fit(s)
    raw_labels = km.labels_
    
    # --- SORTING STEPS ---
    # 1. Attach temporary labels using .loc to prevent warnings
    fit_data.loc[:, 'temp_label'] = raw_labels
    
    # 2. Identify which variable to sort by (Prefer CES Score for "Badness")
    sort_col = 'ces_score' if 'ces_score' in cols else cols[0]
    
    # 3. Calculate mean score for each cluster and sort descending (High score = Bad)
    # This gives us an order: Index 0 is the worst cluster, Index 4 is the best
    means = fit_data.groupby('temp_label')[sort_col].mean().sort_values(ascending=False)
    
    # 4. Create a mapping from Old Random Label -> New Sorted Label (0..4)
    # 0 will be the "Worst" (Highest CES), 4 will be "Best" (Lowest CES)
    mapping = {old_lbl: new_rank for new_rank, old_lbl in enumerate(means.index)}
    
    # 5. Apply the mapping using .loc
    fit_data.loc[:, "cluster"] = fit_data['temp_label'].map(mapping).astype(int)
    
    # Merge back keeping all rows
    return df.merge(fit_data[["GEOID", "cluster"]], on="GEOID", how="left")

# --- VISUALIZATION TOOLS ---

def save_boxplot_comparison(df, out_path):
    """
    Creates a boxplot comparing CES Scores between tracts that HAVE bike lanes
    vs tracts that DO NOT.
    
    This visualizes the 'Infrastructure Gap'. Answers the question 'Are bike lanes serving the 
    most polluted communities, or are they concentrated in cleaner areas?'
    """
    data = df.copy()
    
    # Create a binary category (0 = No Lanes, 1 = Has Lanes)
    data['has_lanes'] = data['bike_lane_density_sq_mi'] > 0
    data = data.dropna(subset=['ces_score', 'has_lanes'])
    
    plt.figure(figsize=(8, 6))
    sns.boxplot(x='has_lanes', y='ces_score', data=data, palette="Set2")
    
    plt.xlabel("Presence of Bike Infrastructure", fontsize=12)
    plt.ylabel("CalEnviroScreen 4.0 Score", fontsize=12)
    plt.title("Distribution of Environmental Burden by Infrastructure Status", fontsize=14)
    plt.xticks([0, 1], ["No Bike Lanes", "Has Bike Lanes"])
    
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

def save_choropleth(gdf, column, out_path, title, cmap='viridis'):
    """
    Generates a Choropleth (Heat) Map of Los Angeles County.
    
    Parameters:
    - cmap: The color map to use. 
      'RdYlGn' (Red-Yellow-Green) is good for "More is Better".
      'RdYlGn_r' (Reversed) is good for "More is Bad" (e.g. pollution).
    
    We use 'Quantile' classification to ensure the colors are evenly distributed,
    making it easier to see high/low patterns across the map.
    """
    if column not in gdf.columns: return

    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Ensure data is numeric
    gdf[column] = pd.to_numeric(gdf[column], errors='coerce')
    
    gdf.plot(
        column=column, 
        ax=ax, 
        legend=True, 
        cmap=cmap, 
        scheme='quantiles', # Breaks data into equal groups
        missing_kwds={'color': '#f0f0f0'} # Light grey for missing data
    )
    
    ax.set_axis_off()
    plt.title(title, fontsize=16, fontweight='bold')
    plt.savefig(out_path)
    plt.close()

def save_cluster_map(gdf, out_path):
    """
    Maps the K-Means clusters.
    
    Uses 'RdYlGn' (Red-Yellow-Green) colormap.
    Because we sorted the clusters in 'add_clusters':
    - 0 (Red) = Worst / Highest Pollution
    - 4 (Green) = Best / Lowest Pollution
    """
    if "cluster" not in gdf.columns: return

    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Ensure cluster is numeric for the gradient colormap to work correctly
    gdf["cluster"] = pd.to_numeric(gdf["cluster"], errors='coerce')
    
    gdf.plot(
        column="cluster", 
        ax=ax, 
        categorical=True, 
        legend=True, 
        cmap='RdYlGn', # Red to Green gradient
        legend_kwds={'title': 'Cluster Rank (0=Worst, 4=Best)', 'loc': 'lower right'}
    )
    
    ax.set_axis_off()
    plt.title("Neighborhood Typologies (Sorted by Environmental Score)", fontsize=16)
    plt.savefig(out_path)
    plt.close()
