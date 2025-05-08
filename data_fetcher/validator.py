import pandas as pd


def validate_weather_data(df):
    errors = []

    if "timestamp" not in df.columns:
        errors.append("Missing 'timestamp' column.")
    else:
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            try:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")
            except Exception:
                errors.append("Invalid datetime format in 'timestamp'.")

    if "air_temperature" not in df.columns:
        errors.append("Missing 'air_temperature' column.")
    else:
        if not pd.api.types.is_numeric_dtype(df["air_temperature"]):
            errors.append("'air_temperature' must be numeric.")
        else:
            if not df["air_temperature"].between(-50, 60).all():
                errors.append("Temperature values out of realistic bounds.")

    if df.duplicated().any():
        errors.append("Duplicate rows detected.")

    if df.isnull().any().any():
        errors.append("Missing data found.")

    if errors:
        raise ValueError("Data validation failed:\n" + "\n".join(errors))

    return df
