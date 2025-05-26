"""
This module orchestrates the GDD (Growing Degree Days) calculation process.
It determines input data paths, invokes the GDD calculator, and then saves the results to the silver layer.
"""

import sys
from datetime import datetime, timedelta, timezone
import logging

try:
    from universal import config as app_config
except ImportError:
    sys.exit(
        "CRITICAL ERROR: Could not import shared configuration from 'universal.config'. "
        "Please ensure 'gdd-app' is in PYTHONPATH and 'universal/config.py' exists."
    )

try:
    from .calculator import calculate_daily_gdd, GDCalculationError
    from .writer import save_gdd_silver_data, GDDWriteError
except ImportError as e:
    sys.exit(
        f"CRITICAL ERROR: Could not import modules from 'gdd_counter.calculator' or 'gdd_counter.writer'. "
        f"Ensure these files exist and 'gdd-app' is in PYTHONPATH. Original error: {e}"
    )
try:
    from universal.processing_utils import generate_daily_s3_glob_uri
except ImportError as e:
    sys.exit(
        f"CRITICAL ERROR: Could not import 'generate_daily_s3_glob_uri' from 'universal.processing_utils'. Original error: {e}"
    )

# Logging configuration.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
# Reduce verbosity of AWS SDK (boto3/botocore) logs.
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("s3transfer").setLevel(
    logging.WARNING
)  # s3transfer is used by boto3 for S3 transfers.


class GDDProcessingError(Exception):
    """
    Custom exception raised for errors encountered during the overall GDD processing workflow.
    This can include issues with path determination, calculation, or writing steps.
    """

    pass


