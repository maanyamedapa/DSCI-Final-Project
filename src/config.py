# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# 1. ESTABLISH PROJECT ROOT
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(PROJECT_ROOT / "src" / ".env")

# 2. DEFINE DATA PATHS
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

# API Endpoints
ACS_BASE_URL = "https://api.census.gov/data/2023/acs/acs5"

# 3. DEFINE SPECIFIC FILE LOCATIONS
CALENVIROSCREEN_FILE = DATA_DIR / "raw" / "CalEnviroScreenData.xlsx"

# LA COUNTY BIKEWAYS SHAPEFILE 
# Make sure all .shp, .shx, .dbf, .prj files are in data/raw/
BIKEWAYS_FILE = DATA_DIR / "raw" / "LA_County_Bikeways_(2024_Metro_ATSP).shp"

TRACTS_FILE = DATA_DIR / "spatial" / "la_tracts.geojson"

