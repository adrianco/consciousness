# Project Setup and Environment Guide

## Overview
This guide provides step-by-step instructions for setting up the House Consciousness System development environment using UV package manager, Python 3.11+, and the recommended development stack.

## Prerequisites
- Python 3.11 or higher
- Git
- Node.js 18+ (for web interface development)
- SQLite3 (included with Python)

## Phase 1: Environment Setup

### 1.1 Install UV Package Manager
```bash
# Install UV (cross-platform)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv

# Verify installation
uv --version
```

### 1.2 Project Initialization
```bash
# Create project directory
mkdir house-consciousness
cd house-consciousness

# Initialize UV project
uv init --python 3.11

# Create project structure
mkdir -p {consciousness/{core,components,io,interfaces,adapters,models,utils},tests/{unit,integration,e2e},docs,scripts,config}
```

### 1.3 pyproject.toml Configuration
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "house-consciousness"
version = "0.1.0"
description = "House Consciousness System with SAFLA Model"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.11"
keywords = ["consciousness", "iot", "safla", "home-automation"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "aiosqlite>=0.19.0",
    "pydantic>=2.4.0",
    "python-multipart>=0.0.6",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "openai>=1.3.0",
    "anthropic>=0.7.0",
    "httpx>=0.25.0",
    "websockets>=12.0",
    "redis>=5.0.0",
    "celery>=5.3.0",
    "schedule>=1.2.0",
    "python-dateutil>=2.8.2",
    "pytz>=2023.3",
    "aiofiles>=23.2.1",
    "jinja2>=3.1.2",
    "pyyaml>=6.0.1",
    "cryptography>=41.0.0",
    "pydantic-settings>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.9.0",
    "isort>=5.12.0",
    "flake8>=6.1.0",
    "mypy>=1.6.0",
    "pre-commit>=3.4.0",
    "httpx>=0.25.0",
    "factory-boy>=3.3.0",
    "faker>=19.12.0",
]

test = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.25.0",
    "factory-boy>=3.3.0",
    "faker>=19.12.0",
]

docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.4.0",
    "mkdocstrings[python]>=0.23.0",
]

