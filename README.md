## GDD App

This repository introduces a GDD (Growing Degree Days) prototype application, which fetches weather data, processes it through bronze and silver layers, and serves it via a FastAPI backend and a Streamlit frontend.

The README focuses on setting up and running the application using Docker Compose for development purposes.

Detailed documentation of the application's components will be updated on [Wiki](https://github.com/datatribe-collective-oy/gdd-app/wiki).

### Prerequisites

Ensure you have the following installed:

- Docker Deskstop

### Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/datatribe-collective/gdd-app.git
    cd gdd-app
    ```

2.  **Create a `.env` file:**

    Copy the example environment file and fill in the required values. This file contains credentials and configuration for the database, Airflow, and MinIO.

    ```bash
    cp example.env .env
    # Edit .env and fill in your details
    ```

    Make sure to define at least the following variables in your `.env` file:

    - `POSTGRES_USER_E`, `POSTGRES_PASSWORD_E`, `POSTGRES_DB_E` (for the PostgreSQL database, meant for airflow metadata)
    - `AIRFLOW_USER_E`, `AIRFLOW_PASSWORD_E` (for the Airflow admin user)
    - `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` (for MinIO credentials)
    - `MINIO_DATA_BUCKET_NAME` (the default bucket MinIO, create manually if needed prior running DAGs.)
    - `MINIO_API_PORT_E`, `MINIO_CONSOLE_PORT_E` (optional, specify ports if needed, defaults are 9000 and 9001)
    - `NGINX_ALLOWED_IP_1E`, `NGINX_ALLOWED_IP_2E` (for Nginx access control)

### Running the Application

Navigate to the root directory of the project where `docker-compose.yaml` is located.

1.  **Build and start the services:**

    These commands will build the necessary Docker images and starts all services defined in `docker-compose.yaml` in detached mode (`-d`).

    ```bash
    docker compose build && docker compose up -d
    ```

    The first run will take some time as it downloads base images, builds custom images, initializes Airflow, and sets up MinIO.

2.  **Initialize Airflow (First Run Only):**

    The `airflow-init` service handles database migrations and user creation. Wait for this service to complete successfully before proceeding. You can check its status:

    ```bash
    docker compose logs airflow-init
    ```

    Look for messages indicating successful completion.

### Accessing Services

Once the services are up and running:

- **Airflow UI:** `http://localhost:8080` (Login with the user/password from your `.env` file)
- **FastAPI Backend:** `http://localhost:8000` if accessing directly
- **Streamlit Frontend:** `http://localhost:8501` if accessing directly
- **MinIO Console:** `http://localhost:9001` (Login with the access key/secret key from your `.env` file)

### Running Airflow DAGs

1.  Access the Airflow UI at `http://localhost:8080`.
2.  (Optional) Unpause DAGs in the UI.
3.  You can trigger the DAG manually via the UI for testing, or wait for the scheduled run.

### Stopping the Application

To stop all running services and remove the containers (but preserve volumes like database and minio data):

```bash
docker compose down
```

To stop services and remove volumes (useful for a clean start, but **data will be lost**):

```bash
docker compose down -v
```

### Development Notes

- Changes to DAG files (`./dags`) are automatically picked up by the Airflow scheduler and webserver due to the volume mount.
- Changes to application code (in `data_fetcher`, `universal`, `gdd_counter` `api_service`, `streamlit_app`, etc) require rebuilding the respective Docker images and restarting the service (`docker compose up --build -d <service_name>`).

### Future Development Tasks for local

- Gold Layer DAG
- Data quality, data fetching and validation logic evaluation, and their respective development.
- Security evaluation (by using OWASP Application Security Verification Standard).

### Future Development for deployment

- Development of Nginx reverse proxying with Let's Encrypt.
- Finalise Terraform setup.
- Integration testing.
- Deployment to AWS (EC2, S3).
- End-to-end testing.
