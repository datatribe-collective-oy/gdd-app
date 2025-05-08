from config import MAIZE_INDIA_LOCATIONS, SORGHUM_KENYA_LOCATIONS
from fetcher import fetch_weather_data
from validator import validate_weather_data
from saver import save_partitioned_parquet_s3

if __name__ == "__main__":
    all_locations = {}

    for loc, coords in MAIZE_INDIA_LOCATIONS.items():
        all_locations[f"maize_india__{loc}"] = coords

    for loc, coords in SORGHUM_KENYA_LOCATIONS.items():
        all_locations[f"sorghum_kenya__{loc}"] = coords

    for location, (lat, lon) in all_locations.items():
        print(f"Fetching data for {location}...")

        df = fetch_weather_data(lat, lon, location)
        df = validate_weather_data(df)
        bucket = "gdd-raw-weather-data"
        save_partitioned_parquet_s3(df, bucket)
