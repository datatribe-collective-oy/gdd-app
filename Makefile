.PHONY: build-fastapi build-streamlit up down test-unit test-integration fmt lint install

api:
	poetry run python -m scripts.api

nodemon: # Imitates behavior of nodemon@node.js
	poetry run uvicorn scripts.api:app --reload

fastapi-b:
	docker build -f Dockerfile.fastapi -t gdd-fastapi .

streamlit-b:
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

black:
	poetry run black .

install:
	poetry install --no-root

terra-plan:
	cd terraform && terraform init && terraform plan

terra-apply:
	cd terraform && terraform apply

venv:
	poetry env activate