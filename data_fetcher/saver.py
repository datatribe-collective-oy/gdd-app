"""
Saves pandas DataFrames to S3 or minIO as partitioned Parquet files.

This module provides functionality to persist weather data, organized by
crop, location, and date, into an S3-compatible storage system.
It leverages shared S3 utilities and processing utilities for client
initialization and key generation.
"""

import pandas as pd
import io
import sys

try:
    from universal.s3_utils import (
        get_s3_client,
    )  # Utility to get an S3 client instance.
except ImportError:
    sys.exit(
        "CRITICAL ERROR: Could not import 'get_s3_client' from 'universal.s3_utils'. "
        "Ensure the file exists and 'gdd-app' is in PYTHONPATH."
    )
try:
    from universal.processing_utils import generate_partitioned_s3_key
except ImportError:  # Utility to create structured S3 keys.
    sys.exit(
        "CRITICAL ERROR: Could not import 'generate_partitioned_s3_key' from 'universal.processing_utils'."
    )


def save_partitioned_parquet_s3(
    df: pd.DataFrame,
    bucket: str,
    base_prefix: str,
    year_for_path: str,
    month_for_path: str,
    date_for_filename: str,
):
    """
    Saves a DataFrame to a Parquet file in S3, using a partitioned key structure.

    The S3 key is generated based on the base prefix, year, month, date,
    crop ID, and location ID. The crop ID and location ID are extracted
    from the DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to save. Expected to contain
                           'location_id' and 'crop_id' columns.
        bucket (str): The S3 bucket name.
        base_prefix (str): The base prefix for the S3 key (e.g., 'bronze/weather/').
        year_for_path (str): The year component for the S3 path (e.g., '2025').
        month_for_path (str): The month component for the S3 path (e.g., '05').
        date_for_filename (str): The date string used in constructing the S3 key,
                                 typically in 'YYYY-MM-DD' format.

    Returns:
        str: The full S3 path (s3://bucket/key) where the file was saved.
    """
    # The DataFrame `df` is expected to contain data primarily for the date_for_filename.
    # Path components are now explicitly passed.
    location = df["location_id"].iloc[0]  # Assumes all rows have the same location_id.
    crop = df["crop_id"].iloc[0]  # Assumes all rows have the same crop_id.
    key = generate_partitioned_s3_key(
        layer_prefix=base_prefix,
        year=year_for_path,
        month=month_for_path,
        day_str=date_for_filename,
        crop_id=crop,
        location_id=location,
    )
    # Write Parquet to memory buffer.
    buffer = io.BytesIO()  # Use an in-memory buffer to avoid writing to disk.
    df.to_parquet(buffer, index=False)
    buffer.seek(0)  # Reset buffer's position to the beginning for reading.

    # Get S3 client and upload the file.
    s3 = get_s3_client()
    s3.upload_fileobj(buffer, bucket, key)

    # Log and return the S3 path.
    print(f"Saved data to s3://{bucket}/{key}")
    return f"s3://{bucket}/{key}"
