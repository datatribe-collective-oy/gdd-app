import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime, date

from botocore.exceptions import ClientError

# FastAPI app instance is in api_service.main.
from api_service.main import app

client = TestClient(app)

# Generate today's date string once for consistent date usage in tests.
today_date_str = date.today().strftime("%Y-%m-%d")
WEATHER_DAYS_WINDOW = 6


@pytest.mark.parametrize(
    "location_id, crop_id, date_str, expected_status",
    [
        ("Belagavi", "maize", today_date_str, 200),
        ("TestLocation", "TestCrop", today_date_str, 200),
    ],
)
@patch("api_service.routers.weather_router.data_retrieval_service")
def test_get_weather_data_success(
    mock_data_service,  # Patched service.
    mock_s3_client_app_override,  # Fixture for S3 client mock.
    location_id,
    crop_id,
    date_str,
    expected_status,
):
    """Test successful retrieval of weather data for various parameters."""
    mock_data = [
        {
            "timestamp": f"{today_date_str}T10:00:00Z",
            "temperature": 25.0,
        },  # Using today_date_str.
        {
            "timestamp": f"{today_date_str}T11:00:00Z",
            "temperature": 26.0,
        },  # Using today_date_str.
    ]
    mock_data_service.get_weather_data_for_period.return_value = mock_data

    response = client.get(
        f"/weather/?location_id={location_id}&crop_id={crop_id}&date={date_str}"
    )

    assert response.status_code == expected_status
    assert response.json() == mock_data
    mock_data_service.get_weather_data_for_period.assert_called_once_with(
        s3_client=mock_s3_client_app_override,  # Use the mock from the fixture.
        location_id=location_id,
        crop_id=crop_id,
        end_date=datetime.strptime(date_str, "%Y-%m-%d"),
        days_window=WEATHER_DAYS_WINDOW,
    )


@patch("api_service.routers.weather_router.data_retrieval_service")
def test_get_weather_data_not_found(mock_data_service, mock_s3_client_app_override):
    """Test case where no weather data is found (404)."""
    mock_data_service.get_weather_data_for_period.return_value = (
        []
    )  # Service returns empty list.

    response = client.get(
        f"/weather/?location_id=NoDataLocation&crop_id=NoDataCrop&date={today_date_str}"
    )

    assert response.status_code == 404
    assert "Weather data not found" in response.json()["detail"]


def test_get_weather_data_invalid_date_format():
    """Test request with an invalid date format (400)."""
    response = client.get(
        "/weather/?location_id=Test&crop_id=Test&date=2023/01/01"  # Invalid date format.
    )
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]


@patch("api_service.routers.weather_router.data_retrieval_service")
def test_get_weather_data_s3_client_error(
    mock_data_service, mock_s3_client_app_override
):
    """Test handling of S3 ClientError (503)."""
    # Simulate ClientError from botocore.
    error_response = {
        "Error": {"Code": "TestS3Error", "Message": "S3 connection failed"}
    }
    mock_data_service.get_weather_data_for_period.side_effect = ClientError(
        error_response, "operation_name"
    )

    response = client.get(
        f"/weather/?location_id=S3ErrorLocation&crop_id=S3ErrorCrop&date={today_date_str}"
    )

    assert response.status_code == 503
    assert "Error communicating with data storage" in response.json()["detail"]


@patch("api_service.routers.weather_router.data_retrieval_service")
def test_get_weather_data_runtime_error(mock_data_service, mock_s3_client_app_override):
    """Test handling of a generic RuntimeError from the service (500)."""
    mock_data_service.get_weather_data_for_period.side_effect = RuntimeError(
        "Something went wrong in service"
    )  # Simulate a generic error.

    response = client.get(
        f"/weather/?location_id=RuntimeErrorLocation&crop_id=RuntimeErrorCrop&date={today_date_str}"
    )

    assert response.status_code == 500
    assert "Internal service error" in response.json()["detail"]


@pytest.mark.parametrize(
    "query_params",
    [
        (f"crop_id=maize&date={today_date_str}"),  # Missing location_id.
        (f"location_id=Belagavi&date={today_date_str}"),  # Missing crop_id.
        ("location_id=Belagavi&crop_id=maize"),  # Missing date.
    ],
)
def test_get_weather_data_missing_parameters(query_params):
    """Test requests with missing required query parameters (422)."""
    response = client.get(f"/weather/?{query_params}")
    assert response.status_code == 422  # Unprocessable Entity for missing params.
