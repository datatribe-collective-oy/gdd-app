"""
This module is responsible for writing the calculated Growing Degree Days (GDD) data
to the silver layer of the data lake (S3 or MinIO).
It handles data partitioning and ensures data is saved in Parquet format.
"""

import pandas as pd
import io
import logging
import sys

try:
    from universal import config as app_config
except ImportError:
    sys.exit(
        "CRITICAL ERROR: Could not import shared configuration from 'universal.config'. "
        "Please ensure 'gdd-app' is in PYTHONPATH and 'universal/config.py' exists."
    )

try:
    from universal.s3_utils import get_s3_client, s3_object_exists
except ImportError:
    sys.exit(
        "CRITICAL ERROR: Could not import 'get_s3_client' from 'universal.s3_utils'. "
        "Ensure the file exists and 'gdd-app' is in PYTHONPATH."
    )
try:
    from universal.processing_utils import generate_partitioned_s3_key
except ImportError:
    sys.exit(
        "CRITICAL ERROR: Could not import 'generate_partitioned_s3_key' from 'universal.processing_utils'."
    )

logger = logging.getLogger(__name__)


class GDDWriteError(Exception):
    """
    Custom exception raised for errors encountered during the process of writing
    GDD data to the silver layer.
    """

    pass


def save_gdd_silver_data(
    silver_df: pd.DataFrame, target_bucket: str, target_base_prefix: str
):
    """
    Saves the processed GDD DataFrame to the silver layer in S3/MinIO,
    partitioning by year, month, crop_id, and location_id. Each unique combination
    of date, crop_id, and location_id results in a separate Parquet file.

    The function iterates through each row of the input DataFrame, constructs a
    partitioned S3 key, and saves the individual record as a Parquet file.
    It checks if an object with the same key already exists to prevent overwriting,
    logging a skip message if it does.

    Args:
        silver_df (pd.DataFrame): The DataFrame containing the calculated GDD data.
                                    It is expected to have columns including 'date' (datetime-like),
                                    'crop_id', and 'location_id', which are used for partitioning,
                                    along with the GDD metrics themselves.
        target_bucket (str): The name of the S3 or MinIO bucket where data will be saved.
        target_base_prefix (str): The base prefix within the target bucket under which
                                    the partitioned data will be stored.

    Raises:
        GDDWriteError: If any error occurs during the S3 upload process for any record.
    """
    logger.info(
        f"Saving GDD Silver Layer Data to {app_config.STORAGE_BACKEND} bucket '{target_bucket}' under prefix '{target_base_prefix}'"
    )

    # Prepare columns for partitioning and filename, if not already present from calculation step.
    silver_df["year_for_path"] = silver_df["date"].dt.year
    silver_df["month_for_path"] = silver_df[
        "date"
    ].dt.month  # Extract month as integer.
    silver_df["date_for_filename"] = silver_df["date"].dt.strftime(
        "%Y-%m-%d"
    )  # Format date as YYYY-MM-DD string for filename.

    s3_client = (
        get_s3_client()
    )  # Obtain an S3 client configured for the target storage backend.
    successful_saves = 0
    skipped_saves = 0

    # Iterate over each row in the DataFrame to save it as an individual Parquet file.
    # This approach creates one file per (date, crop_id, location_id) combination.
    for _, row_data in silver_df.iterrows():
        # Extract values needed for constructing the S3 key and partitioning.
        year_val = row_data["year_for_path"]
        month_val = row_data["month_for_path"]
        crop_val = row_data["crop_id"]
        loc_val = row_data["location_id"]
        date_str_val = row_data["date_for_filename"]

        # Create a new DataFrame containing only the current row's data,
        # excluding the temporary helper columns used for path generation.
        # This ensures only the actual GDD record is saved to Parquet.
        record_to_save_df = pd.DataFrame(
            [row_data.drop(["year_for_path", "month_for_path", "date_for_filename"])]
        )

        # Generate the fully partitioned S3 key for the current record.
        s3_key = generate_partitioned_s3_key(
            layer_prefix=target_base_prefix,
            year=year_val,
            month=month_val,
            day_str=date_str_val,  # The day_str is used as part of the filename.
            crop_id=crop_val,
            location_id=loc_val,
        )
        if s3_object_exists(s3_client, target_bucket, s3_key):
            logger.debug(
                f"Skipping save: Silver data file s3://{target_bucket}/{s3_key} already exists."
            )
            skipped_saves += 1
            continue

        # Serialize the single-record DataFrame to a Parquet format in an in-memory buffer.
        parquet_buffer = io.BytesIO()
        record_to_save_df.to_parquet(parquet_buffer, index=False, engine="pyarrow")
        parquet_buffer.seek(
            0
        )  # Reset buffer's position to the beginning for reading by put_object.

        try:
            # Upload the Parquet data from the buffer to S3/MinIO.
            s3_client.put_object(Bucket=target_bucket, Key=s3_key, Body=parquet_buffer)
            successful_saves += 1
        except Exception as e:
            # If any S3 upload fails, wrap the error in GDDWriteError and re-raise.
            raise GDDWriteError(
                f"Failed to upload {s3_key} to {target_bucket}: {e}"
            ) from e  # Preserve the original exception.

    logger.info(
        f"Successfully saved {successful_saves} GDD files to {app_config.STORAGE_BACKEND}. "
        f"Skipped {skipped_saves} files that already existed."
    )
