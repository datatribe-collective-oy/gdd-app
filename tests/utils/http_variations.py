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

    # Checking expected JSON body if it's given
    if expected_body is not None:
        assert (
            response.json() == expected_body
        ), f"Expected body {expected_body}, got {response.json()}"
