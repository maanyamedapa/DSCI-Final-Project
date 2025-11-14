#tests.py
#
# These tests show that:
#   1. We can pull real data from an API
#   2. We can process it
#   3. We can save it safely to the /data folder


from src.load import fetch_los_angeles_acs, save_acs_to_file
from src.process import compute_vehicle_access_rate


def test_api_fetch():
    """Check that the ACS API download returns a real, non-empty DataFrame."""
    df = fetch_los_angeles_acs()
    assert not df.empty, "The API did not return any data."
    for col in ["GEOID", "median_income", "population", "households_no_vehicle"]:
        assert col in df.columns, f"Missing expected column: {col}"


def test_processing():
    """Check that the no_vehicle_rate column gets added correctly."""
    sample = fetch_los_angeles_acs().head(20)
    processed = compute_vehicle_access_rate(sample)
    assert "no_vehicle_rate" in processed.columns, "Rate column not created."
    # We expect at least one non-null value
    assert processed["no_vehicle_rate"].notna().any(), "Rate column is all empty."


def test_saving():
    """Check that saving the file creates a CSV in the data/ folder."""
    df = fetch_los_angeles_acs().head(10)
    path = save_acs_to_file(df, path="data/test_output.csv")
    import os
    assert os.path.exists(path), "Saving ACS data failed."


# If someone manually runs: python tests.py
if __name__ == "__main__":
    test_api_fetch()
    test_processing()
    test_saving()
    print("All tests passed successfully.")
