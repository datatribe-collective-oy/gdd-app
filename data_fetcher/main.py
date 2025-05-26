"""
Main entry point for the weather data fetching application.

This script orchestrates the process of fetching weather data from an external API,
validating it, and saving it to a specified S3-compatible storage backend
(MinIO or AWS S3) in a partitioned Parquet format (bronze layer).

It can be run to process data for specific dates or, by default, for
today and yesterday, ensuring data completeness and handling potential
API forecast updates.
"""

from .config import (
    MAIZE_INDIA_LOCATIONS,
    SORGHUM_KENYA_LOCATIONS,
)  # Local configuration for specific crop locations.
from .fetcher import fetch_weather_data
from .validator import validate_weather_data
from .saver import save_partitioned_parquet_s3

try:
    from universal import config as app_config  # Shared application-wide configuration.
    from universal.s3_utils import (
        get_s3_client,
        get_s3_parquet_to_df_if_exists,
    )  # Utilities for S3 interaction.
    from universal.processing_utils import (
        determine_fetcher_processing_dates,
        generate_partitioned_s3_key,
    )  # Utilities for data processing tasks like date determination and key generation.
except ImportError:
    # This is a critical failure if shared modules cannot be imported.
    # Ensure 'gdd-app' is in PYTHONPATH.
    exit(
        "CRITICAL ERROR: Could not import shared configuration or S3 utils from 'universal' package. "
        "Please ensure 'gdd-app' is in PYTHONPATH and 'universal/config.py' and 'universal/s3_utils.py' exist."
    )

import pandas as pd  # For DataFrame manipulation.
import argparse  # For command-line arguments.
import logging  # For logging application events.

