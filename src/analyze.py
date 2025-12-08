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
    Performs K-Means clustering to identify neighborhood typologies. Groups tracts based on shared characterisitcs.  
    """
    d = df.copy()
    for col in cols:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors='coerce')
            
    fit_data = d.dropna(subset=cols)
    if len(fit_data) < 20: 
        print("Not enough data to cluster.")
        return df
    
    scaler = StandardScaler()
    s = scaler.fit_transform(fit_data[cols])
    
    km = KMeans(n_clusters=k, random_state=42).fit(s)
    
    fit_data["cluster"] = km.labels_.astype(str)
    
    # Merge back keeping all rows
    return df.merge(fit_data[["GEOID", "cluster"]], on="GEOID", how="left")

# --- VISUALIZATION TOOLS ---

def plot_scatter_relationships(df, out_dir):
    """
    Generates a Choropleth (Heat) Map of Los Angeles County.
    We use 'Quantile' classification to ensure the colors are evenly distributed,
    making it easier to see high/low patterns across the map
    """
    plots = [
        {"y": "ces_score", "t": "CES 4.0 Score", "f": "scatter_ces.png"},
        {"y": "pm25", "t": "PM2.5 Levels", "f": "scatter_pm25.png"},
    ]
    x_var = "bike_lane_density_sq_mi"
    x_label = "Bike Lane Density (Miles / Sq. Mi)"
    
    if x_var not in df.columns: return

    d = df.copy()
    d[x_var] = pd.to_numeric(d[x_var], errors='coerce')
    d['has_bike_lanes'] = d[x_var] > 0

    for p in plots:
        y_var = p["y"]
        if y_var not in d.columns: continue
        d[y_var] = pd.to_numeric(d[y_var], errors='coerce')
        plot_data = d.dropna(subset=[x_var, y_var])
        if plot_data.empty: continue

        # Scatter Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.regplot(x=x_var, y=y_var, data=plot_data, ax=ax, scatter_kws={'alpha':0.5})
        
        # Proper Axis Labels
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(p['t'], fontsize=12)
        plt.title(f"Relationship: {x_label} vs {p['t']}", fontsize=14)
        
        plt.tight_layout()
        plt.savefig(out_dir / p["f"])
        plt.close()

        # Boxplot
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.boxplot(x='has_bike_lanes', y=y_var, hue='has_bike_lanes', data=plot_data, ax=ax, legend=False, palette="Set2")
        
        ax.set_xlabel("Has Bike Lanes?", fontsize=12)
        ax.set_ylabel(p['t'], fontsize=12)
        ax.set_xticklabels(["No", "Yes"])
        
        plt.title(f"{p['t']} by Bike Lane Presence", fontsize=14)
        plt.tight_layout()
        plt.savefig(out_dir / p["f"].replace("scatter", "boxplot"))
        plt.close()

def save_choropleth(gdf, column, out, title):
    if column not in gdf.columns: return
    
    gdf[column] = pd.to_numeric(gdf[column], errors='coerce')
    valid = gdf[column].dropna()
    if valid.empty: return

    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    try:
        gdf.plot(column=column, ax=ax, legend=True, cmap='viridis', scheme='quantiles', missing_kwds={'color': 'lightgrey'})
    except:
        gdf.plot(column=column, ax=ax, legend=True, cmap='viridis')
        
    ax.set_axis_off()
    plt.title(title, fontsize=16, fontweight='bold')
    plt.savefig(out)
    plt.close()

def save_cluster_map(gdf, out):
    if "cluster" not in gdf.columns: 
        print("Cannot map clusters: 'cluster' column missing.")
        return
        
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    gdf.plot(
        column="cluster", 
        ax=ax, 
        cmap="tab10", 
        legend=True, 
        categorical=True, 
        missing_kwds={'color': 'lightgrey'}, 
        legend_kwds={'loc': 'lower right', 'title': 'Neighborhood Type'}
    )
    
    ax.set_axis_off()
    plt.title("Neighborhood Clusters (K-Means)", fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
