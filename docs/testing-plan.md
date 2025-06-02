# Testing Plan

This document outlines the testing strategy for the GDD Timing System application, covering unit tests, integration tests, and CI/CD workflows.

## Testing Philosophy

The testing approach is guided by these key principles:

- **Pragmatic Testing**: Tests are strategically introduced based on component criticality, with testing efforts prioritized for core functionality.
- **Comprehensive manual testing**: Manual testing is performed throughout development to validate functionality.
- **Test pyramid**: The testing strategy follows a hierarchical approach with more unit tests than integration tests, and more integration tests than end-to-end tests.
- **Mocking external dependencies**: External services are replaced with mock objects in unit tests.
- **Real dependencies for integration tests**: TestContainers will be utilized for realistic integration testing.
- **Continuous testing**: Tests are automatically executed on every push and pull request.

## Test Types

### Unit Tests

Unit tests are focused on testing individual components in isolation with mocked dependencies:

- **API Endpoint Testing**: FastAPI endpoints are tested for:

  - Successful responses (HTTP 200).
  - Error handling across various status codes (400, 401, 403, 404, 422, 500, 503).
  - Input validation through FastAPI's Query parameters.
  - Parameter handling for missing or invalid parameters.

- **Service Layer Testing (Planned)**: While the `data_fetcher` and `gdd_counter` modules have undergone extensive manual testing with MinIO to verify their core functionality, automated unit tests for these core data processing and business logic components are planned and will be prioritized. This includes:

  - **Data Fetcher (`data_fetcher` module)**:
    - Testing `fetcher.py` for correct API interaction and data transformation.
    - Testing `validator.py` to ensure data validation rules are applied correctly (e.g., checking for required columns, data types, realistic ranges, duplicates as seen in `validate_weather_data`).
    - Testing `saver.py` for correct data partitioning and saving logic.
    - Testing the main orchestration logic in `data_fetcher/main.py`, including date determination, S3 key generation, and the merging logic for existing and newly fetched data.
  - **GDD Counter (`gdd_counter` module)**:
    - Testing `calculator.py` for accurate GDD calculations, including DuckDB query logic and handling of `T_BASE_MAP`.
    - Testing `processor.py` for correct determination of input paths, invocation of the calculator, and orchestration of saving results.
    - Testing `writer.py` for correct saving of GDD results to the silver layer.
  - Mocking dependencies such as external APIs (for `data_fetcher`) and S3 interactions.

- **Test Implementation Details**:
  - Pytest fixtures are utilized for dependency injection.
  - S3/MinIO clients are mocked via the `mock_s3_client_app_override` fixture.
  - Tests are parameterized with pytest.mark.parametrize for different scenarios.
  - Error cases are comprehensively tested, including S3 ClientErrors and RuntimeErrors.

### Integration Tests (Planned)

Integration tests will be implemented to validate that components work together correctly:

- **TestContainers Strategy**:

  - The [testcontainers-python](https://github.com/testcontainers/testcontainers-python) library will be utilized.
  - Actual containers will be spun up for dependencies:
    - MinIO container for object storage.
    - PostgreSQL container for Airflow metadata testing.

- **Integration Test Focus**:

  - API endpoints with real storage backends.
  - Data flow between services.
  - File storage operations with actual MinIO.

- **Implementation Plan**:
  1. Pytest fixtures will be created for TestContainers initialization.
  2. Container networking will be established for inter-service communication.
  3. Test data seeding will be implemented for MinIO.
  4. Integration tests will be written to validate end-to-end flows.

### End-to-End Testing (Future)

End-to-end testing will be implemented to validate the entire application stack:

- The complete application will be spun up using docker compose.
- User workflows will be tested through the API and UI (Streamlit).
- Data processing pipelines will be validated end-to-end.

## CI/CD Integration

Tests are integrated into the CI/CD pipeline:

- **Current Implementation**:

  - GitHub Actions workflow is triggered on pushes to main and pull requests.
  - Ruff linting is executed to ensure code quality.
  - Unit tests are run via pytest.

- **Planned Enhancements**:
  - Integration tests with TestContainers will be added to the CI pipeline.
  - Test coverage reporting will be implemented.
  - Performance testing for critical endpoints will be introduced.

## Running Tests

- **Unit tests**: `poetry run pytest tests/unit`
- **Integration tests**: `poetry run pytest tests/integration` (planned)
- **All tests**: `poetry run pytest` (runs both unit and integration tests)
- **With coverage**: `poetry run pytest --cov=api_service tests/`
