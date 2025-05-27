from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import logging
from datetime import datetime
from botocore.exceptions import ClientError
from botocore.client import BaseClient

# 'api_service' and 'universal' are packages from the project root.
from api_service.dependencies import get_s3_client_dependency
from api_service.services import data_retrieval_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/weather",
    tags=["weather"],
)


@router.get("/")
async def get_weather_data(
    location_id: str = Query(..., description="Identifier for the location."),
    crop_id: str = Query(
        ...,
        description="Identifier for the crop associated with the weather data.",
    ),
    date: str = Query(
        ...,
        description="End date for the 7-day weather data window (YYYY-MM-DD). "
        "Data for this date and the six preceding days will be returned.",
    ),
    s3_client: BaseClient = Depends(get_s3_client_dependency),
) -> JSONResponse:
    """
    Retrieves weather data for a location and crop for the 7-day period ending on the specified date.
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Please use YYYY-MM-DD.",
        )

    try:
        all_records = data_retrieval_service.get_weather_data_for_period(
            s3_client=s3_client,
            location_id=location_id,
            crop_id=crop_id,
            end_date=target_date,
            days_window=6,  # 7 days total.
        )
    except RuntimeError as e:
        # Catch errors from the service indicating internal issues.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal service error: {e}",
        )
    except ClientError as e:
        # Catch S3 client errors and return a 503
        logger.error(f"S3 ClientError in /weather endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error communicating with data storage: {e.__class__.__name__}",
        )

    if not all_records:
        # The service returns an empty list if no data was found for any day.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather data not found for location '{location_id}', crop '{crop_id}' for the 7-day period ending {date}.",
        )

    headers = {"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour.
    return JSONResponse(content=jsonable_encoder(all_records), headers=headers)
