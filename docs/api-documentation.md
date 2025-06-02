# API Documentation

## Overview

This document provides an overview and details of the GDD App Data API endpoints. The API is built using FastAPI and serves weather and Growing Degree Day (GDD) data.

The interactive API documentation (Swagger UI) is available at `/docs` and ReDoc is available at `/redoc` when the API is running.

## Base URL

The base URL for the API endpoints depends on the deployment environment. For local development, it is set on default host/port in `http://localhost:8000`.

## API Tags

The API endpoints are grouped into the following categories:

*   **diagnostic**: Diagnostic endpoints for health checks and testing.
*   **weather**: Endpoints for retrieving weather data.
*   **gdd**: Endpoints for calculating Growing Degree Days (GDD).

## Endpoints

### Diagnostic Endpoints (`/`)

As for now these endpoints are primarily for checking the API's status, and simulation of testing error responses.

#### Root Endpoint

*   **GET `/`**
    *   **Description:** Basic health check endpoint.
    *   **Responses:**
        *   `200 OK`:
            ```json
            {"message": "Data API Root OK."}
            ```

#### Error Simulation Endpoints

These endpoints simulate various HTTP error responses for testing purposes. They are available directly under `/` and also prefixed with `/gdd/` and `/weather/`.

*   **GET `/unauthorized/`, `/gdd/unauthorized/`, `/weather/unauthorized/`**
    *   **Description:** Simulates a `401 Unauthorized` response.
    *   **Responses:**
        *   `401 Unauthorized`:
            ```json
            {"detail": "You must log in."}
            ```

*   **GET `/forbidden/`, `/gdd/forbidden/`, `/weather/forbidden/`**
    *   **Description:** Simulates a `403 Forbidden` response.
    *   **Responses:**
        *   `403 Forbidden`:
            ```json
            {"detail": "Access denied."}
            ```

*   **GET `/bad_request/`, `/gdd/bad_request/`, `/weather/bad_request/`**
    *   **Description:** Simulates a `400 Bad Request` response.
    *   **Responses:**
        *   `400 Bad Request`:
            ```json
            {"detail": "Bad format."}
            ```

*   **GET `/unprocessable/`, `/gdd/unprocessable/`, `/weather/unprocessable/`**
    *   **Description:** Simulates a `422 Unprocessable Entity` response.
    *   **Responses:**
        *   `422 Unprocessable Entity`:
            ```json
            {"detail": "Invalid data."}
            ```

*   **GET `/server_error/`, `/gdd/server_error/`, `/weather/server_error/`**
    *   **Description:** Simulates a `500 Internal Server Error` response.
    *   **Responses:**
        *   `500 Internal Server Error`:
            ```json
            {"detail": "Server broke down."}
            ```

### Weather Endpoints (`/weather`)

Endpoints for retrieving weather data.

#### Get Weather Data

*   **GET `/weather/`**
    *   **Description:** Retrieves weather data for a location and crop for the 7-day period ending on the specified date. Data for the specified date and the six preceding days will be returned. Prequisite: weather data must be available for the specified period in the storage system. 
    *   **Parameters (Query):**
        *   `location_id` (string, **required**): Identifier for the location.
        *   `crop_id` (string, **required**): Identifier for the crop associated with the weather data.
        *   `date` (string, **required**): End date for the 7-day weather data window (YYYY-MM-DD).
    *   **Responses:**
        *   `200 OK`: Returns a JSON array of weather records for the specified period.
            *   **Content Type:** `application/json`
            *   **Schema:** JSON `array` of objects.
            *   **Headers:** `Cache-Control: public, max-age=3600`

#### Example Query for Weather Data

To query the weather endpoint, you'll need to provide `location_id`, `crop_id`, and a `date`.

*   **`location_id` and `crop_id`**: Refer to the `data_fetcher/config.py` file for available locations and their associated crops (e.g., "Belagavi" for "maize", "Kitui" for "sorghum").
*   **`date`**: The end date (YYYY-MM-DD) for the 7-day data window.

**Example `curl` command:**

Get weather data for maize in Belagavi for the 7-day period ending May 26th, 2025:
```bash
curl -X GET "http://localhost:8000/weather/?location_id=Belagavi&crop_id=maize&date=2025-05-26"
```

