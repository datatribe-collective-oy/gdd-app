from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from data_fetcher.config import MAIZE_INDIA_LOCATIONS, SORGHUM_KENYA_LOCATIONS
from data_fetcher.fetcher import fetch_weather_data
from data_fetcher.validator import validate_weather_data
from data_fetcher.saver import save_partitioned_parquet_s3

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="bronze_fetch_dag",
    default_args=default_args,
    description="Fetch weather data for crop locations and save bronze Parquet in S3",
    schedule_interval="27 3 * * *",  # 03:27 UTC daily, compliance requirement with Yr.no API.
    start_date=datetime(2025, 5, 5),
    catchup=False,
    tags=["bronze", "weather", "GDD"],
) as dag:

    # LOGICAL ERROR
    # Choose which crop to run for
    crop = "sorghum"
    locations = SORGHUM_KENYA_LOCATIONS if crop == "sorghum" else MAIZE_INDIA_LOCATIONS
    bucket = "gdd-raw-weather-data" 

    def fetch_validate_save(location, lat, lon, crop):
        df = fetch_weather_data(lat, lon, location, crop)
        df = validate_weather_data(df)
        save_partitioned_parquet_s3(df, bucket=bucket)

    for location, (lat, lon) in locations.items():
        task = PythonOperator(
            task_id=f"fetch_validate_save_{location}",
            python_callable=fetch_validate_save,
            op_args=[location, lat, lon, crop],
        )
