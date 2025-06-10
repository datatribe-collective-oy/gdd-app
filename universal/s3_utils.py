import boto3
import io
import pandas as pd
import logging
from botocore.exceptions import ClientError
from botocore.client import Config

try:
    # s3_utils.py is in the same package 'universal' as config.py
    from . import config as app_config
except ImportError as e:
    # Instead of sys.exit, re-raise the ImportError.
    # This allows the module importing s3_utils to handle the failure.
    raise ImportError(
        "CRITICAL ERROR: Could not import shared configuration from 'universal.config'. "
        "This is a dependency for 'universal.s3_utils'."
    ) from e

logger = logging.getLogger(__name__)


def get_s3_client():
    """
    Creates and returns an S3 client configured based on the shared app_config.
    Supports 'minio' and 's3' backends.
    """
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
        verify_ssl = (  # Use verify=False for local http or self-signed https.
            None if use_ssl else False
        )  # For local MinIO with http or self-signed https.

        return boto3.client(
            "s3",
            endpoint_url=app_config.MINIO_ENDPOINT_URL,
            aws_access_key_id=app_config.MINIO_ACCESS_KEY,
            aws_secret_access_key=app_config.MINIO_SECRET_KEY,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
            use_ssl=use_ssl,
            verify=verify_ssl,
        )
    elif app_config.STORAGE_BACKEND == "s3":
        return boto3.client("s3")
    else:
        raise ValueError(  # This should be caught by the dependency.
            f"Unsupported STORAGE_BACKEND: '{app_config.STORAGE_BACKEND}' in shared app_config. "
            "Supported options are 'minio' or 's3'."
        )


def s3_object_exists(s3_client, bucket_name: str, object_key: str) -> bool:
    """
    Checks if an object exists in an S3 bucket.

    Args:
        s3_client: Initialized Boto3 S3 client.
        bucket_name: Name of the S3 bucket.
        object_key: Key of the object.

    Returns:
        True if the object exists, False otherwise.

    Raises:
        ClientError: For issues other than '404 Not Found',
        such as permissions errors or bucket not found.
    """
    try:
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        return True
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "404":
            return False
        else:
            # Re-raise other errors, such as permissions issues or bucket not found.
            raise


def get_s3_parquet_to_df_if_exists(
    s3_client, bucket_name: str, object_key: str
) -> pd.DataFrame | None:
    """
    Checks if a Parquet object exists in S3 and loads it into a Pandas DataFrame if it does.

    Args:
        s3_client: Initialized Boto3 S3 client.
        bucket_name: Name of the S3 bucket.
        object_key: Key of the Parquet object.

    Returns:
        pd.DataFrame if the object exists and is successfully read, None otherwise.
    """
    if s3_object_exists(s3_client, bucket_name, object_key):
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            parquet_file = io.BytesIO(response["Body"].read())
            df = pd.read_parquet(parquet_file)  # Read the parquet data.
            logger.info(
                f"Successfully loaded existing Parquet file from s3://{bucket_name}/{object_key}"
            )
            return df
        except Exception as e:
            # Log the error but return None so the calling function knows it failed.
            logger.warning(
                f"Found object s3://{bucket_name}/{object_key} but failed to read it as Parquet: {e}. Will proceed as if no existing data was found."
            )
            return None
    return None
