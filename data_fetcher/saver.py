from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import boto3
import io
from dotenv import load_dotenv
import os


load_dotenv()  # Take environment variables from .env for dev

def get_s3_client():
    if os.getenv("AWS_EXECUTION_ENV"):
        return boto3.client('s3')
    else:
        return boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )



def save_partitioned_parquet_s3(df, bucket, base_prefix="bronze/weather_data"):
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

    # Write Parquet to memory buffer
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)

    s3 = get_s3_client()  
    s3.upload_fileobj(buffer, bucket, key)

    print(f"Saved data to s3://{bucket}/{key}")