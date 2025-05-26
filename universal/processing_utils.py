from datetime import datetime, timedelta, timezone
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Attempt to import s3_utils for file checking; handle potential circularity or setup issues gracefully.
try:
    from .s3_utils import get_s3_parquet_to_df_if_exists
except ImportError:
    # This might happen if s3_utils itself imports processing_utils, or during initial setup.
    # Assuming that is available. If circular dependencies become an issue,
    # s3_utils might need to be passed in as an argument to functions requiring it.
    get_s3_parquet_to_df_if_exists = None
    logging.warning(
        "universal.s3_utils.get_s3_parquet_to_df_if_exists could not be imported in processing_utils. "
        "Functions relying on it might fail if it's not available at runtime."
    )


def generate_partitioned_s3_key(
    layer_prefix: str,
    year: int | str,
    month: int | str,
    day_str: str,
    crop_id: str,
    location_id: str,
) -> str:
    """
    Generates a standardized S3 object key for partitioned data.
    Example: bronze/year=2023/month=10/crop_id=maize/location_id=Belagavi/data_2025-05-26.parquet
    """
    month_str = f"{int(month):02d}"
    return f"{layer_prefix}/year={year}/month={month_str}/crop_id={crop_id}/location_id={location_id}/data_{day_str}.parquet"


def generate_daily_s3_glob_uri(
    bucket_name: str, layer_prefix: str, target_date: datetime
) -> str:
    """
    Generates a full S3 URI glob pattern for a specific date to read all crop/location data for that day.
    Example: s3://bucket/bronze/year=2023/month=10/crop_id=*/location_id=*/data_2025-05-26.parquet
    """
    year_str = str(target_date.year)
    month_str = f"{target_date.month:02d}"
    date_str = target_date.strftime("%Y-%m-%d")
    key_pattern = f"{layer_prefix}/year={year_str}/month={month_str}/crop_id=*/location_id=*/data_{date_str}.parquet"
    return f"s3://{bucket_name}/{key_pattern}"


def determine_fetcher_processing_dates(
    target_date_str: str | None,
    s3_client: Any,  # Boto3 S3 client.
    bucket_name: str,
    bronze_prefix: str,
    locations_config: Dict[str, Dict[str, tuple]],
    expected_rows_per_day: int = 24,
) -> List[datetime]:
    """
    Determines the list of dates for the data_fetcher to process.
    - If target_date_str is provided, processes only that date.
    - Otherwise, processes today.
    - Additionally, processes yesterday if its data is missing or incomplete.
    """
    dates_to_process: List[datetime] = []

    if target_date_str:
        try:
            specific_date = datetime.strptime(target_date_str, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            logger.info(f"Fetcher will process for specified date: {target_date_str}")
            dates_to_process.append(specific_date)
        except ValueError:
            logger.error(
                f"Invalid date format '{target_date_str}'. Please use YYYY-MM-DD."
            )
            raise  # Re-raise to be handled by the caller.
        return dates_to_process

    # Default behavior: always process today.
    today = datetime.now(timezone.utc)
    dates_to_process.append(today)
    logging.info(f"Fetcher will process for today ({today.strftime('%Y-%m-%d')}).")

    # Check if yesterday needs processing.
    yesterday = today - timedelta(days=1)
    should_process_yesterday = False  # Initialize flag.
    logging.info(
        f"Pre-checking yesterday's ({yesterday.strftime('%Y-%m-%d')}) data status..."
    )

    if get_s3_parquet_to_df_if_exists is None:  # Guard against missing import.
        logging.warning(
            "Cannot check yesterday's data completeness: s3_utils not fully available. Assuming yesterday needs processing."
        )
        should_process_yesterday = True
    else:
        for crop_id, locations in locations_config.items():
            if should_process_yesterday:
                break
            for loc_id in locations.keys():
                key = generate_partitioned_s3_key(
                    bronze_prefix,
                    yesterday.year,
                    yesterday.month,
                    yesterday.strftime("%Y-%m-%d"),
                    crop_id,
                    loc_id,
                )
                df_existing = get_s3_parquet_to_df_if_exists(
                    s3_client, bucket_name, key
                )
                if df_existing is None or len(df_existing) < expected_rows_per_day:
                    logging.info(
                        f"Yesterday's data for {crop_id}-{loc_id} is missing or incomplete. Marking yesterday for processing."
                    )
                    should_process_yesterday = True
                    break

    if should_process_yesterday:
        dates_to_process.append(yesterday)
        logging.info(
            f"Fetcher will also process for yesterday ({yesterday.strftime('%Y-%m-%d')})."
        )
    else:
        logging.info(
            f"Yesterday's ({yesterday.strftime('%Y-%m-%d')}) data appears complete. Skipping full re-process of yesterday."
        )

    return dates_to_process
