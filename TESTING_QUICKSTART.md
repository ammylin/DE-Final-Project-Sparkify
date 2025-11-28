# Sparkify Test Suite - Quick Start Guide

Get started with the Sparkify test suite in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- pip or conda

## Quick Setup (2 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Verify Installation
```bash
pytest --version
```

## Running Tests (3 minutes)

### Option 1: Using Makefile (Recommended)
```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run with coverage
make coverage

# See all available commands
make help
```

### Option 2: Using Bash Script
```bash
# Make script executable
chmod +x run_tests.sh

# Run all tests
./run_tests.sh all

# Run specific test type
./run_tests.sh unit
./run_tests.sh coverage
./run_tests.sh lint
```

### Option 3: Using pytest directly
```bash
# Run all tests
pytest tests/ -v

# Run specific file
pytest tests/test_database_operations.py -v

# Run with coverage
pytest tests/ --cov=dags --cov=py_and_notebooks --cov-report=html

# Run in parallel
pytest tests/ -n auto -v
```

## Understanding Test Organization

```
tests/
├── __init__.py                      # Package marker
├── conftest.py                      # Pytest fixtures & configuration
├── pytest.ini                       # Pytest settings
├── README.md                        # Detailed test documentation
│
├── test_database_operations.py      # DAG #1 tests (Training)
│   ├── TestDatabaseOperations       # Table creation, verification
│   └── TestDataIntegrity           # Data validation
│
├── test_recommendation_model.py     # Model training tests
│   ├── TestTrackEmbedding          # Track matrix generation
│   ├── TestUserEmbedding           # User vector generation
│   └── TestModelSerialization      # Model saving/loading
│
├── test_inference_operations.py     # DAG #2 tests (Inference)
│   ├── TestInferenceOperations     # Inference pipeline
│   ├── TestCosineSimilarityScoring # Similarity calculations
│   └── TestRecommendationFiltering # Filtering logic
│
└── test_integration_edge_cases.py   # Integration & edge cases
    ├── TestDataPipelineIntegration # End-to-end flow
    ├── TestEdgeCases               # Boundary conditions
    ├── TestBoundaryConditions      # Limits & constraints
    └── TestErrorHandling           # Error scenarios
```

## Test Coverage

- **71 total tests** covering:
  - Database operations ✅
  - Model training ✅
  - Inference/scoring ✅
  - Data integrity ✅
  - Edge cases ✅
  - Error handling ✅

## Common Test Commands

### Run Tests by Category
```bash
# Unit tests only
pytest tests/ -m unit

# Integration tests only
pytest tests/ -m integration

# Run specific test file
pytest tests/test_database_operations.py -v

# Run specific test class
pytest tests/test_database_operations.py::TestDatabaseOperations -v

# Run specific test function
pytest tests/test_database_operations.py::TestDatabaseOperations::test_create_postgres_tables_success -v
```

### Generate Reports
```bash
# Coverage report (HTML)
pytest tests/ --cov=dags --cov=py_and_notebooks --cov-report=html
# Open htmlcov/index.html in browser

# Coverage report (Terminal)
pytest tests/ --cov --cov-report=term-missing

# JUnit XML report (for CI/CD)
pytest tests/ --junit-xml=junit.xml
```

### Code Quality
```bash
# Format code
make format

# Run linters
make lint

# Security checks
make security

# Full CI pipeline
make ci
```

## Running Tests Locally vs CI/CD

### Local Development
```bash
# Quick checks (unit tests + lint)
make check

# Full test suite
pytest tests/ -v

# Watch for changes and re-run tests
ptw tests/
```

### CI/CD Pipeline (GitHub Actions)
Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request
- Multiple Python versions (3.9, 3.10, 3.11)

See `.github/workflows/ci-cd-tests.yml` for details.

## Test Data

### Using Fixtures
Tests use pytest fixtures for data setup:

```python
def test_with_sample_data(sample_tracks, sample_users):
    """Tests automatically receive sample data."""
    assert len(sample_tracks) == 5
    assert len(sample_users) == 10
```

Available fixtures:
- `sample_tracks`: 5 sample tracks with all audio features
- `sample_users`: 10 users with genre preferences
- `sample_events`: Listening events
- `sample_recommendations`: Recommendation outputs
- `embedding_dimension`: Constant (64)
- `test_config`: Configuration dictionary

See `tests/conftest.py` for all available fixtures.

## Troubleshooting

### Tests Won't Run
```bash
# Install dependencies
pip install -r requirements.txt

# Verify pytest
pytest --version
```

### Import Errors
```bash
# Add current directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

### Database Connection Errors
Most tests mock the database. For integration tests:
1. Ensure PostgreSQL is running
2. Create test database: `createdb test_sparkify`
3. Set environment variables:
   ```bash
   export DB_NAME=test_sparkify
   export DB_USER=postgres
   export DB_PASSWORD=password
   export DB_HOST=localhost
   export DB_PORT=5432
   ```

### Slow Tests
Run in parallel:
```bash
pytest tests/ -n auto  # Uses all CPU cores
```

## What Gets Tested

### DAG #1: Training Pipeline
✅ Database table creation and verification
✅ CSV data loading for tracks
✅ User generation (2000 synthetic users)
✅ Event generation (40K events)
✅ Model training and embeddings
✅ Model serialization/deserialization

### DAG #2: Inference Pipeline
✅ Recommendations table creation
✅ Random user selection
✅ User history fetching
✅ Similarity scoring (cosine)
✅ Top-K recommendations
✅ Score validation

### Data Integrity
✅ Range validation (popularity, audio features)
✅ Null value handling
✅ Type checking
✅ Foreign key consistency
✅ Timestamp ordering

### Edge Cases
✅ Single user/track
✅ Empty data
✅ Large datasets (10K+ users)
✅ Special characters & unicode
✅ Concurrent requests
✅ Error scenarios

## Next Steps

1. **Run tests locally**: `make test`
2. **Check coverage**: `make coverage`
3. **Review failing tests**: Check test output
4. **Add new tests**: See `tests/README.md`
5. **Set up CI/CD**: Commit to GitHub to trigger workflows

## Resources

- 📋 **Detailed Docs**: `tests/README.md`
- 🗺️ **Test Mapping**: `TEST_COVERAGE_MAPPING.md`
- 🔧 **Makefile**: `Makefile` (all available commands)
- 🚀 **CI/CD**: `.github/workflows/ci-cd-tests.yml`

## Support

- Questions about tests? See `tests/README.md`
- Project documentation? See `README.md`
- Test mapping? See `TEST_COVERAGE_MAPPING.md`

---

**Happy Testing!** 🎵
