from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import boto3
import io
from dotenv import load_dotenv
import os
from botocore.client import Config 


load_dotenv()  # Take environment variables from .env for dev.

def get_s3_client():
    s3_endpoint_url = os.getenv("S3_ENDPOINT_URL")
    aws_execution_env = os.getenv("AWS_EXECUTION_ENV")

    if aws_execution_env:
        # Running in an AWS managed environment (e.g., Lambda, Fargate).
        # Credentials are automatically provided by the environment/IAM role.
        return boto3.client("s3")
    
    elif s3_endpoint_url:
        # Running in a local or non-AWS environment with a custom S3 endpoint.
        access_key = os.getenv("MINIO_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
        secret_key = os.getenv("MINIO_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
        # Default region is set to "eu-north-1" if not specified in the env file.
        raw_region = os.getenv("AWS_DEFAULT_REGION", "eu-north-1")
        # Clean the region string: take part before any '#' and strip whitespace.
        region = raw_region.split('#')[0].strip()
        if not region: # If region is empty after split, set to default.
            region = "eu-north-1" # Fallback to default region.

        if not access_key or not secret_key:
            raise ValueError(
                "For S3-compatible storage (e.g., MinIO), please set EITHER "
                "MINIO_ACCESS_KEY_ID and MINIO_SECRET_ACCESS_KEY OR "
                "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in the env file."
            )
 
        return boto3.client(
            "s3",
            endpoint_url=s3_endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"} # Often needed for MinIO.
            ),
            use_ssl=s3_endpoint_url.startswith("https://"), # Auto-detect http/https
            # For local MinIO (often http), verify=False is needed to avoid SSL errors.
            # If https with valid cert, verify=True, or None (default).
            # If https with self-signed cert, verify=False is needed.
            verify=False if not s3_endpoint_url.startswith("https://") else None
        )
    
    else:
        # Fallback to real AWS S3 using explicitly set AWS credentials.
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_DEFAULT_REGION")

        if not aws_access_key_id or not aws_secret_access_key or not aws_region:
            raise ValueError(
                "For AWS S3, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION must be set "
                "if not running in an AWS_EXECUTION_ENV and S3_ENDPOINT_URL is not provided."
            )
        
        return boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
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