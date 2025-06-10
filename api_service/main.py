from fastapi import FastAPI
import uvicorn
import logging

# Assuming 'api_service' and 'universal' are packages accessible from the project root.
from api_service.routers import (
    weather_router,
    gdd_router,
    diagnostic_router,
)
from universal import config as app_config

# Configure basic logging.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GDD App Data API",
    description="API for accessing weather and GDD data for the GDD App.",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "diagnostic",
            "description": "Diagnostic endpoints for health checks and testing.",
        },
        {
            "name": "weather",
            "description": "Endpoints for retrieving weather data.",
        },
        {
            "name": "gdd",
            "description": "Endpoints for calculating Growing Degree Days (GDD).",
        },
    ],
    docs_url="/docs",
)

# Include routers.
app.include_router(diagnostic_router.router)  # Includes "/" and test routes.
app.include_router(weather_router.router)
app.include_router(gdd_router.router)


# Run API by uvicorn, local development.
if __name__ == "__main__":
    logger.info("Starting Uvicorn server for GDD App Data API...")
    logger.info(f"Storage Backend: {app_config.STORAGE_BACKEND}")
    if app_config.STORAGE_BACKEND == "minio":
        logger.info(f"MinIO Endpoint: {app_config.MINIO_ENDPOINT_URL}")
        logger.info(f"MinIO Bucket: {app_config.MINIO_DATA_BUCKET_NAME}")
    # if get_s3_client is not None:
    #     try:
    #         # Attempt to get client to see if config is valid
    #         get_s3_client()
    #     except (ValueError, Exception) as e:
    #          print(f"CRITICAL RUNTIME WARNING: S3 client failed to initialize at startup check: {e}. Endpoints /weather and /gdd will fail.")

    logger.info(f"AWS S3 Bucket: {app_config.AWS_S3_DATA_BUCKET_NAME}")
    logger.info(f"Bronze Prefix: {app_config.BRONZE_PREFIX}")
    logger.info(f"Silver Prefix: {app_config.SILVER_PREFIX}")
    logger.info(f"Gold Prefix: {app_config.GOLD_PREFIX}")

    uvicorn.run(app, host="localhost", port=8000)
