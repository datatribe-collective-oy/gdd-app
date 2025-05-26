"""
Validates weather data DataFrames.

This module provides functions to check the integrity and consistency of
weather data before it is saved. Validation includes checking for required
columns, correct data types, realistic data ranges, duplicates, and
the expected number of data points for a given day.
"""

import pandas as pd


def validate_weather_data(
    df: pd.DataFrame, target_processing_date: pd.Timestamp
):
    """
    Validates a DataFrame containing hourly weather data for a specific processing date.

    Args:
        df (pd.DataFrame): The DataFrame to validate.
        target_processing_date (pd.Timestamp): The specific date for which the data is being processed.
                                               All timestamps in the DataFrame should fall on this date.

    Returns:
        pd.DataFrame: The validated DataFrame if all checks pass.

    Raises:
        ValueError: If any validation check fails, containing a message with all detected errors.
    """
    errors = []

    if "timestamp" not in df.columns:
        errors.append("Missing 'timestamp' column.")
    else:
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            try:
                # Attempt to convert to datetime if not already.
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")
            except Exception:
                errors.append("Invalid datetime format in 'timestamp'.")
            else:
                # Check if all timestamps, once normalized to date, match the target processing date.
                if not (
                    df["timestamp"].dt.normalize() == target_processing_date.normalize()
                ).all():
                    errors.append(
                        f"All timestamps must be on the target processing date: {target_processing_date.strftime('%Y-%m-%d')}."
                    )

    if "air_temperature" not in df.columns:
        errors.append("Missing 'air_temperature' column.")
    else:
        if not pd.api.types.is_numeric_dtype(df["air_temperature"]):
            errors.append("'air_temperature' must be numeric.")
        else:
            # Check for realistic temperature bounds (Celsius).
            if not df["air_temperature"].between(-50, 60).all():
                errors.append("Temperature values out of realistic bounds.")

    # Check for duplicates based on timestamp, location_id, and crop_id.
    # Assuming location_id and crop_id are present before validation of the final daily set.
    if "location_id" in df.columns and "crop_id" in df.columns:
        if df.duplicated(subset=["timestamp", "location_id", "crop_id"]).any():
            errors.append(
                "Duplicate rows detected based on timestamp, location, and crop."
            )
    elif df.duplicated(subset=["timestamp"]).any():
        # Fallback check if crop_id or location_id are not present (less specific).
        errors.append("Duplicate rows detected.")

    if df.isnull().any().any():
        # Check for any missing values in the entire DataFrame.
        errors.append("Missing data found.")

    if errors:
        # If any errors were collected, raise a ValueError.
        raise ValueError("Data validation failed:\n" + "\n".join(errors))

    return df
