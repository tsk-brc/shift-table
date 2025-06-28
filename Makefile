.PHONY: help install test test-coverage lint format security clean docker-build docker-run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test: ## Run tests
	python manage.py test --settings=shift_table.settings_test

test-coverage: ## Run tests with coverage
	pytest --cov=shift --cov=shift_table --cov-report=html --cov-report=term-missing

test-e2e: ## Run end-to-end tests
	python manage.py test shift.tests.test_e2e --settings=shift_table.settings_test

lint: ## Run linting
	flake8 shift/ shift_table/ --max-line-length=120 --ignore=E501,W503
	black --check shift/ shift_table/

format: ## Format code
	black shift/ shift_table/
	isort shift/ shift_table/

security: ## Run security checks
	bandit -r shift/ shift_table/
	safety check

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

docker-build: ## Build Docker image
	docker build -t shift-table .

docker-run: ## Run Docker container
	docker-compose up -d

docker-stop: ## Stop Docker container
	docker-compose down

migrate: ## Run database migrations
	python manage.py makemigrations
	python manage.py migrate

superuser: ## Create superuser
	python manage.py createsuperuser

shell: ## Open Django shell
	python manage.py shell

runserver: ## Run development server
	python manage.py runserver

collectstatic: ## Collect static files
	python manage.py collectstatic --noinput

check: ## Run Django system check
	python manage.py check

all: install lint test test-coverage security ## Run all checks 