**Changeable parts:**
*   `location_id=Belagavi`: Change `Belagavi` to another valid location.
*   `crop_id=maize`: Change `maize` to the crop associated with your chosen `location_id`.
*   `date=2025-05-26`: Change to your desired end date.

The API will return a JSON array of weather records for the specified date and the six preceding days.

**Example JSON response (a small fraction of example data):**

```json
  {
    "timestamp": "2025-05-26T23:00:00+00:00",
    "air_temperature": 20.6,
    "location_id": "Belagavi",
    "crop_id": "maize"
  }
```


### GDD Endpoints (`/gdd`)

Endpoints for calculating and retrieving Growing Degree Days (GDD).

#### Get GDD Data

*   **GET `/gdd/`**
    *   **Description:** Retrieves GDD data for a location and crop for a period ending on the specified date. Can fetch for a single exact date or a 30-day window. Prequisite: weather data must be available for the specified period in the storage system.
    *   **Parameters (Query):**
        *   `location_id` (string, **required**): Identifier for the location.
        *   `crop_id` (string, **required**): Identifier for the crop.
        *   `date` (string, **required**): End date for the GDD data window (YYYY-MM-DD). Defaults to a 30-day window. Use `exact_match=true` for a single day.
        *   `exact_match` (boolean, optional, default: `false`): If true, fetches GDD data only for the specified `date`. Otherwise, fetches for a 30-day window ending on `date`.
    *   **Responses:**
        *   `200 OK`: Returns a JSON array of GDD records for the specified period.
            *   **Content Type:** `application/json`
            *   **Schema:** JSON `array` of GDD record objects.
            *   **Headers:** `Cache-Control: public, max-age=3600`
        

#### Example Queries for GDD Data

To query the GDD endpoint, you'll need `location_id`, `crop_id`, and a `date`. You can also specify `exact_match`.

*   **`location_id` and `crop_id`**: Refer to `data_fetcher/config.py` for available locations and crops.
*   **`date`**: The end date (YYYY-MM-DD) for the data window.
*   **`exact_match`**: Set to `true` for a single day's data, or `false` (or omit) for a 30-day window.

**Example `curl` command (30-day window):**

Get GDD data for sorghum in Kitui for the 30-day period ending May 26th, 2025:
```bash
curl -X GET "http://localhost:8000/gdd/?location_id=Belagavi&crop_id=maize&date=2025-05-26"
```

**Example `curl` command (exact date):**

Get GDD data for sorghum in Belagavi for May 26th, 2025, only:
```bash
curl -X GET "http://localhost:8000/gdd/?location_id=Belagavi&crop_id=maize&date=2025-05-26&exact_match=true"
```

**Changeable parts:**
*   `location_id=Belagavi`: Change to another valid location.
*   `crop_id=maize`: Change to the crop associated with your chosen `location_id`.
*   `date=2025-05-26`: Change to your desired end date.
*   `exact_match=true`: Change to `false` or omit for the 30-day window.

**Example JSON response:** 
        
```json
  {
    "date": "2025-05-26T00:00:00",
    "crop_id": "maize",
    "location_id": "Belagavi",
    "t_min_daily": 20.3,
    "t_max_daily": 21.6,
    "t_avg_daily": 20.95,
    "t_base_used": 10,
    "daily_gdd": 10.95
  }
```

## Related Documentation

For more information on specific aspects of the architecture, refer to the following documentation:

- [System Architecture](./system-architecture.md) - Overall system design and component interactions.
- [Data Flow and Modeling](./data-flow-and-modeling.md) - Information on data processing and storage.
- [API Documentation](./api-documentation.md) - API endpoint specifications and usage.
- [Yr.no API Compliance](./yrno-api-compliance.md) - Compliance with the Yr.no Weather API terms of service.
- [AWS Services](./aws-services.md) - Details on AWS infrastructure and IAM configurations.
- [Containerisation](./containerisation.md) - Information on Docker container security and isolation.
- [Reverse Proxy](./reverse-proxy.md) - Details on Nginx configuration and access controls.
- [Security Architecture](./security-architecture.md) - Overview of the security measures and design.
- [Testing Plan](./testing-plan.md) - Outline of the testing strategy, including security testing.

These documents provide further context and detail on implementation throughout the system.
