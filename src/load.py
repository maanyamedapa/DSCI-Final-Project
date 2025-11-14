# src/load.py

# This file downloads data from the U.S. Census ACS API.
# The goal is to fetch basic information for all census tracts
# in Los Angeles County (like median income and population).

# This API does NOT require a key, which keeps the project simple
# and safe for the progress submission.


import os
import requests
import pandas as pd


def fetch_los_angeles_acs():
    """
    Pulls ACS 2023 data for Los Angeles County.
    This includes:
        - median household income
        - population
        - households without a vehicle

    Returns:
        A pandas DataFrame with GEOID and the selected variables.
    """

    # API URL — this asks for the variables we want
    base_url = "https://api.census.gov/data/2023/acs/acs5"
    chosen_variables = ["B19013_001E", "B01001_001E", "B08201_002E"]

    # Build the full URL for Los Angeles County (state=06, county=037)
    full_url = (
        f"{base_url}?get=NAME,{','.join(chosen_variables)}"
        "&for=tract:*&in=state:06+county:037"
    )

    # Send request to the API
    response = requests.get(full_url, timeout=60)
    response.raise_for_status()

    raw_json = response.json()

    # The first row is the header
    column_names = [
        "NAME",
        "median_income",
        "population",
        "households_no_vehicle",
        "state",
        "county",
        "tract",
    ]

    data = pd.DataFrame(raw_json[1:], columns=column_names)

    # Build full tract GEOID
    data["GEOID"] = data["state"] + data["county"] + data["tract"]

    # Convert numeric fields
    for col in ["median_income", "population", "households_no_vehicle"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    # Only return the cleaned useful columns
    return data[["GEOID", "median_income", "population", "households_no_vehicle"]]


def save_acs_to_file(df, path="data/los_angeles_acs.csv"):
    """
    Saves the downloaded data to a CSV file inside the /data folder.
    The /data folder is gitignored, so this file will NOT be committed
    to GitHub (which is what the professor wants).

    Returns:
        The path where the file is saved.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return path
