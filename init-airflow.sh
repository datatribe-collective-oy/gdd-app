#!/bin/bash

airflow db migrate

if ! airflow users list | grep -q "${AIRFLOW_ADMIN_USER}"; then
    airflow users create \
    --username "${AIRFLOW_ADMIN_USER}" \
    --firstname "${AIRFLOW_ADMIN_FIRSTNAME}" \
    --lastname "${AIRFLOW_ADMIN_LASTNAME}" \
    --role ${AIRFLOW_ADMIN_ROLE} \
    --email ${AIRFLOW_ADMIN_EMAIL} \
    --password "${AIRFLOW_ADMIN_PASSWORD}"
else
    echo "Admin user ${AIRFLOW_ADMIN_USER} already exists."
fi
