import os
from .config import MAIZE_INDIA_LOCATIONS, SORGHUM_KENYA_LOCATIONS
from fetcher import fetch_weather_data
from validator import validate_weather_data
from saver import save_partitioned_parquet_s3

if __name__ == "__main__":
    # Get bucket name and base prefix from environment variables.
    S3_BUCKET_NAME = os.getenv("BRONZE_BUCKET", "gdd-raw-weather-data")
    BASE_S3_PREFIX = os.getenv("BRONZE_S3_PREFIX", "bronze")

    # Define locations to process.
    locations_to_process_config = {
        "maize": MAIZE_INDIA_LOCATIONS,
        "sorghum": SORGHUM_KENYA_LOCATIONS
    }

    print(f"Starting batch processing. Target S3 Bucket: {S3_BUCKET_NAME}, Base Prefix: {BASE_S3_PREFIX}")

    for crop_id, locations_map in locations_to_process_config.items():
        for location_id, (lat, lon) in locations_map.items():
            print(f"Processing: Crop='{crop_id}', Location='{location_id}', Coords=({lat}, {lon})")
            try:
                print(f"  1. Fetching weather data for {location_id}...")
                df_raw = fetch_weather_data(lat, lon, location_id)
                df_raw['crop_id'] = crop_id  # Add crop_id for validation and saving.

                print(f"  2. Validating weather data for {location_id}...")
                df_validated = validate_weather_data(df_raw.copy())

                print(f"  3. Saving data for {location_id} to S3...")
                save_partitioned_parquet_s3(df_validated, bucket=S3_BUCKET_NAME, base_prefix=BASE_S3_PREFIX)
                print(f"  Data for {crop_id} - {location_id} saved successfully.")
            except Exception as e:
                print(f"  ERROR processing {crop_id} - {location_id}: {e}")

    print("Batch processing finished.")