[project.scripts]
consciousness = "consciousness.main:main"
consciousness-dev = "consciousness.dev:main"
consciousness-migrate = "consciousness.database:migrate"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=consciousness",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
asyncio_mode = "auto"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow tests",
    "external: Tests requiring external services",
]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.nox
  | \.pants.d
  | \.pyc
  | \.pyo
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["consciousness"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = [
    "openai.*",
    "anthropic.*",
    "schedule.*",
    "celery.*",
    "redis.*",
]
ignore_missing_imports = true
```

### 1.4 Install Dependencies
```bash
# Install development dependencies
uv add --dev pytest pytest-asyncio pytest-cov black isort flake8 mypy pre-commit

# Install production dependencies
uv add fastapi uvicorn sqlalchemy alembic aiosqlite pydantic openai anthropic httpx websockets redis celery schedule python-dateutil pytz aiofiles jinja2 pyyaml cryptography pydantic-settings

# Install optional dependencies
uv add --dev factory-boy faker mkdocs mkdocs-material mkdocstrings[python]
```

### 1.5 Pre-commit Setup
```bash
# Create pre-commit configuration
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
EOF

# Install pre-commit hooks
uv run pre-commit install
```

## Phase 2: Project Structure Setup

### 2.1 Create Core Directory Structure
```bash
# Create main application structure
touch consciousness/__init__.py
touch consciousness/main.py
touch consciousness/config.py
touch consciousness/exceptions.py

# Core consciousness components
touch consciousness/core/__init__.py
touch consciousness/core/orchestrator.py
touch consciousness/core/consciousness_engine.py
touch consciousness/core/emotion_processor.py
touch consciousness/core/memory_manager.py
touch consciousness/core/decision_engine.py
touch consciousness/core/learning_engine.py
touch consciousness/core/query_engine.py
touch consciousness/core/prediction_engine.py

# SAFLA components
touch consciousness/components/__init__.py
touch consciousness/components/safla_loop.py
touch consciousness/components/sense_module.py
touch consciousness/components/analyze_module.py
touch consciousness/components/feedback_module.py
touch consciousness/components/learn_module.py

# IO modules
touch consciousness/io/__init__.py
touch consciousness/io/device_collector.py
touch consciousness/io/data_aggregator.py
touch consciousness/io/event_processor.py
touch consciousness/io/device_controller.py
touch consciousness/io/action_executor.py
touch consciousness/io/protocol_adapter.py

# Interfaces
touch consciousness/interfaces/__init__.py
touch consciousness/interfaces/web_interface.py
touch consciousness/interfaces/mobile_interface.py
touch consciousness/interfaces/voice_interface.py
touch consciousness/interfaces/api_interface.py

# Device adapters
touch consciousness/adapters/__init__.py
touch consciousness/adapters/homekit_adapter.py
touch consciousness/adapters/alexa_adapter.py
touch consciousness/adapters/weather_adapter.py
touch consciousness/adapters/energy_adapter.py
touch consciousness/adapters/security_adapter.py

# Database models
touch consciousness/models/__init__.py
touch consciousness/models/base.py
touch consciousness/models/consciousness.py
touch consciousness/models/entities.py
touch consciousness/models/events.py
touch consciousness/models/controls.py

# Utilities
touch consciousness/utils/__init__.py
touch consciousness/utils/config.py
touch consciousness/utils/logging.py
touch consciousness/utils/security.py
touch consciousness/utils/helpers.py
```

### 2.2 Create Test Structure
```bash
# Test directories
touch tests/__init__.py
touch tests/conftest.py

# Unit tests
touch tests/unit/__init__.py
touch tests/unit/test_consciousness_engine.py
touch tests/unit/test_emotion_processor.py
touch tests/unit/test_memory_manager.py
touch tests/unit/test_safla_loop.py
touch tests/unit/test_models.py

# Integration tests
touch tests/integration/__init__.py
touch tests/integration/test_database.py
touch tests/integration/test_device_adapters.py
touch tests/integration/test_api_endpoints.py
touch tests/integration/test_safla_integration.py

# E2E tests
touch tests/e2e/__init__.py
touch tests/e2e/test_consciousness_scenarios.py
touch tests/e2e/test_conversation_flows.py
touch tests/e2e/test_device_orchestration.py
```

## Phase 3: Configuration Setup

### 3.1 Environment Configuration
```bash
# Create environment files
cat > .env.example << 'EOF'
# Application Settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here
API_KEY_OPENAI=your-openai-api-key
API_KEY_ANTHROPIC=your-anthropic-api-key

# Database
DATABASE_URL=sqlite:///./consciousness.db
DATABASE_TEST_URL=sqlite:///./test_consciousness.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/consciousness.log

# Device Integration
HOMEKIT_PIN=123-45-678
WEATHER_API_KEY=your-weather-api-key
ENERGY_PROVIDER_API_KEY=your-energy-api-key

# Security
ENCRYPTION_KEY=your-encryption-key
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Consciousness Settings
EMOTION_UPDATE_INTERVAL=300
MEMORY_RETENTION_DAYS=365
LEARNING_RATE=0.01
PREDICTION_HORIZON_HOURS=24
EOF

# Copy to actual .env file
cp .env.example .env
```

### 3.2 Create Configuration Files
```bash
# Create config directory structure
mkdir -p config/{development,production,testing}

# Development config
cat > config/development.yaml << 'EOF'
database:
  url: "sqlite:///./consciousness_dev.db"
  echo: true
  pool_size: 5

consciousness:
  emotion_update_interval: 60
  memory_retention_days: 30
  learning_rate: 0.1
  debug_mode: true

logging:
  level: DEBUG
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/development.log"

devices:
  discovery_interval: 300
  timeout: 30
  retry_attempts: 3
EOF

# Production config
cat > config/production.yaml << 'EOF'
database:
  url: "sqlite:///./consciousness.db"
  echo: false
  pool_size: 20

consciousness:
  emotion_update_interval: 300
  memory_retention_days: 365
  learning_rate: 0.01
  debug_mode: false

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/production.log"

devices:
  discovery_interval: 600
  timeout: 60
  retry_attempts: 5
EOF

# Testing config
cat > config/testing.yaml << 'EOF'
database:
  url: "sqlite:///:memory:"
  echo: false
  pool_size: 1

consciousness:
  emotion_update_interval: 1
  memory_retention_days: 1
  learning_rate: 1.0
  debug_mode: true

logging:
  level: WARNING
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: null

devices:
  discovery_interval: 10
  timeout: 5
  retry_attempts: 1
EOF
```

## Phase 4: Development Scripts

### 4.1 Create Development Scripts
```bash
# Create scripts directory
mkdir -p scripts

# Development server script
cat > scripts/dev.py << 'EOF'
#!/usr/bin/env python3
"""Development server script."""

import uvicorn
from consciousness.main import app

if __name__ == "__main__":
    uvicorn.run(
        "consciousness.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["consciousness"],
        log_level="debug",
    )
EOF

# Database migration script
cat > scripts/migrate.py << 'EOF'
#!/usr/bin/env python3
"""Database migration script."""

import asyncio
from consciousness.database import init_db, create_tables

async def main():
    await init_db()
    await create_tables()
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Make scripts executable
chmod +x scripts/*.py
```

### 4.2 Create Makefile
```bash
cat > Makefile << 'EOF'
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
EOF
```

## Phase 5: Initial Setup Verification

### 5.1 Verify Installation
```bash
# Check UV installation
uv --version

# Check Python version
uv run python --version

# Verify dependencies
uv run python -c "import fastapi, sqlalchemy, pytest; print('All dependencies installed successfully!')"
```

### 5.2 Run Initial Tests
```bash
# Create basic test to verify setup
cat > tests/test_setup.py << 'EOF'
"""Test setup and basic functionality."""

def test_python_version():
    """Test Python version compatibility."""
    import sys
    assert sys.version_info >= (3, 11)

def test_dependencies():
    """Test that all critical dependencies are importable."""
    import fastapi
    import sqlalchemy
    import pytest
    import pydantic
    assert True
EOF

# Run the test
uv run pytest tests/test_setup.py -v
```

## Next Steps

1. **Database Setup**: Follow `02-database-implementation-guide.md`
2. **Core Engine**: Implement consciousness engine using `03-consciousness-engine-guide.md`
3. **SAFLA Loop**: Build SAFLA components using `04-safla-loop-guide.md`
4. **Device Integration**: Add device adapters using `05-device-integration-guide.md`

## Common Issues and Solutions

### UV Installation Issues
- **Issue**: UV not found after installation
- **Solution**: Restart terminal or run `source ~/.bashrc`

### Dependency Conflicts
- **Issue**: Version conflicts during installation
- **Solution**: Use `uv add --resolution=highest` or specify exact versions

### Python Version Issues
- **Issue**: Python 3.11+ not available
- **Solution**: Use `uv python install 3.11` to install specific version

### Permission Issues
- **Issue**: Permission denied during installation
- **Solution**: Use `--user` flag or virtual environment

This setup guide provides a solid foundation for the House Consciousness System development. The project structure follows modern Python best practices with comprehensive testing, linting, and development tools configured for optimal developer experience.