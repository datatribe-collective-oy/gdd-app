from .config import (
    MAIZE_INDIA_LOCATIONS,
    SORGHUM_KENYA_LOCATIONS,
)  # Local config for locations
from .fetcher import fetch_weather_data  
from .validator import validate_weather_data  
from .saver import save_partitioned_parquet_s3 

try:
    from universal import config as app_config
except ImportError:
    exit(
        "CRITICAL ERROR: Could not import shared configuration from 'universal.config'. Please ensure 'gdd-app' is in PYTHONPATH and 'universal/config.py' exists."
    )


if __name__ == "__main__":
    # Determine target bucket name and base prefix from shared app_config
    target_bucket_name = None
    if app_config.STORAGE_BACKEND == "minio":
        target_bucket_name = app_config.MINIO_DATA_BUCKET_NAME
    elif app_config.STORAGE_BACKEND == "s3":
        target_bucket_name = app_config.AWS_S3_DATA_BUCKET_NAME
    else:
        print(
            f"Error: Invalid STORAGE_BACKEND '{app_config.STORAGE_BACKEND}' defined in shared config."
        )
        exit(1)

    if not target_bucket_name:
        print(
            f"Error: Target bucket name could not be determined for backend '{app_config.STORAGE_BACKEND}'. Ensure it's set in shared config."
        )
        exit(1)

    base_s3_prefix = app_config.BRONZE_PREFIX

    # Define locations to process.
    locations_to_process_config = {
        "maize": MAIZE_INDIA_LOCATIONS,
        "sorghum": SORGHUM_KENYA_LOCATIONS,
    }
    print(
        f"Starting batch processing. Storage Backend: {app_config.STORAGE_BACKEND}, Target Bucket: {target_bucket_name}, Base Prefix: {base_s3_prefix}"
    )

    for crop_id, locations_map in locations_to_process_config.items():
        for location_id, (lat, lon) in locations_map.items():
            print(
                f"Processing: Crop='{crop_id}', Location='{location_id}', Coords=({lat}, {lon})"
            )
            try:
                print(f"  1. Fetching weather data for {location_id}...")
                df_raw = fetch_weather_data(lat, lon, location_id)
                df_raw["crop_id"] = crop_id  # Add crop_id for validation and saving.

                print(f"  2. Validating weather data for {location_id}...")
                df_validated = validate_weather_data(df_raw.copy())

                print(
                    f"  3. Saving data for {location_id} to {app_config.STORAGE_BACKEND} storage..."
                )
                save_partitioned_parquet_s3(
                    df_validated, bucket=target_bucket_name, base_prefix=base_s3_prefix
                )
                print(f"  Data for {crop_id} - {location_id} saved successfully.")
            except Exception as e:
                print(f"  ERROR processing {crop_id} - {location_id}: {e}")

    print("Batch processing finished.")
