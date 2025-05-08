#!/bin/bash

airflow db upgrade

if ! airflow users list | grep -q "${AIRFLOW_ADMIN_USER}"; then
    airflow users create \
    --username "${AIRFLOW_ADMIN_USER}" \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password "${AIRFLOW_ADMIN_PASSWORD}"
else
    echo "Admin user ${AIRFLOW_ADMIN_USER} already exists."
fi
