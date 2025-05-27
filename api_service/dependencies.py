from fastapi import HTTPException, status
from botocore.client import BaseClient
import logging

logger = logging.getLogger(__name__)

# 'universal' package from the project root.
try:
    from universal.s3_utils import get_s3_client
except ImportError:
    # This is a critical dependency for the data API.
    logger.critical(
        "Could not import 'get_s3_client' from 'universal.s3_utils'. The data API will not be able to initialize the S3 client."
    )
    get_s3_client = None  # Set to None if import fails.


def get_s3_client_dependency() -> BaseClient:
    """
    FastAPI dependency to provide an S3 client instance.
    Raises HTTPException if the client cannot be initialized.
    """
    if get_s3_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 client utility is not available.",
        )
    try:
        s3_client = get_s3_client()
        if s3_client is None:
            # This case should ideally be caught by the ValueError in get_s3_client.
            raise ValueError("get_s3_client returned None")
        return s3_client
    except ValueError as e:
        logger.critical(f"Error initializing S3 client in dependency: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize S3 client: {e}",
        )
    except Exception as e:
        # Catch any other unexpected errors during client initialization.
        logger.critical(f"Unexpected error during S3 client initialization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during S3 client initialization: {e}",
        )
