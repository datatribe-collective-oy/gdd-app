"""
This module is responsible for calculating Growing Degree Days (GDD) from bronze layer data.
It uses DuckDB for efficient in-memory processing and S3 access.
"""

import duckdb
import pandas as pd
import logging
import sys

try:
    from universal import config as app_config  # For T_BASE_MAP
except ImportError:
    sys.exit(
        "CRITICAL ERROR: Could not import shared configuration from 'universal.config'. "
        "Please ensure 'gdd-app' is in PYTHONPATH and 'universal/config.py' exists."
    )

logger = logging.getLogger(__name__)


class GDCalculationError(Exception):
    """
    Custom exception raised for errors encountered during the GDD calculation process.
    This helps in distinguishing GDD calculation specific issues from other runtime errors.
    """

    pass


def calculate_daily_gdd(bronze_data_glob_paths: list[str]) -> pd.DataFrame:
    """
    Calculates daily GDD from bronze layer data using DuckDB.
    The function reads Parquet files specified by glob patterns, processes the data to find
    daily minimum and maximum temperatures, and then computes GDD based on crop-specific
    base temperatures.

    Args:
        bronze_data_glob_paths (list[str]): A list of S3 glob patterns pointing to the
                                            bronze layer Parquet files. These files are
                                            expected to contain timestamped temperature readings.

    Returns:
        pd.DataFrame: A Pandas DataFrame containing daily GDD data, including date, crop ID,
                      location ID, min/max/avg temperatures, base temperature used, and the calculated GDD.
                      Returns an empty DataFrame if no data is found or processed.

    Raises:
        GDCalculationError: If any error occurs during DuckDB setup, S3 access configuration,
                            data reading, or GDD query execution.
    """
    logger.info(f"Calculating daily GDD from paths/globs: {bronze_data_glob_paths}")
    con = None
    try:
        t_base_df = pd.DataFrame(
            list(app_config.T_BASE_MAP.items()), columns=["crop_id_map", "t_base"]
        )

        # Initialize a DuckDB in-memory connection.
        con = duckdb.connect()

        # Configure DuckDB's S3 credentials and endpoint. This is necessary for DuckDB to access S3-compatible storage.
        if app_config.STORAGE_BACKEND == "minio":
            if not all(
                [
                    app_config.MINIO_ENDPOINT_URL,
                    app_config.MINIO_ACCESS_KEY,
                    app_config.MINIO_SECRET_KEY,
                ]
            ):
                raise GDCalculationError(
                    "MinIO configuration is incomplete for DuckDB S3 access."
                )  # Ensure all storage details are present.

            endpoint = app_config.MINIO_ENDPOINT_URL
            # DuckDB expects the S3 endpoint without the scheme (http/https).
            s3_endpoint_host_port = endpoint.replace("http://", "").replace(
                "https://", ""
            )
            s3_use_ssl = (
                "true" if endpoint.startswith("https://") else "false"
            )  # Set SSL based on endpoint.

            con.sql(f"SET s3_endpoint='{s3_endpoint_host_port}';")
            con.sql(f"SET s3_access_key_id='{app_config.MINIO_ACCESS_KEY}';")
            con.sql(f"SET s3_secret_access_key='{app_config.MINIO_SECRET_KEY}';")
            con.sql(f"SET s3_use_ssl={s3_use_ssl};")
            con.sql(
                "SET s3_url_style='path';"
            )  # MinIO uses path-style addressing for buckets.
            logger.info("DuckDB S3 settings configured for MinIO.")
        elif app_config.STORAGE_BACKEND == "s3":
            # For AWS S3, DuckDB automatically uses default credential providers.
            logger.info("DuckDB will use default AWS S3 credentials and settings.")

        # Register the base temperature mapping DataFrame as a DuckDB table.
        con.register("t_base_table", t_base_df)

        # Read data for each provided glob pattern individually. By allowing graceful skipping of patterns that match no files,
        # preventing the entire process from failing if one glob is empty.
        all_bronze_dfs = []
        for glob_pattern in bronze_data_glob_paths:
            try:
                logger.info(f"Attempting to read bronze data from: {glob_pattern}")
                # Execute a query to read Parquet files matching the current glob pattern.
                # Hive partitioning is enabled to correctly interpret partitioned data.
                # The filename column is not used downstream, so filename=1 is removed.
                df_single_glob = con.execute(
                    f"SELECT * FROM read_parquet('{glob_pattern}', hive_partitioning=1);"
                ).fetchdf()
                if not df_single_glob.empty:
                    all_bronze_dfs.append(df_single_glob)
                    logger.info(
                        f"Successfully read {len(df_single_glob)} rows from {glob_pattern}"
                    )
            except duckdb.IOException as e:
                # Specifically handle "No files found" errors as warnings and continue.
                if "No files found that match the pattern" in str(e):
                    logger.warning(
                        f"No files found for pattern: {glob_pattern}. Skipping this pattern."
                    )
                else:
                    raise GDCalculationError(
                        f"DuckDB IOException for {glob_pattern}: {e}"
                    ) from e  # Re-raise other IOExceptions as GDCalculationError.

        if not all_bronze_dfs:
            logger.warning(
                "No bronze data found for any of the provided glob patterns. Returning empty DataFrame."
            )
            return pd.DataFrame()  # Return empty DataFrame if no data could be read.

        # Concatenate all pandas DataFrames read from the individual globs.
        # ASSUMPTION: Schemas of the Parquet files are compatible at this point.
        combined_bronze_df = pd.concat(all_bronze_dfs, ignore_index=True)
        # Register the combined DataFrame as a table in DuckDB for processing.
        con.register("bronze_table_for_processing", combined_bronze_df)

        # Define Common Table Expressions (CTEs) for the GDD calculation.
        data_processing_ctes = """
        WITH DailyTemps AS (
            -- This CTE calculates the daily minimum and maximum air temperatures
            -- for each crop_id and location_id by grouping the raw bronze data.
            SELECT
                CAST(timestamp AS DATE) AS "date",
                crop_id,
                location_id,
                MIN(air_temperature) AS t_min_daily,
                MAX(air_temperature) AS t_max_daily
            FROM bronze_table_for_processing
            GROUP BY 1, 2, 3
        )"""

        gdd_calculation_final_select = """
        SELECT
            dt."date",
            -- Selects daily temperature aggregates and joins with base temperatures.
            -- Calculates the average daily temperature (t_avg_daily)
            -- and the Growing Degree Days (daily_gdd).
            dt.crop_id,
            dt.location_id,
            dt.t_min_daily,
            dt.t_max_daily,
            (dt.t_max_daily + dt.t_min_daily) / 2 AS t_avg_daily,
            tb.t_base AS t_base_used,
            GREATEST(0.0, ((dt.t_max_daily + dt.t_min_daily) / 2) - tb.t_base) AS daily_gdd
            -- daily_gdd is calculated as (t_avg_daily - t_base), but not less than 0.
        FROM DailyTemps dt
        JOIN t_base_table tb ON dt.crop_id = tb.crop_id_map;
        """
        logger.info("Calculating GDD from all available bronze data...")

        # Execute the full SQL query (CTEs + final SELECT) and fetch results as a pandas DataFrame.
        silver_df = con.execute(
            f"{data_processing_ctes} {gdd_calculation_final_select}"
        ).fetchdf()
        logger.info(
            f"Successfully calculated GDD. Shape of resulting data: {silver_df.shape}"
        )
        return silver_df
    except Exception as e:
        # Catch any unexpected error during the process and wrap it in GDCalculationError.
        raise GDCalculationError(
            f"Error executing DuckDB query for GDD calculation: {e}"
        ) from e
    finally:
        # Ensure the DuckDB connection is closed in all cases (success or failure).
        if con:
            con.close()
            logger.info("DuckDB connection closed for GDD calculation.")
