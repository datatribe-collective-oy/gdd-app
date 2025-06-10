from tests.utils.http_status import (
    assert_status_ok,
    assert_status_created,
    assert_status_bad_request,
    assert_status_unauthorized,
    assert_status_forbidden,
    assert_status_not_found,
    assert_status_unprocessable,
    assert_status_server_error,
)


def assert_response_for_case(response, case, expected_body=None):
    """
    Asserts the HTTP response status based on a predefined case string.
    Optionally, it can also assert the response body.

    Args:
        response: The HTTP response object (typically from FastAPI's TestClient).
        case (str): A string representing the expected outcome. Supported cases are:
                    "ok", "created", "bad_request", "unauthorized",
                    "not_found", "forbidden", "unprocessable", "server_error".
        expected_body (Optional[Any]): The expected JSON body of the response.
                                       If None, the body is not checked.

    Raises:
        ValueError: If an unknown case string is provided.
    """
    match case:
        case "ok":
            assert_status_ok(response)
        case "created":
            assert_status_created(response)
        case "bad_request":
            assert_status_bad_request(response)
        case "unauthorized":
            assert_status_unauthorized(response)
        case "not_found":
            assert_status_not_found(response)
        case "forbidden":
            assert_status_forbidden(response)
        case "unprocessable":
            assert_status_unprocessable(response)
        case "server_error":
            assert_status_server_error(response)
        case _:
            raise ValueError(f"Oops, sorry! Unknown case: {case}")

    # Checking expected JSON body if it's given.
    if expected_body is not None:
        assert (
            response.json() == expected_body
        ), f"Expected body {expected_body}, got {response.json()}"
