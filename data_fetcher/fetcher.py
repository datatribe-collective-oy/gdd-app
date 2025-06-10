"""
Fetches weather data from an external API.

This module is responsible for making HTTP requests to a weather API
(api.met.no) to retrieve forecast data for specified geographical coordinates.
It then processes the JSON response into a pandas DataFrame.
"""

import requests
import pandas as pd
import logging  # For more informative error messages.
from .config import HEADERS

# Initialize logger for this module.
logger = logging.getLogger(__name__)


def fetch_weather_data(lat, lon, location_id):
    """
    Fetches weather data for a given latitude, longitude, and location ID.

    Args:
        lat (float): The latitude of the location.
        lon (float): The longitude of the location.
        location_id (str): A unique identifier for the location.

    Returns:
        pandas.DataFrame: A DataFrame containing 'timestamp', 'air_temperature', and 'location_id'.
                          Timestamps are parsed and converted to UTC.
                          Returns an empty DataFrame if no temperature data is found or if an error occurs.

    Raises:
        requests.exceptions.RequestException: If the API request fails for any reason (e.g., network issue, HTTP error).
    """
    url = (
        f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
        f"?lat={lat}&lon={lon}"
    )
    try:
        # Timeout and specific exception handling.
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx).
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Failed to fetch weather data for {location_id} ({lat}, {lon}) from {url}: {e}"
        )
        # Re-raise the exception so it can be handled by the caller.
        raise

    # Parse the JSON response from the API.
    data = response.json()

    times = []
    temps = []

    for entry in data["properties"]["timeseries"]:
        # Extract time and air temperature from each timeseries entry.
        time = entry["time"]
        temp = entry["data"]["instant"]["details"].get("air_temperature")
        if temp is not None:
            times.append(time)
            temps.append(temp)

    df = pd.DataFrame(
        # Create a DataFrame from the collected times and temperatures.
        {"timestamp": times, "air_temperature": temps, "location_id": location_id}
    )
    if not df.empty:
        # Parse the timestamp strings into datetime objects.
        # Pandas will correctly interpret ISO 8601 with timezone offsets.
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Convert the timestamp to UTC.
        df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")

    return df
