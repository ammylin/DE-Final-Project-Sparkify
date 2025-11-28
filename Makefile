.PHONY: help install test test-unit test-integration test-edge coverage lint format clean security check-requirements

help:
	@echo "Sparkify Test Suite Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup:"
	@echo "  make install              Install dependencies"
	@echo "  make check-requirements   Check if all requirements are installed"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 Run all tests"
	@echo "  make test-unit            Run unit tests only"
	@echo "  make test-integration     Run integration tests"
	@echo "  make test-edge            Run edge case tests"
	@echo "  make test-parallel        Run tests in parallel"
	@echo "  make coverage             Generate coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Run all linters"
	@echo "  make format               Format code"
	@echo "  make security             Run security checks"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean                Clean test artifacts"
	@echo ""

install:
	pip install -r requirements.txt
	@echo "Dependencies installed successfully"

check-requirements:
	@python -c "import pytest; print(f'pytest {pytest.__version__}')" || (echo "pytest not found" && exit 1)
	@python -c "import pandas; print(f'pandas {pandas.__version__}')" || (echo "pandas not found" && exit 1)
	@python -c "import numpy; print(f'numpy {numpy.__version__}')" || (echo "numpy not found" && exit 1)
	@python -c "import sklearn; print(f'scikit-learn installed')" || (echo "scikit-learn not found" && exit 1)
	@echo "All requirements satisfied"

test:
	pytest tests/ -v --tb=short

test-unit:
	pytest tests/ -v -m unit --tb=short

test-integration:
	pytest tests/ -v -m integration --tb=short

test-edge:
	pytest tests/test_integration_edge_cases.py -v --tb=short

test-parallel:
	pytest tests/ -n auto -v --tb=short

coverage:
	pytest tests/ \
		--cov=dags \
		--cov=py_and_notebooks \
		--cov-report=html \
		--cov-report=term-missing \
		--cov-report=xml
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	flake8 dags/ py_and_notebooks/ tests/ --max-line-length=100 || true
	black --check dags/ py_and_notebooks/ tests/ --line-length=100 || true
	isort --check-only dags/ py_and_notebooks/ tests/ || true

format:
	black dags/ py_and_notebooks/ tests/ --line-length=100
	isort dags/ py_and_notebooks/ tests/
	@echo "Code formatted successfully"

security:
	bandit -r dags/ py_and_notebooks/ -ll || true
	safety check --json || true

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + || true
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .coverage.*
	rm -rf dist/
	rm -rf build/
	@echo "Clean completed"

# Development targets
dev-setup: install
	pip install black flake8 isort pylint bandit safety

watch-tests:
	ptw tests/

test-verbose:
	pytest tests/ -vv --tb=long

test-failed-first:
	pytest tests/ -v --tb=short --failed-first --lf

test-failed-only:
	pytest tests/ -v --tb=short --lf

# CI/CD simulation
ci: clean check-requirements lint test coverage security
	@echo "CI pipeline completed successfully"

# Quick check
check: test-unit lint
	@echo "Quick checks completed"
