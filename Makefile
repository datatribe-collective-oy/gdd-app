# Default shell for executing recipes
SHELL := /bin/bash

# Help Target: Parses ## comments from targets
.PHONY: help
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: venv unit-t integration-t ruff-check ruff install nodemon data-fetcher gdd-counter

# Application dev

venv: ## Create or activate poetry virtual environment
	poetry env activate

unit-t: ## Run unit tests
	poetry run pytest tests/unit

integration-t: ## Run integration tests
	poetry run pytest tests/integration

ruff-check: ## Check code with ruff
	poetry run ruff check .

ruff: ## Lint and fix code with ruff
	poetry run ruff check . --fix

install: ## Install dependencies using poetry
	poetry install --no-root

nodemon: ## Run FastAPI dev server with auto-reload (uvicorn)
	poetry run uvicorn api_service.main:app --reload

data-fetcher-poetry: ## (Local Dev) Run data fetcher using poetry
	poetry run python -m data_fetcher.main $(if $(DATE),--date $(DATE),)

data-fetcher: ## (CI/Container) Run data fetcher directly
	python -m data_fetcher.main $(if $(DATE),--date $(DATE),)

gdd-counter-poetry: ## (Local Dev) Run GDD counter using poetry. Optionally provide bronze_path="<glob_pattern>"
	@if [ -n "$(bronze_path)" ]; then \
		echo "Running GDD counter with provided bronze_path: $(bronze_path)"; \
		poetry run python -m gdd_counter.processor "$(bronze_path)"; \
	else \
		echo "Running GDD counter for the last 2 days (default behavior)."; \
		poetry run python -m gdd_counter.processor; \
	fi

gdd-counter: ## (CI/Container) Run GDD counter directly. Optionally provide bronze_path="<glob_pattern>"
	@if [ -n "$(bronze_path)" ]; then \
		echo "Running GDD counter with provided bronze_path: $(bronze_path)"; \
		python -m gdd_counter.processor "$(bronze_path)"; \
	else \
		echo "Running GDD counter for the last 2 days (default behavior)."; \
		python -m gdd_counter.processor; \
	fi

# Docker containers (using docker compose)
.PHONY: build-core build-services build-all build-no-c up up-d down down-v logs-service ps restart-service

build-core: ## Build nginx, streamlit, and fastapi services without cache
	docker compose build --no-cache nginx streamlit fastapi

build-services: ## Build nginx, streamlit, and fastapi services (uses cache)
	docker compose build nginx streamlit fastapi

build-all: ## Build all services defined in docker-compose.yaml (uses cache)
	docker compose build

build-no-c: ## Build all services defined in docker-compose.yaml without cache
	docker compose build --no-cache

up-core: ## Start core services (nginx, streamlit, fastapi) in foreground (interactive)
	docker compose up -d nginx streamlit fastapi

up: ## Start all services in foreground (interactive)
	docker compose up

up-d: ## Start all services in detached mode (background)
	docker compose up -d

down: ## Stop and remove containers
	docker compose down

down-v: ## Stop and remove containers and their volumes
	docker compose down -v

logs-service: ## View logs for a specific service (e.g., make logs-service service=fastapi)
	@if [ -z "$(service)" ]; then \
		echo "Error: service name not provided. Usage: make logs-service service=<name>"; \
		exit 1; \
	fi
	docker compose logs -f $(service)

ps: ## List running Docker Compose services
	docker compose ps

restart-service: ## Restart a specific service (e.g., make restart-service service=fastapi)
	@if [ -z "$(service)" ]; then \
		echo "Error: service name not provided. Usage: make restart-service service=<name>"; \
		exit 1; \
	fi
	docker compose restart $(service)

# Docker containers (individual image builds - if needed for specific tagging/pushing outside compose)
.PHONY: fastapi-b streamlit-b

fastapi-b: ## Build gdd-fastapi image directly using Dockerfile.fastapi
	docker build -f Dockerfile.fastapi -t gdd-fastapi .

streamlit-b: ## Build gdd-streamlit image directly using Dockerfile.streamlit
	docker build -f Dockerfile.streamlit -t gdd-streamlit .

# Terraform setup
.PHONY: terra-plan terra-apply terra-destroy terra-list terra-fmt terra-valid

terra-plan: ## Preview terraform changes (init + plan)
	cd terraform && terraform init && terraform plan

terra-apply: ## Apply terraform changes using dev.tfvars (init + apply, auto-approve)
	cd terraform && terraform init && terraform apply -var-file=dev.tfvars -auto-approve

terra-destroy: ## Destroy terraform resources with dev.tfvars (auto-approve)
	cd terraform && terraform destroy -var-file=dev.tfvars -auto-approve

terra-list: ## List resources in terraform state
	cd terraform && terraform state list

terra-fmt: ## Format terraform code recursively
	cd terraform && terraform fmt -recursive

terra-valid: ## Validate terraform code
	cd terraform && terraform validate
