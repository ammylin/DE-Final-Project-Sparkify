# Sparkify Test Suite

Comprehensive test suite for the Sparkify music recommendation system CI/CD pipeline.

## Test Organization

### Test Files

1. **test_database_operations.py**
   - Tests for DAG #1 (training/embedding) database operations
   - Tests for `create_postgres_tables()`, `verify_postgres_tables()`, `generate_tracks_table()`, `generate_users()`, `generate_events_table()`
   - Data integrity validation tests

2. **test_recommendation_model.py**
   - Tests for recommendation model training
   - Tests for `build_track_matrix()`, `generate_user_vector()`, `train_and_save_recommendation_model()`
   - Model serialization and structure tests

3. **test_inference_operations.py**
   - Tests for DAG #2 (inference/scoring) operations
   - Tests for `create_recommendations_table()`, `fetch_random_user_and_history()`, `generate_recommendations()`
   - Cosine similarity scoring and recommendation filtering tests

4. **test_integration_edge_cases.py**
   - End-to-end pipeline integration tests
   - Edge cases and boundary condition tests
   - Error handling and resilience tests

5. **conftest.py**
   - Pytest configuration and shared fixtures
   - Provides reusable test data and mocks

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_database_operations.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_database_operations.py::TestDatabaseOperations -v
```

### Run Specific Test Function
```bash
pytest tests/test_database_operations.py::TestDatabaseOperations::test_create_postgres_tables_success -v
```

### Run Tests by Marker
```bash
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m slow
pytest tests/ -m database
```

### Run Tests with Coverage
```bash
pytest tests/ --cov=dags --cov=py_and_notebooks --cov-report=html
```

### Run Tests in Parallel
```bash
pytest tests/ -n auto
```

## Test Categories

### Unit Tests
- Individual function testing
- Data validation
- Error handling
- Data types and structure verification

### Integration Tests
- End-to-end pipeline flow
- Database operations (when test DB available)
- Model training and inference workflow

### Edge Case Tests
- Boundary conditions
- Large data volumes (10K+ users, 100K+ tracks)
- Empty or null data
- Special characters and unicode
- Concurrent requests

## Test Coverage

### Database Operations Coverage
- ✅ Table creation and verification
- ✅ Data loading from CSV
- ✅ User generation with preferences
- ✅ Event generation with constraints
- ✅ Foreign key integrity
- ✅ Data type validation

### Recommendation Model Coverage
- ✅ Track embedding generation
- ✅ Track matrix structure and shape
- ✅ User vector generation
- ✅ Missing value handling
- ✅ Model serialization
- ✅ User-track matching

### Inference Operations Coverage
- ✅ Recommendations table creation
- ✅ Random user selection
- ✅ User history fetching
- ✅ Similarity scoring (cosine)
- ✅ Score validation and range checks
- ✅ Duplicate filtering
- ✅ Top-K recommendations

### Data Integrity Coverage
- ✅ Null value handling
- ✅ Range validation (popularity 0-100, audio features 0-1)
- ✅ Audio feature ranges
- ✅ User age validation
- ✅ Timestamp ordering
- ✅ Foreign key consistency

## Fixtures Available

- `sample_tracks`: Sample DataFrame with 5 tracks and all audio features
- `sample_users`: Sample DataFrame with 10 users and genre preferences
- `sample_events`: Sample DataFrame with listening events
- `sample_recommendations`: Sample recommendations output
- `embedding_dimension`: Constant (64) for embedding tests
- `sample_embeddings`: Random track embeddings (100 x 64)
- `sample_user_vectors`: Random user vectors
- `mock_db_connection`: Mock database connection
- `temp_data_dir`: Temporary directory for test files
- `test_config`: Test configuration dictionary

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest tests/ --cov=dags --cov=py_and_notebooks
```

## Requirements

Add to `requirements.txt`:
```
pytest>=7.0
pytest-cov>=3.0
pytest-xdist>=2.5
pytest-timeout>=2.1
pytest-mock>=3.6
```

Install with:
```bash
pip install -r requirements.txt
```

## Best Practices

1. **Test Isolation**: Each test is independent and can run in any order
2. **Mocking**: External dependencies (PostgreSQL, file system) are mocked
3. **Fixtures**: Shared test data provided via pytest fixtures
4. **Clear Names**: Test names clearly describe what is being tested
5. **Assertions**: Each test has clear assertions with helpful messages
6. **Documentation**: Each test includes docstrings explaining the test purpose

## Adding New Tests

1. Create test function with `test_` prefix
2. Use descriptive names: `test_<function>_<scenario>`
3. Use fixtures for data setup
4. Add assertions with messages
5. Mark with appropriate marker (`@pytest.mark.unit`, etc.)

Example:
```python
@pytest.mark.unit
def test_recommendation_sorting(sample_recommendations):
    """Test that recommendations are sorted by score descending."""
    sorted_recs = sample_recommendations.sort_values('score', ascending=False)
    assert sorted_recs['score'].is_monotonic_decreasing
```

## Troubleshooting

### Tests Fail Due to Missing Dependencies
```bash
pip install -r requirements.txt
```

### PostgreSQL Connection Errors
Database operations are mocked by default in unit tests. For integration tests with real DB:
1. Ensure PostgreSQL is running
2. Set environment variables: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
3. Create test database: `createdb test_sparkify`

### Timeout Issues
Increase timeout in `pytest.ini`:
```ini
timeout = 600
```

### Memory Issues with Large Tests
Run tests sequentially:
```bash
pytest tests/ -n 1
```

## Contact

For questions about tests, contact the team or create an issue in the repository.
