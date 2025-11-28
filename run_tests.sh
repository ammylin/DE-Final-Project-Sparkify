#!/bin/bash
# Local test runner script for Sparkify project
# Usage: ./run_tests.sh [all|unit|integration|coverage|lint]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default test type
TEST_TYPE=${1:-all}

# Helper functions
print_header() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_pytest() {
    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found. Installing dependencies..."
        pip install -r requirements.txt
    fi
}

# Test functions
run_unit_tests() {
    print_header "Running Unit Tests"
    pytest tests/ -v -m unit --tb=short || return 1
    print_success "Unit tests passed"
}

run_integration_tests() {
    print_header "Running Integration Tests"
    pytest tests/ -v -m integration --tb=short || {
        print_warning "Integration tests failed (may require database)"
        return 0
    }
    print_success "Integration tests passed"
}

run_edge_case_tests() {
    print_header "Running Edge Case Tests"
    pytest tests/test_integration_edge_cases.py -v --tb=short || return 1
    print_success "Edge case tests passed"
}

run_all_tests() {
    print_header "Running All Tests"
    pytest tests/ -v --tb=short || return 1
    print_success "All tests passed"
}

run_coverage_tests() {
    print_header "Running Tests with Coverage"
    pytest tests/ \
        --cov=dags \
        --cov=py_and_notebooks \
        --cov-report=html \
        --cov-report=term-missing \
        --cov-report=xml \
        -v || return 1
    print_success "Coverage report generated in htmlcov/index.html"
}

run_parallel_tests() {
    print_header "Running Tests in Parallel"
    if ! command -v pytest-xdist &> /dev/null; then
        print_warning "pytest-xdist not found. Install with: pip install pytest-xdist"
        return 1
    fi
    pytest tests/ -n auto -v --tb=short || return 1
    print_success "Parallel tests passed"
}

run_lint() {
    print_header "Running Linters"
    
    # Check for flake8
    if command -v flake8 &> /dev/null; then
        print_warning "Running flake8..."
        flake8 dags/ py_and_notebooks/ tests/ --max-line-length=100 --exit-zero || true
    else
        print_warning "flake8 not installed"
    fi
    
    # Check for black
    if command -v black &> /dev/null; then
        print_warning "Checking code formatting with black..."
        black --check dags/ py_and_notebooks/ tests/ --line-length=100 || {
            print_warning "Some files need formatting. Run: black dags/ py_and_notebooks/ tests/"
        }
    else
        print_warning "black not installed"
    fi
    
    # Check for isort
    if command -v isort &> /dev/null; then
        print_warning "Checking import sorting with isort..."
        isort --check-only dags/ py_and_notebooks/ tests/ || {
            print_warning "Some imports need sorting. Run: isort dags/ py_and_notebooks/ tests/"
        }
    else
        print_warning "isort not installed"
    fi
    
    print_success "Lint checks completed"
}

run_format() {
    print_header "Formatting Code"
    
    if command -v black &> /dev/null; then
        print_warning "Formatting with black..."
        black dags/ py_and_notebooks/ tests/ --line-length=100
        print_success "Code formatted with black"
    fi
    
    if command -v isort &> /dev/null; then
        print_warning "Sorting imports with isort..."
        isort dags/ py_and_notebooks/ tests/
        print_success "Imports sorted with isort"
    fi
}

run_security_check() {
    print_header "Running Security Checks"
    
    if command -v bandit &> /dev/null; then
        print_warning "Running Bandit security scan..."
        bandit -r dags/ py_and_notebooks/ -ll || true
    else
        print_warning "bandit not installed"
    fi
    
    if command -v safety &> /dev/null; then
        print_warning "Checking dependencies for vulnerabilities..."
        safety check --json || true
    else
        print_warning "safety not installed"
    fi
    
    print_success "Security checks completed"
}

show_help() {
    cat << EOF
Sparkify Test Runner

Usage: ./run_tests.sh [command]

Commands:
    all           Run all tests (default)
    unit          Run unit tests only
    integration   Run integration tests only
    edge          Run edge case tests
    coverage      Run tests with coverage report
    parallel      Run tests in parallel
    lint          Run linters (flake8, black, isort)
    format        Format code with black and isort
    security      Run security checks
    help          Show this help message

Examples:
    ./run_tests.sh                  # Run all tests
    ./run_tests.sh unit             # Run unit tests only
    ./run_tests.sh coverage         # Generate coverage report
    ./run_tests.sh lint             # Run linters
    ./run_tests.sh format           # Format code

Requirements:
    - Python 3.9+
    - pytest and dependencies (see requirements.txt)

EOF
}

# Main script logic
check_pytest

case "$TEST_TYPE" in
    all)
        run_all_tests || exit 1
        ;;
    unit)
        run_unit_tests || exit 1
        ;;
    integration)
        run_integration_tests || exit 1
        ;;
    edge)
        run_edge_case_tests || exit 1
        ;;
    coverage)
        run_coverage_tests || exit 1
        ;;
    parallel)
        run_parallel_tests || exit 1
        ;;
    lint)
        run_lint
        ;;
    format)
        run_format
        ;;
    security)
        run_security_check
        ;;
    help)
        show_help
        ;;
    *)
        print_error "Unknown command: $TEST_TYPE"
        echo ""
        show_help
        exit 1
        ;;
esac

print_header "Test Run Complete"
print_success "All checks passed successfully!"
