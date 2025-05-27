import pytest
from unittest.mock import MagicMock

from api_service.main import app
from api_service.dependencies import get_s3_client_dependency


@pytest.fixture
def mock_s3_client_app_override():
    """
    Pytest fixture to mock the S3 client dependency for the FastAPI app.

    This fixture creates a MagicMock for the S3 client, overrides the
    `get_s3_client_dependency` in the FastAPI application (`app`),
    and yields the mock client for use in tests. It ensures that
    the original dependency overrides are restored after the test execution.
    """
    mock_s3_client = MagicMock()
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_s3_client_dependency] = lambda: mock_s3_client
    yield mock_s3_client
    app.dependency_overrides = original_overrides
