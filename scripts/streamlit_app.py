import streamlit as st
import os
import requests
from urllib.parse import urljoin, urlencode
from typing import Dict, Any, Optional

## Frontend setup for end-to-end testing.

# Configuration
# Read the API base URL from the environment variable.
# This is expected to be set by the Docker Compose environment (e.g., to http://fastapi:8000).
API_BASE_URL = os.getenv("API_BASE_URL")

if not API_BASE_URL:
    st.error(
        "FATAL: API_BASE_URL environment variable is not set. Please configure the Streamlit service environment."
    )
    # Optionally, you could raise an exception here to halt execution if this is critical:
    # raise ValueError("API_BASE_URL environment variable must be set for the application to function.")


# API Client Functions
def build_api_url(endpoint_path: str, params: Optional[Dict[str, Any]] = None) -> str:
    """
    Constructs the full API URL.

    Args:
        endpoint_path: The specific API endpoint path (e.g., "/weather/", "/gdd/").
        params: A dictionary of query parameters.

    Returns:
        The full URL string.
    """
    # Ensure the endpoint_path starts with a slash if it's a path segment.
    if not endpoint_path.startswith("/") and "://" not in endpoint_path:
        endpoint_path = "/" + endpoint_path

    full_url = urljoin(API_BASE_URL, endpoint_path)

    if params:
        # Filter out None values from params before encoding.
        filtered_params = {k: v for k, v in params.items() if v is not None}
        if filtered_params:
            query_string = urlencode(filtered_params)
            return f"{full_url}?{query_string}"
    return full_url


def fetch_data_from_api(
    endpoint_path: str, params: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """
    Fetches data from the specified API endpoint.
    """
    url = build_api_url(endpoint_path, params)
    st.write(f"Requesting data from: {url}")  # For debugging.
    try:
        response = requests.get(url, timeout=10)  # Added timeout.
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX).
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err} - {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        st.error(
            f"Connection error occurred: {conn_err} - Is the API service running at {API_BASE_URL}?"
        )
    except requests.exceptions.Timeout as timeout_err:
        st.error(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        st.error(f"An unexpected error occurred with the request: {req_err}")
    return None


# Streamlit App UI.
st.title("GDD App JSON Data")

st.header("Fetch Weather Data")
location_id_weather = st.text_input("Location ID (Weather)", "Belagavi")
crop_id_weather = st.text_input("Crop ID (Weather)", "maize")
date_weather = st.text_input("Date (YYYY-MM-DD for Weather)", "2025-05-27")

if st.button("Get Weather Data"):
    weather_params = {
        "location_id": location_id_weather,
        "crop_id": crop_id_weather,
        "date": date_weather,
    }
    weather_data = fetch_data_from_api("/weather/", weather_params)
    if weather_data:
        st.json(weather_data)
        # st.dataframe(pd.DataFrame(weather_data)) # Optionally display as a table.

st.header("Fetch GDD Data")
location_id_gdd = st.text_input("Location ID (GDD)", "Belagavi")
crop_id_gdd = st.text_input("Crop ID (GDD)", "maize")
date_gdd = st.text_input("Date (YYYY-MM-DD for GDD)", "2025-05-27")
exact_match_gdd = st.checkbox("Exact Match for GDD?", True)

if st.button("Get GDD Data"):
    gdd_params = {
        "location_id": location_id_gdd,
        "crop_id": crop_id_gdd,
        "date": date_gdd,
        "exact_match": exact_match_gdd,
    }
    gdd_data = fetch_data_from_api("/gdd/", gdd_params)
    if gdd_data:
        st.json(gdd_data)
        # st.dataframe(pd.DataFrame(gdd_data)) # Optionally display as a table.
