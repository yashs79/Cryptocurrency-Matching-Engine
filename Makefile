.PHONY: help install test lint format clean docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean temporary files"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start Docker services"
	@echo "  make docker-down   - Stop Docker services"
	@echo "  make dev           - Run development server"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src/matching_engine --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	black --check src/ tests/
	isort --check-only src/ tests/
	flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203
	mypy src/ --ignore-missing-imports
	bandit -r src/

format:
	black src/ tests/
	isort src/ tests/

security:
	bandit -r src/
	safety check

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

docker-build:
	docker build -t matching-engine:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down -v

docker-logs:
	docker-compose logs -f

dev:
	uvicorn src.matching_engine.main:app --reload --host 0.0.0.0 --port 8000

benchmark:
	pytest tests/benchmark/ -v --benchmark-only

migrate:
	alembic upgrade head

migrate-create:
	@read -p "Enter migration name: " name; \
	alembic revision --autogenerate -m "$$name"
