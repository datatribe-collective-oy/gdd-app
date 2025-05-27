from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import subprocess
import os


# Define Python callable for the task
def run_make_gdd_counter(**kwargs):
    """
    Runs the 'make gdd-counter' command.
    The gdd_counter.processor.py script, when called without arguments by 'make',
    defaults to processing bronze data for the last 2 days.
    """
    project_root = os.getenv(
        "AIRFLOW_HOME", "/opt/airflow"
    )  
    make_command = ["make", "gdd-counter"]

    print(f"Executing command: {' '.join(make_command)} in {project_root}")
    try:
        process = subprocess.run(
            make_command, check=True, cwd=project_root, capture_output=True, text=True
        )
        print("STDOUT:", process.stdout)
        if process.stderr:
            print("STDERR:", process.stderr)
    except subprocess.CalledProcessError as e:
        print("Error during 'make gdd-counter' execution.")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        raise


with DAG(
    dag_id="silver_gdd_processor_dag",
    schedule_interval="23 3 * * *",  # 03:23 UTC daily 
    start_date=datetime(2025, 5, 25),  
    catchup=False,
    tags=["silver", "gdd-app", "make"],
    doc_md="DAG to trigger the gdd_counter via a make command.",
) as dag:
    run_gdd_counter_task = PythonOperator(
        task_id="run_make_gdd_counter_task",
        python_callable=run_make_gdd_counter,
    )
