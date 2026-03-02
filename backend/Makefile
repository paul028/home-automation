.PHONY: run test test-v test-file install freeze lint db-revision db-upgrade db-downgrade db-current db-history db-reset help

VENV := .venv/bin
PYTHON := $(VENV)/python
PYTEST := $(VENV)/python -m pytest
ALEMBIC := $(VENV)/alembic
UVICORN := $(VENV)/uvicorn

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

run: ## Start the backend (with hot reload)
	$(UVICORN) app.main:app --reload

run-rec: ## Start the backend with recording enabled
	RECORDING_ENABLED=true $(UVICORN) app.main:app --reload

install: ## Install dependencies from requirements.txt
	$(VENV)/pip install -r requirements.txt

freeze: ## Update requirements.txt from installed packages
	$(VENV)/pip freeze > requirements.txt

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: ## Run all tests
	$(PYTEST)

test-v: ## Run all tests with verbose output
	$(PYTEST) -v

test-file: ## Run a specific test file (usage: make test-file F=tests/services/test_camera_service.py)
	$(PYTEST) $(F) -v

# ---------------------------------------------------------------------------
# Database migrations
# ---------------------------------------------------------------------------

db-revision: ## Create a new migration (usage: make db-revision M="add users table")
	$(ALEMBIC) revision --autogenerate -m "$(M)"

db-upgrade: ## Apply all pending migrations
	$(ALEMBIC) upgrade head

db-downgrade: ## Revert the last migration
	$(ALEMBIC) downgrade -1

db-current: ## Show current migration version
	$(ALEMBIC) current

db-history: ## Show migration history
	$(ALEMBIC) history

db-reset: ## Delete the database and re-run all migrations
	rm -f home_automation.db
	$(ALEMBIC) upgrade head