# Configure basic logging for the application.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def run_data_fetcher(target_date_str: str | None = None):
    """
    Fetches, validates, and saves weather data to the bronze layer.

    If target_date_str is None, processes data for today and yesterday.
    Otherwise, processes for the specified date.

    Args:
        target_date_str (str | None): Specific date in 'YYYY-MM-DD' format,
                                      or None to default to processing for today and yesterday.
    """
    # Determine target bucket name from shared app_config based on the storage backend.
    target_bucket_name = None
    if (
        app_config.STORAGE_BACKEND == "minio"
    ):  # Check if MinIO is the configured backend.
        target_bucket_name = app_config.MINIO_DATA_BUCKET_NAME
    elif app_config.STORAGE_BACKEND == "s3":
        target_bucket_name = app_config.AWS_S3_DATA_BUCKET_NAME
    else:
        logging.error(
            f"Error: Invalid STORAGE_BACKEND '{app_config.STORAGE_BACKEND}' defined in shared config."
        )
        exit(1)

    # Ensure a target bucket name was successfully determined.
    if not target_bucket_name:
        logging.error(
            f"Error: Target bucket name could not be determined for backend '{app_config.STORAGE_BACKEND}'. Ensure it's set in shared config."
        )
        exit(1)

    base_s3_prefix = (
        app_config.BRONZE_PREFIX
    )  # Base S3 prefix for the bronze data layer.

    # Initialize S3 client once for reuse.
    try:
        s3_client = get_s3_client()
    except Exception as e:
        logging.error(f"Fatal: Error initializing S3 client: {e}. Exiting.")
        exit(1)

    # Define locations to process. This needs to be defined before the pre-check for yesterday.
    locations_to_process_config = {
        "maize": MAIZE_INDIA_LOCATIONS,
        "sorghum": SORGHUM_KENYA_LOCATIONS,
    }

    # Determine the specific dates for which data needs to be fetched and processed.
    try:
        dates_to_process = determine_fetcher_processing_dates(
            target_date_str=target_date_str,
            s3_client=s3_client,
            bucket_name=target_bucket_name,
            bronze_prefix=base_s3_prefix,
            locations_config=locations_to_process_config,
            expected_rows_per_day=24,  # Expected 24 hourly records per day.
        )
    except (
        ValueError
    ):  # Raised by determine_fetcher_processing_dates for bad date format.
        exit(1)
    except Exception as e:
        logging.error(f"Fatal: Error determining dates to process: {e}. Exiting.")
        exit(1)

    logging.info(
        f"Starting data fetching. Storage Backend: {app_config.STORAGE_BACKEND}, Target Bucket: {target_bucket_name}, Base Prefix: {base_s3_prefix}"
    )

    for process_dt in dates_to_process:
        # Prepare date components for path construction and logging.
        current_year_str = str(process_dt.year)
        current_month_str = f"{process_dt.month:02d}"
        current_day_str = process_dt.strftime("%Y-%m-%d")
        logging.info(f"\n Processing data for date: {current_day_str}")

        for crop_id, locations_map in locations_to_process_config.items():
            for location_id, (lat, lon) in locations_map.items():
                logging.info(
                    f"  Processing: Date='{current_day_str}', Crop='{crop_id}', Location='{location_id}', Coords=({lat}, {lon})"
                )

                # Construct the expected S3 key for the current processing date, crop, and location.
                expected_bronze_key = generate_partitioned_s3_key(
                    layer_prefix=base_s3_prefix,
                    year=current_year_str,
                    month=current_month_str,
                    day_str=current_day_str,
                    crop_id=crop_id,
                    location_id=location_id,
                )

                # Check if data already exists in S3 for this partition.
                df_existing = get_s3_parquet_to_df_if_exists(
                    s3_client, target_bucket_name, expected_bronze_key
                )
                try:
                    logging.info(
                        f"    Fetching weather data for {location_id} for {current_day_str}..."
                    )
                    # Note: The API typically gives a forecast, so fetching for "yesterday" will still give current forecast.
                    # The key is that we are *saving* it under yesterday's date partition.
                    df_newly_fetched = fetch_weather_data(lat, lon, location_id)
                    df_newly_fetched["crop_id"] = (
                        crop_id  # Add crop_id early for context.
                    )

                    if df_newly_fetched.empty:
                        logging.info(
                            f"    No data fetched from API for {location_id} for {current_day_str}. Skipping."
                        )
                        continue

                    # Timestamps in df_newly_fetched are already datetime objects and UTC-aware from fetcher.py.
                    # CRUCIAL: Filter newly fetched data to ONLY include records for the target processing date (process_dt)
                    # This ensures we only consider data relevant to the file we are trying to build/update.
                    df_newly_fetched = df_newly_fetched[
                        df_newly_fetched["timestamp"].dt.date == process_dt.date()
                    ]

                    if df_existing is not None:
                        logging.info(
                            f"    Merging newly fetched data with existing data from s3://{target_bucket_name}/{expected_bronze_key}"
                        )
                        # Ensure existing timestamps are datetime objects and localized to UTC if naive, then converted to UTC.
                        df_existing["timestamp"] = pd.to_datetime(
                            df_existing["timestamp"]
                        )
                        # If timestamps are naive, localize to UTC. If timezone-aware, convert to UTC.
                        df_existing["timestamp"] = (
                            df_existing["timestamp"]
                            .dt.tz_convert(None)
                            .dt.tz_localize("UTC")
                        )
                        # Combine, prioritize newly fetched data for duplicate timestamps within the same day.
                        df_combined = pd.concat(
                            [df_existing, df_newly_fetched], ignore_index=True
                        )
                        # Sort by timestamp, then use a marker to keep 'new' over 'existing' if timestamps are identical
                        # This assumes newly_fetched is more up-to-date for a given hour.
                        # Drop duplicates, keeping the 'last' entry (from newly_fetched) for any identical timestamps.
                        df_processed = df_combined.sort_values(
                            by="timestamp"
                        ).drop_duplicates(
                            subset=["timestamp", "location_id", "crop_id"], keep="last"
                        )
                        logging.info(
                            f"      Combined and de-duplicated data shape for {current_day_str}: {df_processed.shape}"
                        )
                    else:
                        logging.info(
                            f"    No existing data found for {current_day_str}. Using newly fetched data."
                        )
                        # Ensure newly fetched data (already filtered for process_dt) is sorted by timestamp.
                        df_processed = df_newly_fetched.sort_values(by="timestamp")

                    # At this point, df_processed should ONLY contain unique hourly data for process_dt.
                    if not df_processed.empty:
                        logging.info(
                            f"    Validating final weather data for {location_id} for {current_day_str}..."
                        )
                        # Convert process_dt (a datetime.datetime object) to a UTC-aware pandas Timestamp for the validator.
                        # First, create a pandas Timestamp from the datetime.datetime object.
                        temp_timestamp = pd.Timestamp(process_dt)
                        # Then, ensure it is UTC. If naive, localize to UTC. If already timezone-aware, convert to UTC.
                        if temp_timestamp.tzinfo is None:
                            target_pd_timestamp = temp_timestamp.tz_localize("UTC")
                        else:
                            target_pd_timestamp = temp_timestamp.tz_convert("UTC")
                        df_validated = validate_weather_data(
                            df_processed.copy(),  # Pass a copy to avoid unintended modifications.
                            target_processing_date=target_pd_timestamp,
                        )

                        logging.info(
                            f"    Saving data for {location_id} for {current_day_str} to {app_config.STORAGE_BACKEND} storage..."
                        )
                        saved_path = save_partitioned_parquet_s3(
                            df_validated,  # Save the validated, hopefully complete-day data.
                            bucket=target_bucket_name,
                            base_prefix=base_s3_prefix,
                            year_for_path=current_year_str,
                            month_for_path=current_month_str,
                            date_for_filename=current_day_str,
                        )
                        logging.info(
                            f"    Data for {crop_id} - {location_id} for {current_day_str} saved to {saved_path}"
                        )
                    else:  # df_processed is empty after fetch/merge/filter.
                        logging.warning(
                            f"    No data to save for {crop_id} - {location_id} for {current_day_str} after fetch/merge/filter. Skipping save."
                        )
                except Exception as e:
                    # Log errors encountered during processing for a specific location/date and continue to the next.
                    logging.error(
                        f"    ERROR processing {crop_id} - {location_id} for {current_day_str}: {e}"
                    )

    logging.info("\nData fetching process finished.")


if __name__ == "__main__":
    # Set up command-line argument parsing.
    parser = argparse.ArgumentParser(
        description="Fetches weather data and stores it in the bronze layer. Processes today and yesterday by default."
    )
    parser.add_argument(
        # Optional argument to specify a single date for processing.
        "--date",
        type=str,
        default=None,
        help="Optional: Specific date to process in YYYY-MM-DD format. ",
    )
    args = parser.parse_args()

    # Run the main data fetching logic with the provided or default date.
    run_data_fetcher(target_date_str=args.date)
