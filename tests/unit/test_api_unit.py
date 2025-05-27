from tests.utils.http_variations import assert_response_for_case
from fastapi.testclient import TestClient
import pytest
from api_service.main import app  # Main FastAPI application

client = TestClient(app)


@pytest.mark.parametrize(
    "path, case",
    [
        ("/", "ok"),
        ("/unknown/", "not_found"),
        ("/gdd/unknown/", "not_found"),
        ("/weather/unknown/", "not_found"),
        ("/unauthorized/", "unauthorized"),
        ("/gdd/unauthorized/", "unauthorized"),
        ("/weather/unauthorized/", "unauthorized"),
        ("/forbidden/", "forbidden"),
        ("/gdd/forbidden/", "forbidden"),
        ("/weather/forbidden/", "forbidden"),
        ("/bad_request/", "bad_request"),
        ("/gdd/bad_request/", "bad_request"),
        ("/weather/bad_request/", "bad_request"),
        ("/unprocessable/", "unprocessable"),
        ("/gdd/unprocessable/", "unprocessable"),
        ("/weather/unprocessable/", "unprocessable"),
        ("/server_error/", "server_error"),
        ("/gdd/server_error/", "server_error"),
        ("/weather/server_error/", "server_error"),
    ],
)
def test_various_endpoints(path, case):
    """
    Tests various simple GET endpoints to ensure they return expected HTTP status codes.
    This test is parameterized to cover different paths and their corresponding status cases.
    """
    response = client.get(path)
    assert_response_for_case(response, case)
