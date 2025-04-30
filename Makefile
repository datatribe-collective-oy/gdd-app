.PHONY: build-fastapi build-streamlit up down test-unit test-integration fmt lint install

api:
	poetry run python -m scripts.api

nodemon: # Imitates behavior of nodemon@node.js
	poetry run uvicorn scripts.api:app --reload

build-fastapi:
	docker build -f Dockerfile.fastapi -t gdd-fastapi .

build-streamlit:
	docker build -f Dockerfile.streamlit -t gdd-streamlit .

up:
	docker-compose up

down:
	docker-compose down

test-unit:
	poetry run pytest tests/unit

test-integration:
	poetry run pytest tests/integration

lint:
	poetry run ruff check scripts tests

fmt:
	poetry run ruff format scripts tests

black:
	poetry run black scripts tests

install:
	poetry install --no-root

terraform-plan:
	cd terraform && terraform init && terraform plan

terraform-apply:
	cd terraform && terraform apply

venv:
	poetry env activate