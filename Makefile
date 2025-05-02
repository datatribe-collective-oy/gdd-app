.PHONY: fastapi-b streamlit-b up down unit-t integration-t black ruff install ruff-check venv nodemon terra-plan terra-apply terra-apply-tfvars terra-destroy terra-list terra-fmt terra-valid

# Application dev

venv: # create virtual environment
	poetry env activate

unit-t: # run unit tests
	poetry run pytest tests/unit

integration-t: # run integration tests
	poetry run pytest tests/integration

ruff-check: # check code with ruff
	poetry run ruff check .

ruff: # lint and fix code
	poetry run ruff check . --fix

black: #format code
	poetry run black .

install: # install dependencies
	poetry install --no-root

api: # run fastapi app
	poetry run python -m scripts.api

nodemon: # run dev server similar to nodemon@node.js
	poetry run uvicorn scripts.api:app --reload

# Docker containers
fastapi-b: # build fastapi container
	docker build -f Dockerfile.fastapi -t gdd-fastapi .

streamlit-b: # build streamlit container
	docker build -f Dockerfile.streamlit -t gdd-streamlit .

up: # start containers
	docker-compose up

down: # stop and remove containers
	docker-compose down

# Terraform setup

terra-plan: # preview terraform changes
	cd terraform && terraform init && terraform plan

terra-apply: # apply terraform changes
	cd terraform && terraform apply

terra-apply-tfvars: # ! apply terraform changes with tfvars
	cd terraform && terraform init && terraform apply -var-file=dev.tfvars

terra-destroy: # ! destroy terraform resources
	cd terraform && terraform destroy -var-file=dev.tfvars

terra-list: # list resources in terraform state
	cd terraform && terraform state list

terra-fmt: # format terraform code
	cd terraform && terraform fmt

terra-valid: # validate terraform code
	cd terraform && terraform validate
