# System Architecture & Data Flow
This document outlines the system architecture for the farmer's assistant application.

## Overview

| Component        | Role                                                                 |
|------------------|----------------------------------------------------------------------|
| FastAPI          | Backend API to serve weather and GDD data                            |
| Streamlit        | Frontend dashboard for farmers to visualize GDD          |
| Airflow          | Orchestration tool to schedule and run data ingestion pipelines      |
| DuckDB           | Lightweight embedded database to store and query weather data        |
| NGINX            | Reverse proxy to route traffic between frontend and backend          |
| Docker           | Containerization for modular, isolated components                    |
| EC2 (AWS)        | Cloud VM hosting the full application stack                          |
| Terraform        | Infrastructure-as-code tool to provision AWS resources               |

## Data Flow
## API Usage (Yr.no)
## Docker Architecture
## Cloud Infrastructure
## Tech Stack

- Python
- SQL
- FastAPI
- Streamlit
- Apache Airflow
- DuckDB
- NGINX
- Docker & Docker Compose
- AWS EC2
- Terraform

## Notes