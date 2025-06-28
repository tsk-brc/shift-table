# Docker環境でコマンドを実行するための変数
DOCKER_EXEC = docker compose exec web

ifeq ($(USE_DOCKER),0)
    EXEC_CMD =
else
    EXEC_CMD = $(DOCKER_EXEC)
endif

.PHONY: help install test test-coverage lint format security clean docker-build docker-run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	$(EXEC_CMD) pip install -r requirements.txt
	$(EXEC_CMD) pip install -r requirements-dev.txt

test: ## Run tests
	$(EXEC_CMD) python manage.py test --settings=shift_table.settings_test

test-coverage: ## Run tests with coverage
	$(EXEC_CMD) pytest shift/test_files/ --cov=shift --cov=shift_table --cov-report=html --cov-report=term-missing

test-e2e: ## Run end-to-end tests
	$(EXEC_CMD) python manage.py test shift.test_files.test_e2e --settings=shift_table.settings_test

lint: ## Run linting
	$(EXEC_CMD) flake8 shift/ shift_table/ --max-line-length=120 --ignore=E501,W503
	$(EXEC_CMD) black --check shift/ shift_table/

format: ## Format code
	$(EXEC_CMD) black shift/ shift_table/
	$(EXEC_CMD) isort shift/ shift_table/

security: ## Run security checks
	$(EXEC_CMD) bandit -r shift/ shift_table/
	$(EXEC_CMD) safety check

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
	$(EXEC_CMD) python manage.py makemigrations
	$(EXEC_CMD) python manage.py migrate

superuser: ## Create superuser
	$(EXEC_CMD) python manage.py createsuperuser

shell: ## Open Django shell
	$(EXEC_CMD) python manage.py shell

runserver: ## Run development server
	$(EXEC_CMD) python manage.py runserver 0.0.0.0:8000

collectstatic: ## Collect static files
	$(EXEC_CMD) python manage.py collectstatic --noinput

check: ## Run Django system check
	$(EXEC_CMD) python manage.py check

all: install lint test test-coverage security ## Run all checks 