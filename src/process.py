# src/process.py
#
# This file applies simple data transformations to the ACS data.
# For this progress step, we calculate the share of households
# that do NOT have access to a vehicle.
#
# This keeps the logic small, clear, and easy to test.


import pandas as pd


def compute_vehicle_access_rate(df):
    """
    Adds a new column showing the percentage of households
    without a vehicle in each census tract.

    The formula is:
        households_no_vehicle / population

    We return a NEW DataFrame so that the original is unchanged.
    """
    result = df.copy()

    # Avoid division by zero issues — if population is 0,
    # the rate will be marked as NA.
    result["no_vehicle_rate"] = (
        result["households_no_vehicle"]
        / result["population"].replace(0, pd.NA)
    )

    return result
