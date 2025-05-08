import requests
import pandas as pd
from .config import HEADERS


def fetch_weather_data(lat, lon, location_id):
    url = (
        f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
        f"?lat={lat}&lon={lon}"
    )
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

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
