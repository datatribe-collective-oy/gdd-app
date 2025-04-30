from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR
)

def assert_status_ok(response):
    assert response.status_code == HTTP_200_OK, f"Expected 200 OK, got {response.status_code} instead."

def assert_status_created(response):
    assert response.status_code == HTTP_201_CREATED, f"Expected 201 Created, got {response.status_code} instead."

def assert_status_bad_request(response):
    assert response.status_code == HTTP_400_BAD_REQUEST, f"Expected 400 Bad Request, got {response.status_code} instead."

def assert_status_unauthorized(response):
    assert response.status_code == HTTP_401_UNAUTHORIZED, f"Expected 401 Unauthorized, got {response.status_code} instead."

def assert_status_forbidden(response):
    assert response.status_code == HTTP_403_FORBIDDEN, f"Expected 403 Forbidden, got {response.status_code} instead."

def assert_status_not_found(response):
    assert response.status_code == HTTP_404_NOT_FOUND, f"Expected 404 Not Found, got {response.status_code} instead."

def assert_status_unprocessable(response):
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY, f"Expected 422 Unprocessable Entity, got {response.status_code} instead."

def assert_status_server_error(response):
    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR, f"Expected 500 Internal Server Error, got {response.status_code} instead."
