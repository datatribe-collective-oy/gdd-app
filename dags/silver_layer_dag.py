from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import subprocess
import os


# Define Python callable for the task
def run_gdd_counter_module(**kwargs):
    """
    Runs the gdd_counter.processor module using Poetry.
    This script is expected to process recent bronze data by default.
    """
    project_root = os.getenv(
        "AIRFLOW_HOME", "/opt/airflow"
    )  
    # Command to execute: poetry run python -m gdd_counter.processor
    # Ensure your gdd_counter.processor module is set up to be run this way.
    poetry_command = ["poetry", "run", "python", "-m", "gdd_counter.processor"]

    print(f"Executing command: {' '.join(poetry_command)} in {project_root}")
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
    print("GDD counter module completed successfully.")
    print("STDOUT:", process.stdout)
    if process.stderr: # Still good to log stderr if present, even on success
        print("STDERR:", process.stderr)


with DAG(
    dag_id="silver_gdd_processor_dag",
    schedule_interval="23 3 * * *",  # 03:23 UTC daily 
    start_date=datetime(2025, 5, 25),  
    catchup=False,
    tags=["silver", "gdd-app"],
    doc_md="DAG to trigger the gdd_counter.processor Python module via Poetry.",
) as dag:
    run_gdd_counter_task = PythonOperator(
        task_id="run_gdd_counter_module_task",
        python_callable=run_gdd_counter_module,
    )
