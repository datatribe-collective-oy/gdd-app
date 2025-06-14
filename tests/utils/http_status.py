from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


def assert_status_ok(response):
    """Assert that the response status code is 200 OK."""
    assert (
        response.status_code == HTTP_200_OK
    ), f"Expected 200 OK, got {response.status_code} instead."


def assert_status_created(response):
    """Assert that the response status code is 201 Created."""
    assert (
        response.status_code == HTTP_201_CREATED
    ), f"Expected 201 Created, got {response.status_code} instead."


def assert_status_bad_request(response):
    """Assert that the response status code is 400 Bad Request."""
    assert (
        response.status_code == HTTP_400_BAD_REQUEST
    ), f"Expected 400 Bad Request, got {response.status_code} instead."


def assert_status_unauthorized(response):
    """Assert that the response status code is 401 Unauthorized."""
    assert (
        response.status_code == HTTP_401_UNAUTHORIZED
    ), f"Expected 401 Unauthorized, got {response.status_code} instead."


def assert_status_forbidden(response):
    """Assert that the response status code is 403 Forbidden."""
    assert (
        response.status_code == HTTP_403_FORBIDDEN
    ), f"Expected 403 Forbidden, got {response.status_code} instead."


def assert_status_not_found(response):
    """Assert that the response status code is 404 Not Found."""
    assert (
        response.status_code == HTTP_404_NOT_FOUND
    ), f"Expected 404 Not Found, got {response.status_code} instead."


def assert_status_unprocessable(response):
    """Assert that the response status code is 422 Unprocessable Entity."""
    assert (
        response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
    ), f"Expected 422 Unprocessable Entity, got {response.status_code} instead."


def assert_status_server_error(response):
    """Assert that the response status code is 500 Internal Server Error."""
    assert (
        response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    ), f"Expected 500 Internal Server Error, got {response.status_code} instead."
