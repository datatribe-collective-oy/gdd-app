import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base temperature map for different crops, in celsius.
T_BASE_MAP = {
    "maize": 10.0,  
    "sorghum": 10.0,  
    # Add other crops if needed.
}

# Storage Configuration Options: 'minio', 's3'. Default to 'minio'.
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND")

#  MinIO Configuration. Used if STORAGE_BACKEND is 'minio'.
MINIO_ENDPOINT_URL = os.getenv("MINIO_ENDPOINT_URL")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_DATA_BUCKET_NAME = os.getenv("MINIO_DATA_BUCKET_NAME")


AWS_S3_DATA_BUCKET_NAME = os.getenv(
    "AWS_S3_DATA_BUCKET_NAME"
)


BRONZE_PREFIX = os.getenv("BRONZE_PREFIX", "bronze")
SILVER_PREFIX = os.getenv("SILVER_PREFIX", "silver")
GOLD_PREFIX = os.getenv("GOLD_PREFIX", "gold")
