.PHONY: build-fastapi build-streamlit up down test-unit test-integration fmt lint install

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

fmt:
	poetry run black scripts tests

lint:
	poetry run flake8 scripts tests

install:
	poetry install

terraform-plan:
	cd terraform && terraform init && terraform plan

terraform-apply:
	cd terraform && terraform apply