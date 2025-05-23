import requests
import pandas as pd
import logging # For more informative error messages
from .config import HEADERS


logger = logging.getLogger(__name__)

def fetch_weather_data(lat, lon, location_id):
    url = (
        f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
        f"?lat={lat}&lon={lon}"
    )
    try:
        # Timeout and specific exception handling.
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses.
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch weather data for {location_id} ({lat}, {lon}) from {url}: {e}")
        # Re-raising the exception, so it can be handled upstream if needed.
        raise

    data = response.json()

    times = []
    temps = []

    for entry in data["properties"]["timeseries"]:
        time = entry["time"]
        temp = entry["data"]["instant"]["details"].get("air_temperature")
        if temp is not None:
            times.append(time)
            temps.append(temp)

    df = pd.DataFrame(
        {"timestamp": times, "air_temperature": temps, "location_id": location_id}
    )

    return df
