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

- [Yr.no](https://developer.yr.no/) for developers.
- [Terms of Service of API usage](https://developer.yr.no/doc/TermsOfService/)
- Follows guidelines: authenticated headers, proxy-ready logic
- Traffic to Yr.no is **not triggered by user activity**, but instead scheduled via **Airflow DAGs**.
- Weather data is **fetched periodically**, parsed, and **stored in DuckDB**.
- Weather data is used to calculate GDD to estimate plant growth.

## Docker Architecture

- Each major component (NGINX, FastAPI, Streamlit, Airflow) runs in its own isolated Docker container.
- All containers are managed using Docker Compose, and share a network that allows them to communicate internally
- NGINX uses this internal network to route requests to the appropriate container (e.g., `/api/ → FastAPI`, `/ → Streamlit`)
- DuckDB is accessed by both services (FastAPI and Airflow) via a shared volume, allowing consistent read/write access across containers.

## Cloud Infrastructure

- Hosted on **AWS EC2** with the Free Tier
- Uses **Terraform** to provision:
  - EC2 instance
  - Security groups
  - S3 (if needed, under consideration)
- All internet-facing traffic is routed through **NGINX**, which:
  - Hides internal ports
  - Acts as a security and routing gateway
  - Can be upgraded to a **load balancer** if scaling is needed

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

> NGINX  hides infrastructure complexity and only exposes the necessary interfaces to the user.