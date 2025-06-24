.PHONY: help install dev test lint format clean docs

help:
	@echo "Available commands:"
	@echo "  install    Install dependencies"
	@echo "  dev        Run development server"
	@echo "  test       Run tests"
	@echo "  lint       Run linting"
	@echo "  format     Format code"
	@echo "  clean      Clean up files"
	@echo "  docs       Build documentation"

install:
	uv sync --dev

dev:
	uv run python scripts/dev.py

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit/

test-integration:
	uv run pytest tests/integration/

test-e2e:
	uv run pytest tests/e2e/

test-cov:
	uv run pytest --cov=consciousness --cov-report=html

lint:
	uv run flake8 consciousness tests
	uv run mypy consciousness

format:
	uv run black consciousness tests scripts
	uv run isort consciousness tests scripts

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/
	rm -rf build/ dist/ *.egg-info/

docs:
	uv run mkdocs build

docs-serve:
	uv run mkdocs serve

migrate:
	uv run python scripts/migrate.py

init-db:
	uv run alembic init alembic
	uv run alembic revision --autogenerate -m "Initial migration"
	uv run alembic upgrade head
