from tests.utils.http_variations import assert_response_for_case
from fastapi.testclient import TestClient
from scripts.api import app
import pytest

client = TestClient(app)


@pytest.mark.parametrize(
    "path, case",
    [
        ("/api/", "ok"),
        ("/api/gdd/", "ok"),
        ("/api/weather/", "ok"),
        ("/api/unknown/", "not_found"),
        ("/api/gdd/unknown/", "not_found"),
        ("/api/weather/unknown/", "not_found"),
        ("/api/unauthorized/", "unauthorized"),
        ("/api/gdd/unauthorized/", "unauthorized"),
        ("/api/weather/unauthorized/", "unauthorized"),
        ("/api/forbidden/", "forbidden"),
        ("/api/gdd/forbidden/", "forbidden"),
        ("/api/weather/forbidden/", "forbidden"),
        ("/api/bad_request/", "bad_request"),
        ("/api/gdd/bad_request/", "bad_request"),
        ("/api/weather/bad_request/", "bad_request"),
        ("/api/unprocessable/", "unprocessable"),
        ("/api/gdd/unprocessable/", "unprocessable"),
        ("/api/weather/unprocessable/", "unprocessable"),
        ("/api/server_error/", "server_error"),
        ("/api/gdd/server_error/", "server_error"),
        ("/api/weather/server_error/", "server_error"),
    ],
)
def test_various_endpoints(path, case):
    response = client.get(path)
    assert_response_for_case(response, case)