def process_gdd_for_silver_layer(bronze_data_glob_input: str | None = None):
    """
    Processes bronze layer data to calculate GDD and stores it in the silver layer.

    This function serves as the main entry point for the GDD calculation pipeline.
    It first determines the S3 paths for the bronze layer data. If a specific glob pattern
    is provided, it uses that. Otherwise, it defaults to processing data for the
    current day and the previous day.

    After identifying the input paths, it calls the `calculate_daily_gdd` function
    to perform the GDD calculations. The resulting DataFrame is then validated before
    being passed to `save_gdd_silver_data` for storage in the silver layer of the data lake.

    Args:
        bronze_data_glob_input (str | None, optional): A specific S3 glob pattern for bronze
                                                       layer Parquet files (e.g., "bronze/weather_data/year=2025/*/*/*.parquet").
                                                       If None, the function defaults to processing data for the last 2 days (today and yesterday).
    """
    bronze_paths_to_process: list[str]
    base_bronze_prefix = app_config.BRONZE_PREFIX

    # Determine current data bucket name based on storage backend.
    current_data_bucket_name = None
    if app_config.STORAGE_BACKEND == "minio":
        current_data_bucket_name = app_config.MINIO_DATA_BUCKET_NAME
    elif app_config.STORAGE_BACKEND == "s3":
        current_data_bucket_name = app_config.AWS_S3_DATA_BUCKET_NAME
    else:
        raise GDDProcessingError(
            f"Unknown or unsupported STORAGE_BACKEND '{app_config.STORAGE_BACKEND}'. Supported options are 'minio' or 's3'."
        )  # Ensure the configured backend is valid.

    if not current_data_bucket_name:
        # This check is important if the config might have a valid backend string
        # but is missing the corresponding bucket name.
        raise GDDProcessingError(
            f"Data bucket name could not be determined for backend '{app_config.STORAGE_BACKEND}'. Ensure it is set in the shared configuration."
        )

    if bronze_data_glob_input:
        logging.info(
            f"Starting GDD processing for Silver layer using provided glob: {bronze_data_glob_input}"
        )
        # If the storage backend is S3-compatible (MinIO or AWS S3) and the input glob
        # does not already start with a scheme (s3://, http://, https://),
        # prepend the S3 scheme and bucket name to form a full S3 URI.
        if app_config.STORAGE_BACKEND in ["minio", "s3"] and not any(
            bronze_data_glob_input.startswith(scheme)
            for scheme in ["s3://", "http://", "https://"]
        ):
            processed_glob = f"s3://{current_data_bucket_name}/{bronze_data_glob_input.lstrip('/')}"  # lstrip('/') ensures no double slashes if input starts with one.
            bronze_paths_to_process = [processed_glob]
            logging.info(f"  Adjusted S3 glob path to: {processed_glob}")
        else:
            # If it's not an S3 backend or already has a scheme, use as is.
            bronze_paths_to_process = [bronze_data_glob_input]
    else:
        # Default behavior: process data for today and yesterday.
        logging.info(
            "Starting GDD processing for Silver layer for the last 2 days, starting from today."
        )
        today = datetime.now(timezone.utc)
        yesterday = today - timedelta(days=1)

        glob_today = generate_daily_s3_glob_uri(
            # Uses the utility function to create a date-partitioned S3 glob.
            bucket_name=current_data_bucket_name,
            layer_prefix=base_bronze_prefix,
            target_date=today,
        )
        glob_yesterday = generate_daily_s3_glob_uri(
            bucket_name=current_data_bucket_name,
            layer_prefix=base_bronze_prefix,
            target_date=yesterday,
        )
        bronze_paths_to_process = [glob_today, glob_yesterday]
        logging.info(f"  Generated globs: {bronze_paths_to_process}")

    try:
        # Calculate GDD using the determined bronze data paths.
        logging.info("Calculating GDD...")
        silver_df = calculate_daily_gdd(bronze_paths_to_process)
        logging.info("Silver Layer: Daily GDD Data (Sample after calculation)")
        logging.info(
            f"\n{silver_df.head().to_string()}"
        )  # Log the head of the resulting DataFrame for quick inspection.

        # Validate the results from the calculation step.
        # An empty DataFrame indicates no data was processed or found.
        if silver_df.empty:
            logging.warning(
                "Warning: No data processed from DuckDB query for Silver layer. Output will be empty."
            )
            # Raise an error to halt processing if no data is produced,
            # as there's nothing to save to the silver layer.
            raise GDDProcessingError(
                "No data processed from DuckDB query for Silver layer. Output would be empty."
            )

        # Determine S3 target details and save the processed data.
        logging.info("Saving Silver Layer Data...")
        # In this application's setup, the silver layer data is stored in the same
        # bucket as the bronze layer, but under a different prefix (e.g., "silver/").
        target_bucket_for_silver = current_data_bucket_name
        target_base_prefix = app_config.SILVER_PREFIX
        save_gdd_silver_data(silver_df, target_bucket_for_silver, target_base_prefix)

        logging.info("Silver layer GDD data processing complete.")

    except (
        GDCalculationError,
        GDDWriteError,
    ) as e:  # Catch specific custom exceptions.
        # Re-raise caught calculation or write errors as a general processing error,
        # preserving the original exception for context.
        raise GDDProcessingError(f"A step in GDD processing failed: {e}") from e


# The `if __name__ == "__main__":` block allows this script to be run directly.

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Processes bronze layer data to calculate GDD and stores it in the silver layer."
    )
    parser.add_argument(
        "bronze_data_glob_input",
        type=str,
        nargs="?",  # Makes the argument optional.
        default=None,  # Default value if argument is not provided.
        help="Optional: Glob pattern for bronze layer Parquet files (e.g., 'bronze/weather_data/year=2025/*/*/*.parquet'). "
        "If not provided, processes data for the last 2 days, starting from today.",
    )
    args = parser.parse_args()

    try:
        process_gdd_for_silver_layer(args.bronze_data_glob_input)
        logging.info("GDD Counter script finished successfully.")
    except GDDProcessingError as e:
        logging.error(f"ERROR in GDD Counter script: {e}")
        sys.exit(1)
    except Exception as e:  # Catch any other unexpected errors.
        # Log critical errors with full traceback information for debugging.
        logging.critical(f"UNEXPECTED ERROR in GDD Counter script: {e}", exc_info=True)
        sys.exit(1)
