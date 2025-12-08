# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# 1. ESTABLISH PROJECT ROOT
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(PROJECT_ROOT / "src" / ".env")

# 2. # Directories, (DEFINE DATA PATHS)
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

# API Endpoints
# We use the 2023 ACS 5-year estimates for stable tract-level data
ACS_BASE_URL = "https://api.census.gov/data/2023/acs/acs5"

# 3. DEFINE SPECIFIC FILE LOCATIONS: # Local File Paths, CalEnviroScreen contains pollution burden scores and pm2.5 per tract
CALENVIROSCREEN_FILE = DATA_DIR / "raw" / "CalEnviroScreenData.xlsx"

# LA COUNTY BIKEWAYS SHAPEFILE : 2024 Metro ATSP shapefile contains the vector lines for bike lanes
# Make sure all .shp, .shx, .dbf, .prj files are in data/raw/
BIKEWAYS_FILE = DATA_DIR / "raw" / "LA_County_Bikeways_(2024_Metro_ATSP).shp"

#--------------------------------------------------------------------------------------------------------------------------------------------#
# Standard Census Tract boundaries for LA County
#(EPSG:3310 projection instead of Lat/Lon to accurately represent LA County's shape and area using meters, ideal for showing distributions where area preservation is key.
#(EPSG:2229)can also be used for smaller regional comparision
#--------------------------------------------------------------------------------------------------------------------------------------------#
TRACTS_FILE = DATA_DIR / "spatial" / "la_tracts.geojson"

