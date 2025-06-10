"""
Configuration settings for the data_fetcher component.

This module contains constants used throughout the data fetching process,
such as API headers and predefined geographical locations for weather data retrieval.
"""

# Standard headers to be used for making HTTP requests to the weather API.
HEADERS = {"User-Agent": "gdd-app/0.1 (eveliinahampus@gmail.com)"}

# Dictionary defining locations in India for maize crop weather data.
# Each key is a location name, and the value is a tuple of (latitude, longitude).
MAIZE_INDIA_LOCATIONS = {
    "Belagavi": (15.85, 74.50),
    "Chhindwara": (22.06, 78.94),
    "Jalgaon": (21.01, 75.56),
    "Perambalur": (11.23, 78.88),
    "Katihar": (25.54, 87.58),
}

# Dictionary defining locations in Kenya for sorghum crop weather data.
# Each key is a location name, and the value is a tuple of (latitude, longitude).
SORGHUM_KENYA_LOCATIONS = {
    "Kitui": (-1.38, 38.01),
    "Machakos": (-1.52, 37.27),
    "Makueni": (-2.24, 37.96),
    "Tharaka_Nithi": (-0.30, 37.93),
    "Siaya": (0.06, 34.29),
}
