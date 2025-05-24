from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import boto3
import io
import sys  

from botocore.client import Config


try:
    from universal import config as app_config
except ImportError:
    sys.exit(
        "CRITICAL ERROR: Could not import shared configuration from 'universal.config'. "
        "Please ensure 'gdd-app' is in PYTHONPATH and 'universal/config.py' exists."
    )


def get_s3_client():
    if app_config.STORAGE_BACKEND == "minio":
        if not all(
            [
                app_config.MINIO_ENDPOINT_URL,
                app_config.MINIO_ACCESS_KEY,
                app_config.MINIO_SECRET_KEY,
            ]
        ):
            raise ValueError(
                "MinIO configuration (MINIO_ENDPOINT_URL, MINIO_ACCESS_KEY, MINIO_SECRET_KEY) "
                "is incomplete in the shared app_config."
            )

        use_ssl = app_config.MINIO_ENDPOINT_URL.startswith("https://")
            # Auto-detect http/https.
            # For local MinIO (often http), verify=False is needed to avoid SSL errors.
            # If https with valid cert, verify=True, or None (default).
            # If https with self-signed cert, verify=False is needed.

        # Set to False explicitly if using http or self-signed https for MinIO.
        verify_ssl = (
            None if use_ssl else False
        )  
        
        return boto3.client(
            "s3",
            endpoint_url=app_config.MINIO_ENDPOINT_URL,
            aws_access_key_id=app_config.MINIO_ACCESS_KEY,
            aws_secret_access_key=app_config.MINIO_SECRET_KEY,
            # region_name could be added from app_config if needed, e.g., app_config.MINIO_REGION.
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"}, # Use path-style addressing for MinIO.
            use_ssl=use_ssl,
            verify=verify_ssl,
        )
    elif app_config.STORAGE_BACKEND == "s3":
        return boto3.client("s3")
    else:
        raise ValueError(
            f"Unsupported STORAGE_BACKEND: '{app_config.STORAGE_BACKEND}' in shared app_config. "
            "Supported options are 'minio' or 's3'."
        )


def save_partitioned_parquet_s3(df, bucket, base_prefix="bronze"):
    df["year"] = pd.to_datetime(df["timestamp"]).dt.year
    df["month"] = pd.to_datetime(df["timestamp"]).dt.month

    year = df["year"].iloc[0]
    month = f"{df['month'].iloc[0]:02d}"
    location = df["location_id"].iloc[0]
    crop = df["crop_id"].iloc[0]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    key = (
        f"{base_prefix}/year={year}/month={month}/"
        f"crop_id={crop}/location_id={location}/"
        f"data_{today}.parquet"
    )

    # Write Parquet to memory buffer.
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)

    s3 = get_s3_client()
    s3.upload_fileobj(buffer, bucket, key)

    print(f"Saved data to s3://{bucket}/{key}")
    return f"s3://{bucket}/{key}"
