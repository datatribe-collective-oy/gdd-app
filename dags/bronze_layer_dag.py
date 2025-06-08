from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import subprocess
import os


# Define Python callable for the task.
def run_data_fetcher_module(**kwargs):
    """
    Runs the data_fetcher.main module using Poetry, passing the DAG's execution date.
    """
    execution_date_str = kwargs["ds"]  # Airflow's execution date as YYYY-MM-DD string.
    project_root = os.getenv(
        "AIRFLOW_HOME", "/opt/airflow"  
    )

    # Command to execute: poetry run python -m data_fetcher.main --date YYYY-MM-DD
    # Ensure your data_fetcher.main module accepts a --date argument.
    poetry_command = [
        "poetry", "run", "python", "-m", "data_fetcher.main", "--date", execution_date_str
    ]

    print(f"Attempting to execute command: {' '.join(poetry_command)} in working directory: {project_root}")
    # The subprocess.run call will raise a CalledProcessError if the command fails,
    # which Airflow will catch and mark the task as failed.
    # stdout and stderr will be captured by Airflow logs.
    process = subprocess.run(
        poetry_command,
        check=True,
        cwd=project_root,
        capture_output=True, # Capture output for Airflow logs
        text=True
    )
    print(f"Data fetcher module for date {execution_date_str} completed successfully.")
    print("STDOUT:", process.stdout)
    if process.stderr: # Still good to log stderr if present, even on success
        print("STDERR:", process.stderr)


with DAG(
    dag_id="bronze_data_fetcher_dag",
    schedule_interval="27 3 * * *",  # 03:17 UTC daily
    start_date=datetime(2025, 5, 25),  
    catchup=False,
    tags=["bronze", "gdd-app"],
    doc_md="DAG to trigger the data_fetcher.main Python module via Poetry for the execution date.",
) as dag:
    run_data_fetcher_task = PythonOperator(
        task_id="run_data_fetcher_module_task",
        python_callable=run_data_fetcher_module,
    )
