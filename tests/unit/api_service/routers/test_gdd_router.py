import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime, date

from botocore.exceptions import ClientError


from api_service.main import app

client = TestClient(app)

# Generate today's date string once for consistency in tests.
today_date_str = date.today().strftime("%Y-%m-%d")
GDD_DAYS_WINDOW = 29


# Test cases for the GDD data retrieval endpoint.
@pytest.mark.parametrize(
    "location_id, crop_id, date_str, exact_match, expected_status",
    [
        ("Belagavi", "maize", today_date_str, False, 200),
        ("TestLocation", "TestCrop", today_date_str, True, 200),
        ("AnotherLocation", "AnotherCrop", today_date_str, False, 200),
    ],
)
# Patch the data retrieval service to mock its behavior.
@patch("api_service.routers.gdd_router.data_retrieval_service")
def test_get_gdd_data_success(
    mock_data_service,
    mock_s3_client_app_override,
    location_id,
    crop_id,
    date_str,
    exact_match,
    expected_status,
):
    """Test successful retrieval of GDD data for various parameters."""
    mock_gdd_data = [
        {
            "date": today_date_str,
            "daily_gdd": 15.5,
        },
    ]
    mock_data_service.get_gdd_data_for_period.return_value = mock_gdd_data

    response = client.get(
        f"/gdd/?location_id={location_id}&crop_id={crop_id}&date={date_str}&exact_match={str(exact_match).lower()}"
    )

    assert response.status_code == expected_status
    assert response.json() == mock_gdd_data
    mock_data_service.get_gdd_data_for_period.assert_called_once_with(
        s3_client=mock_s3_client_app_override,
        location_id=location_id,
        crop_id=crop_id,
        end_date=datetime.strptime(date_str, "%Y-%m-%d"),
        exact_match=exact_match,
        days_window=GDD_DAYS_WINDOW,
    )


# Test case for when no GDD data is found (404).
@pytest.mark.parametrize("exact_match", [True, False])
@patch("api_service.routers.gdd_router.data_retrieval_service")
def test_get_gdd_data_not_found(
    mock_data_service, mock_s3_client_app_override, exact_match
):
    """
    Test GDD data retrieval when no data is found for the given criteria (404).
    This test is parameterized for both exact_match True and False.
    """
    mock_data_service.get_gdd_data_for_period.return_value = (
        []
    )  # Service returns empty list.

    response = client.get(
        f"/gdd/?location_id=NoDataLocation&crop_id=NoDataCrop&date={today_date_str}&exact_match={str(exact_match).lower()}"
    )

    assert response.status_code == 404
    assert "GDD data not found" in response.json()["detail"]


def test_get_gdd_data_invalid_date_format(mock_s3_client_app_override):
    """Test request with an invalid date format (400)."""
    response = client.get(
        # mock_s3_client_app_override is included to ensure S3 client is mocked,
        # allowing the app to reach validation logic before any S3 interaction.
        "/gdd/?location_id=Test&crop_id=Test&date=2023/01/01"  # Invalid format.
    )
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]


@patch("api_service.routers.gdd_router.data_retrieval_service")
def test_get_gdd_data_s3_client_error(mock_data_service, mock_s3_client_app_override):
    """Test handling of S3 ClientError (503)."""
    error_response = {
        "Error": {"Code": "TestS3Error", "Message": "S3 connection failed"}
    }
    mock_data_service.get_gdd_data_for_period.side_effect = ClientError(
        error_response, "operation_name"
    )

    response = client.get(
        f"/gdd/?location_id=S3ErrorLocation&crop_id=S3ErrorCrop&date={today_date_str}"
    )

    assert response.status_code == 503
    assert "Error communicating with data storage" in response.json()["detail"]
    # Assert that the service method was called correctly before the error.
    mock_data_service.get_gdd_data_for_period.assert_called_once_with(
        s3_client=mock_s3_client_app_override,
        location_id="S3ErrorLocation",
        crop_id="S3ErrorCrop",
        end_date=datetime.strptime(today_date_str, "%Y-%m-%d"),
        exact_match=False,  # Assuming default is False if not in query for this endpoint.
        days_window=GDD_DAYS_WINDOW,
    )


@patch("api_service.routers.gdd_router.data_retrieval_service")
def test_get_gdd_data_runtime_error(mock_data_service, mock_s3_client_app_override):
    """Test handling of a generic RuntimeError from the service (500)."""
    mock_data_service.get_gdd_data_for_period.side_effect = RuntimeError(
        "Something went wrong in service"
    )  # Simulate a generic error.

    response = client.get(
        f"/gdd/?location_id=RuntimeErrorLocation&crop_id=RuntimeErrorCrop&date={today_date_str}"
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
def test_get_gdd_data_missing_parameters(query_params, mock_s3_client_app_override):
    """Test requests with missing required query parameters (422)."""
    response = client.get(f"/gdd/?{query_params}")
    # mock_s3_client_app_override is included to ensure S3 client is mocked,
    # allowing the app to reach validation logic before any S3 interaction.
    assert response.status_code == 422
