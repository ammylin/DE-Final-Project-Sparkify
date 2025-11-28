# Sparkify Test Suite — Summary

This repository contains the automated tests used by the Sparkify recommendation project. The test suite currently runs **78 tests** across the test files.


Purpose:
- Explain how to run tests locally and in CI
- Provide a short overview of test organization and fixtures
- Provide quick troubleshooting tips

Summary
-------
- Total tests: **78**
- Test files: `tests/` (several files covering database, model, inference, and integration)
- Fixtures: defined in `tests/conftest.py`

Quick commands
--------------
Install dependencies (recommended inside a virtualenv):

This document consolidates all testing-related documentation for the Sparkify recommendation project into a single, comprehensive file. It covers the test scope, how to run tests locally and in CI, fixtures, common troubleshooting, and a verification checklist.

Table of contents
-----------------
1. Summary
2. Test modules & short descriptions
3. Fixtures and pytest markers
4. How to run tests (local)
5. Integration tests and Postgres
6. CI/CD notes
7. Troubleshooting
8. Verification checklist
9. Contribution guidelines for tests

## 1) Summary ##
----------
- Total tests (current): **78**
- Main test modules (under `tests/`):
	- `test_database_operations.py` — DB schema & data ops
	- `test_recommendation_model.py` — model & embeddings
	- `test_inference_operations.py` — inference pipeline
	- `test_integration_edge_cases.py` — end-to-end and edge cases

## 2) Test modules & short descriptions ##
-----------------------------------
- `tests/test_database_operations.py` (13 tests)
	- Validates SQL-based table creation, verification of table existence, CSV loading logic (tracks), synthetic user generation, events generation, and basic data validation (ranges, nulls).

- `tests/test_recommendation_model.py` (18 tests)
	- Validates track matrix and embedding construction, normalization of features, user vector construction from genre weights, model dict structure, and serialization (pickle) format.

- `tests/test_inference_operations.py` (19 tests)
	- Validates recommendation table creation SQL, fetch-and-filter behavior for user histories, recommendation structure (ids and scores), score range validation, sorting/top-k logic, duplicate prevention, cosine similarity calculations, and batch similarity utilities.

- `tests/test_integration_edge_cases.py` (28 tests)
	- End-to-end flow sanity checks (tracks → users → events → recommendations), duplicate handling, timestamp ordering and precision, large-scale count logic, error handling (missing fields, malformed JSON), retry logic simulation, and unicode/special-character handling.

### 2.1) Testing types — what each category means ###
--------------------------------------------
- **Unit tests** — Fast, isolated tests that validate a single function or small component in isolation. They use mocks for external dependencies (database, network, filesystem). Unit tests are ideal for checking logic such as data validation, filtering, sorting, and math/algorithm correctness. In this repo, most checks inside `test_inference_operations.py` and many in `test_recommendation_model.py` are written as unit tests.

- **Integration tests** — Tests that verify multiple components working together and may require external services (e.g., a PostgreSQL instance). They exercise DB reads/writes, SQL DDL/DML, and full pipeline steps without mocking the external service. Marked with `@pytest.mark.integration` in `conftest.py`. The heavier checks in `test_database_operations.py` and parts of `test_integration_edge_cases.py` are integration-style.

- **End-to-end (E2E)** — Full pipeline runs that simulate realistic usage from ingestion through model training and inference. These tests validate data flow, end-to-end correctness, and system-level behaviour. `test_integration_edge_cases.py` contains several E2E style checks (data flow sanity, event-to-recommendation mapping).


Mapping quick reference:
- Unit: fast checks — most functions in `test_inference_operations.py`, many in `test_recommendation_model.py`.
- Integration: database and multi-component tests — `test_database_operations.py`, selected tests in `test_integration_edge_cases.py`.
- E2E: full-data-flow checks — `test_integration_edge_cases.py`.

## 3) Fixtures & pytest markers ##
---------------------------
- All shared fixtures live in `tests/conftest.py` and include:
	- `sample_tracks`, `sample_users`, `sample_events`, `sample_recommendations`
	- `embedding_dimension`, `sample_embeddings`, `sample_user_vectors`
	- `mock_db_connection` (MagicMock conn + cursor), `temp_data_dir` (tmp_path), `test_config`
- Markers registered in `conftest.py`:
	- `unit`, `integration`, `slow`, `database`

## 4) How to run tests (local) ##
---------------------------
Recommended workflow (macOS / zsh):

```bash
# create + activate virtualenv
python3 -m venv .venv
source .venv/bin/activate

# install deps
pip install --upgrade pip
pip install -r requirements.txt

# run full suite
pytest tests/ -v

# run unit tests only
pytest tests/ -m unit -v

# run a single module
pytest tests/test_inference_operations.py -q

# run tests in parallel (requires pytest-xdist)
pytest tests/ -n auto -v
```

Convenience
-----------
- `./run_tests.sh` — helper script for common runs (unit/integration/coverage/lint)
- `Makefile` — targets `make test`, `make test-unit`, `make coverage`, `make lint`, etc.

## 5) Integration tests & Postgres ##
-------------------------------
- Unit tests use mocks; integration tests may require a running Postgres instance.

Example setup (macOS/Homebrew):

```bash
brew install postgresql
brew services start postgresql
createdb test_sparkify

export DB_NAME=test_sparkify
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=5432

# run integration tests
pytest tests/ -m integration -v
```

## 6) CI/CD notes ##
--------------
- The repo's GitHub Actions workflow should:
	- Set up Python, install deps, run unit tests
	- Optionally run integration tests on a self-hosted runner or tagged builds
	- Run linters and security scans if configured
	- Publish coverage reports (HTML / codecov) if desired


## 7) Troubleshooting ##
------------------
- `pytest` missing: `pip install pytest` inside activated venv.
- `psycopg2` build errors: install `psycopg2-binary` or `libpq` via Homebrew and add to PATH.
- Flaky time-based tests: mock timestamps or use deterministic time fixtures.
- Missing data files: ensure tests using file fixtures write to `tmp_path` during setup.

## 8) Verification checklist ##
-------------------------
- [ ] Activate venv and run `pip install -r requirements.txt`
- [ ] `pytest tests/ -v` completes with ~78 tests passing
- [ ] Generate coverage: `pytest tests/ --cov --cov-report=html` and open `htmlcov/index.html`
- [ ] Confirm CI passes for the branch in GitHub Actions

## 9) Contribution guidelines for tests ##
-----------------------------------
- Name test files `test_<feature>.py` and test functions `test_<unit>_<condition>`.
- Use fixtures for common setup and avoid global state.
- Mark tests requiring external services with `@pytest.mark.integration` or `@pytest.mark.database`.
- Keep tests small and focused; for heavy end-to-end checks, mark as `slow` or place under `integration`.


Last updated: November 28, 2025
