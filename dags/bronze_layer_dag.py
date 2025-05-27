from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import subprocess
import os


# Define Python callable for the task.
def run_make_data_fetcher(**kwargs):
    """
    Runs the 'make data-fetcher' command, passing the DAG's execution date.
    The data_fetcher.main.py script will process data for this specific date.
    """
    execution_date_str = kwargs["ds"]  # Airflow's execution date as YYYY-MM-DD string.
    project_root = os.getenv(
        "AIRFLOW_HOME", "/opt/airflow"  
    )

    make_command = ["make", "data-fetcher", f"DATE={execution_date_str}"]

    print(f"Attempting to execute command: {' '.join(make_command)} in working directory: {project_root}")
    try:
        process = subprocess.run(
            make_command,
            check=True,         # Raise CalledProcessError for non-zero exit codes.
            cwd=project_root,
            capture_output=True,
            text=True           # Decode stdout/stderr as string.
        )
        print(f"'make data-fetcher' for date {execution_date_str} completed successfully.")
        print("STDOUT:")
        print(process.stdout)
        if process.stderr:
            print("STDERR: (Note: Some tools output to stderr even on success)")
            print(process.stderr)
    except subprocess.CalledProcessError as e:
        print(
            f"ERROR: 'make data-fetcher' command failed with exit code {e.returncode} for date {execution_date_str}."
        )
        print("STDOUT from failed command:")
        print(e.stdout)
        print("STDERR from failed command:")
        print(e.stderr)
        raise  # Re-raise the exception to fail the Airflow task
    except FileNotFoundError:
        print(
            f"ERROR: The 'make' command was not found, or the working directory '{project_root}' does not exist."
        )
        print(f"Please ensure 'make' is installed and in PATH, and the project_root is correct and accessible.")
        raise
    except PermissionError as e:
        print(
            f"ERROR: Permission denied when trying to execute 'make' for date {execution_date_str}."
        )
        print(f"Details: {str(e)}")
        print(f"Please ensure the 'make' command (usually at /usr/bin/make) is executable by the Airflow worker user in '{project_root}'.")
        raise
    except Exception as e:
        # Catch any other unexpected errors during subprocess execution.
        print(f"ERROR: An unexpected error occurred while trying to run 'make data-fetcher' for date {execution_date_str}: {str(e)}")
        raise


with DAG(
    dag_id="bronze_data_fetcher_dag",
    schedule_interval="27 3 * * *",  # 03:17 UTC daily
    start_date=datetime(2025, 5, 25),  
    catchup=False,
    tags=["bronze", "gdd-app", "make"],
    doc_md="DAG to trigger the data_fetcher via a make command for the execution date.",
) as dag:
    run_data_fetcher_task = PythonOperator(
        task_id="run_make_data_fetcher_task",
        python_callable=run_make_data_fetcher,
    )
