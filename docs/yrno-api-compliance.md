# Yr.no API Compliance

## Overview

This document outlines how the GDD App adheres to the [Terms of Service for the Yr.no Weather API](https://developer.yr.no/doc/TermsOfService/).

## 1. Identification

**Requirement:** Applications must identify themselves with a custom `User-Agent` string in all HTTP requests, including a way to be contacted.

**Compliance:**
- The `data_fetcher` component, responsible for all API calls to Yr.no, uses a compliant `User-Agent` string.
- This is defined in `data_fetcher/config.py` as:
  ```python
  HEADERS = {"User-Agent": "gdd-app/0.1 (eveliinahampus@gmail.com)"}
  ```
- This header is included in every request made by `data_fetcher/fetcher.py`.

## 2. Caching and Request Frequency

**Requirement:** Cache data, respect cache headers, and do not request data already possessed. Do not poll for data more than once every 10 minutes.

**Compliance:**
- **Request Frequency Management:** The GDD App does not trigger API requests directly from user interactions. Instead, data fetching is managed by scheduled Apache Airflow DAGs (as detailed in the System Architecture).
  - This batch-oriented approach ensures that requests to the Yr.no API are made periodically (e.g., daily or twice daily) rather than in response to individual user actions, inherently controlling the polling frequency to well within acceptable limits.
- **Data Storage:** Raw weather data fetched from Yr.no is stored in an S3-compatible object store (MinIO locally, AWS S3 in production) in a "bronze" layer. This data is then used for internal processing (GDD calculation).
- **Caching Headers:** While the `data_fetcher/fetcher.py` does not currently implement client-side HTTP caching mechanisms (like `ETag` or `If-Modified-Since`), the nature of the "Locationforecast" API (providing changing forecast data) means that periodic refetching is necessary. The primary control for request volume is the Airflow DAG scheduling.

## 3. Data Usage and Redistribution

**Requirement:** Do not redistribute raw data from the API. You can use the data to create your own services and visualizations.

**Compliance:**
- The GDD App fetches weather data for internal processing to calculate Growing Degree Days (GDD).
- Raw weather data is stored in a private S3 bucket and is not publicly redistributed.
- The application serves processed GDD data. It also serves recent weather data (e.g., temperature, timestamps), fetched from the application's S3 bronze layer, via its API (`FastAPI`) for display within its own frontend (`Streamlit`). This usage is to provide weather context as part of the GDD application's service, aligning with the terms that allow using data to create specific services and visualizations, rather than general redistribution of raw API data.

## 4. Error Handling

**Compliance:**
- The `data_fetcher/fetcher.py` module includes error handling for API requests, such as checking for HTTP error statuses (`response.raise_for_status()`) and catching network-related exceptions. This helps in managing API interactions robustly.

By adhering to these practices, the GDD App aims to be a responsible consumer of the Yr.no API services.

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