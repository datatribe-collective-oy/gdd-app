from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from botocore.exceptions import ClientError
from botocore.client import BaseClient

# 'universal' package from the project root.
from universal import config as app_config
from universal.processing_utils import generate_partitioned_s3_key

# Import the S3 utility function.
try:
    from universal.s3_utils import get_s3_parquet_to_df_if_exists
except ImportError:
    print(
        "CRITICAL WARNING: Could not import 'get_s3_parquet_to_df_if_exists' from 'universal.s3_utils'."
    )
    print("Data retrieval service functions will not function correctly.")
    get_s3_parquet_to_df_if_exists = None

logger = logging.getLogger(__name__)


def _get_bucket_name() -> str:
    """Determines the correct bucket name based on storage backend config."""
    if app_config.STORAGE_BACKEND == "minio":
        bucket_name = app_config.MINIO_DATA_BUCKET_NAME
    elif app_config.STORAGE_BACKEND == "s3":
        bucket_name = app_config.AWS_S3_DATA_BUCKET_NAME
    else:
        # This should ideally be caught earlier during client init.
        raise ValueError("Invalid storage backend configuration.")

    if not bucket_name:
        raise ValueError("S3 bucket name is not configured for the selected backend.")

    return bucket_name


def get_weather_data_for_period(
    s3_client: BaseClient,
    location_id: str,
    crop_id: str,
    end_date: datetime,
    days_window: int = 6,  # 7 days total.
) -> List[Dict[str, Any]]:
    """
    Fetches weather data for a specified location, crop, and date range from the bronze layer.
    """
    if get_s3_parquet_to_df_if_exists is None:
        raise RuntimeError(
            "S3 utility (get_s3_parquet_to_df_if_exists) is not available."
        )

    try:
        bucket_name = _get_bucket_name()
    except ValueError as e:
        raise RuntimeError(f"Configuration error: {e}") from e

    dates_to_fetch: List[datetime] = []
    for i in range(days_window, -1, -1):
        current_processing_date = end_date - timedelta(days=i)
        dates_to_fetch.append(current_processing_date)

    all_records: List[Dict[str, Any]] = []

    try:
        for dt_obj in dates_to_fetch:
            s3_key = generate_partitioned_s3_key(
                layer_prefix=app_config.BRONZE_PREFIX,
                year=str(dt_obj.year),
                month=f"{dt_obj.month:02d}",
                day_str=dt_obj.strftime("%Y-%m-%d"),
                crop_id=crop_id,
                location_id=location_id,
            )
            df = get_s3_parquet_to_df_if_exists(s3_client, bucket_name, s3_key)

            if df is not None and not df.empty:
                all_records.extend(df.to_dict(orient="records"))

    except ClientError as e:
        # Re-raise ClientError and the router will catch it.
        raise e
    except Exception as e:
        # Catch other unexpected errors during data fetching.
        logger.error(f"Unexpected error fetching weather data: {e}")
        raise RuntimeError(
            f"An unexpected error occurred while fetching data: {e}"
        ) from e

    return all_records


def get_gdd_data_for_period(
    s3_client: BaseClient,
    location_id: str,
    crop_id: str,
    end_date: datetime,
    exact_match: bool = False,
    days_window: int = 29,  # 30 days total for default.
) -> List[Dict[str, Any]]:
    """
    Fetches GDD data for a specified location, crop, and date range from the silver layer.
    Can fetch for an exact date or a window ending on the date.
    """
    if get_s3_parquet_to_df_if_exists is None:
        raise RuntimeError(
            "S3 utility (get_s3_parquet_to_df_if_exists) is not available."
        )

    try:
        bucket_name = _get_bucket_name()
    except ValueError as e:
        raise RuntimeError(f"Configuration error: {e}") from e

    dates_to_fetch: List[datetime] = []
    if exact_match:
        dates_to_fetch.append(end_date)
    else:
        for i in range(days_window, -1, -1):
            current_processing_date = end_date - timedelta(days=i)
            dates_to_fetch.append(current_processing_date)

    all_records: List[Dict[str, Any]] = []

    try:
        for dt_obj in dates_to_fetch:
            s3_key = generate_partitioned_s3_key(
                layer_prefix=app_config.SILVER_PREFIX,
                year=str(dt_obj.year),
                month=f"{dt_obj.month:02d}",
                day_str=dt_obj.strftime("%Y-%m-%d"),
                crop_id=crop_id,
                location_id=location_id,
            )
            df = get_s3_parquet_to_df_if_exists(s3_client, bucket_name, s3_key)

            if df is not None and not df.empty:
                all_records.extend(df.to_dict(orient="records"))

    except ClientError as e:
        # Re-raise ClientError and the router will catch it.
        raise e
    except Exception as e:
        # Catch other unexpected errors during data fetching.
        logger.error(f"Unexpected error fetching GDD data: {e}")
        raise RuntimeError(
            f"An unexpected error occurred while fetching data: {e}"
        ) from e

    return all_records
