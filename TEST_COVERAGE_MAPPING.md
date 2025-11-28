# Sparkify Test Coverage Mapping

This document maps the test suite to the project plan requirements for DAG #1 (training) and DAG #2 (inference).

## Project Plan Requirements vs Test Coverage

### DAG #1: Training/Embedding Pipeline (`music_data_pipeline`)

#### 1. Create Empty Tables
**Function:** `create_postgres_tables()`

**Tests:**
- `test_database_operations.py::TestDatabaseOperations::test_create_postgres_tables_success`
  - Verifies table creation SQL is executed
  - Validates connection handling
  
- `test_database_operations.py::TestDatabaseOperations::test_verify_postgres_tables_all_exist`
  - Confirms all three required tables exist after creation
  - Tests: `music_analytics.tracks`, `music_analytics.users`, `music_analytics.listening_events`

**Expected Behavior:**
- Creates schema `music_analytics` if not exists
- Creates 3 tables with proper columns
- Sets up foreign key constraints
- Enables PostgreSQL vector extension

---

#### 2. Verify Tables Exist
**Function:** `verify_postgres_tables()`

**Tests:**
- `test_database_operations.py::TestDatabaseOperations::test_verify_postgres_tables_all_exist`
  - All required tables present
  
- `test_database_operations.py::TestDatabaseOperations::test_verify_postgres_tables_missing_tables`
  - Detects when tables are missing
  - Raises appropriate error

**Expected Behavior:**
- Queries `information_schema.tables`
- Confirms 3 tables exist
- Returns error if any missing

---

#### 3. Generate Tracks Table
**Function:** `generate_tracks_table()`

**Tests:**
- `test_database_operations.py::TestDatabaseOperations::test_generate_tracks_table_csv_loading`
  - Loads CSV data correctly
  - Preserves all required columns
  
- `test_database_operations.py::TestDataIntegrity::test_popularity_score_range`
  - Validates popularity is 0-100
  
- `test_database_operations.py::TestDataIntegrity::test_audio_features_in_valid_range`
  - Audio features are 0-1 range

**Expected Behavior:**
- Reads from `data/cleaned_spotify_tracks.csv`
- Loads ~500K Spotify tracks
- Inserts into `music_analytics.tracks` table
- Preserves all audio features

---

#### 4. Generate Users Table
**Function:** `generate_users(n_users=2000)`

**Tests:**
- `test_database_operations.py::TestDatabaseOperations::test_generate_users_creates_correct_count`
  - Creates exactly 2000 users
  - Each user has unique ID
  
- `test_database_operations.py::TestDatabaseOperations::test_generate_users_has_valid_genres`
  - Genre preferences are populated
  - Weights are valid (0-1)
  
- `test_recommendation_model.py::TestUserEmbedding::test_genre_weights_sum_to_one`
  - Genre weights sum to ~1.0
  
- `test_recommendation_model.py::TestUserEmbedding::test_weights_are_non_negative`
  - All weights are >= 0

**Expected Behavior:**
- Creates 2000 synthetic users
- Each user has realistic preference profile
- Users have age, country, favorite genres
- Genre weights reflect user taste

**Sample User:**
```json
{
  "user_id": "user_1",
  "age": 32,
  "country": "USA",
  "favorite_genres": ["pop", "rock", "hip-hop"],
  "genre_weights": {"pop": 0.5, "rock": 0.3, "hip-hop": 0.2}
}
```

---

#### 5. Generate Events Table
**Function:** `generate_events_table(events_per_user=20)`

**Tests:**
- `test_database_operations.py::TestDatabaseOperations::test_generate_events_table_structure`
  - Events have correct structure
  - All required fields present
  
- `test_database_operations.py::TestDatabaseOperations::test_events_per_user_constraint`
  - Exactly 20 events per user
  - 2000 users × 20 = 40,000 total events
  
- `test_database_operations.py::TestDatabaseOperations::test_foreign_key_integrity`
  - All user_ids reference valid users
  - All track_ids reference valid tracks
  
- `test_integration_edge_cases.py::TestDataPipelineIntegration::test_pipeline_handles_duplicate_events`
  - Duplicate events allowed (user can play song multiple times)

**Expected Behavior:**
- Generates 40,000 listening events
- Each event has timestamp, user, track
- Events distributed across users and tracks
- Simulates realistic listening patterns

---

#### 6. Train Recommendation Model
**Function:** `train_and_save_recommendation_model()`

**Tests:**
- `test_recommendation_model.py::TestTrackEmbedding::test_track_matrix_shape`
  - Creates embedding matrix (500K tracks × 64 dimensions)
  
- `test_recommendation_model.py::TestTrackEmbedding::test_track_matrix_not_null`
  - No NaN values in embeddings
  
- `test_recommendation_model.py::TestUserEmbedding::test_user_vector_shape`
  - User vectors are 64-dimensional
  
- `test_recommendation_model.py::TestModelSerialization::test_model_dict_structure`
  - Model has `track_matrix`, `user_map`, `track_meta` keys
  
- `test_recommendation_model.py::TestModelTraining::test_training_generates_user_map`
  - Creates vector for each of 2000 users

**Expected Behavior:**
- Uses PCA to create 64-dimensional embeddings
- Builds track matrix from audio features + genre
- Generates user vectors from genre preferences
- Saves model as pickle file: `recommendation_model.pkl`

**Model Structure:**
```python
{
    'track_matrix': np.array(500000, 64),  # All track embeddings
    'user_map': {'user_0': vector, ...},   # User embeddings
    'track_meta': [{...}, ...],             # Track metadata
}
```

---

### DAG #2: Inference/Scoring Pipeline

#### 1. Create Recommendations Table
**Function:** `create_recommendations_table()`

**Tests:**
- `test_inference_operations.py::TestInferenceOperations::test_create_recommendations_table_sql_valid`
  - SQL syntax is valid
  - All required columns present
  
- `test_inference_operations.py::TestInferenceOperations::test_recommendations_table_structure`
  - Structure: recommendation_id, user_id, track_id, score

**Expected Behavior:**
- Creates `music_analytics.recommendations` table
- Columns: recommendation_id, user_id, track_id, track_name, score, timestamp

---

#### 2. Fetch Random User and History
**Function:** `fetch_random_user_and_history()`

**Tests:**
- `test_inference_operations.py::TestInferenceOperations::test_fetch_random_user_context_structure`
  - Returns valid context dict
  
- `test_inference_operations.py::TestInferenceOperations::test_fetch_random_user_excludes_history`
  - Listened tracks excluded from recommendations

**Expected Behavior:**
- Randomly selects one user
- Fetches their listening history
- Returns user_id and listened_track_ids

---

#### 3. Generate Recommendations
**Function:** `generate_recommendations(user_context, top_k=10)`

**Tests:**
- `test_inference_operations.py::TestInferenceOperations::test_generate_recommendations_returns_valid_structure`
  - Returns top-10 recommendations
  
- `test_inference_operations.py::TestInferenceOperations::test_recommendations_scores_in_valid_range`
  - Scores are 0-1 range
  
- `test_inference_operations.py::TestInferenceOperations::test_recommendations_sorted_by_score`
  - Results sorted by score descending
  
- `test_inference_operations.py::TestCosineSimilarityScoring::test_cosine_similarity_calculation`
  - Cosine similarity correctly calculated
  
- `test_inference_operations.py::TestRecommendationFiltering::test_filter_already_listened_tracks`
  - Excludes already-heard tracks

**Expected Behavior:**
- Loads saved model from pickle
- Calculates cosine similarity between user vector and all track vectors
- Filters out already-listened tracks
- Returns top 10 recommendations with scores
- Scores reflect combined factors: genre preference, similarity, popularity

---

#### 4. Insert Recommendations
**Function:** (Implicit in DAG)

**Tests:**
- `test_inference_operations.py::TestInferenceOperations::test_insert_recommendations_creates_valid_records`
  - Records have valid structure for insertion
  
- `test_inference_operations.py::TestInferenceOperations::test_no_duplicate_recommendations_per_user`
  - No duplicate track recommendations

**Expected Behavior:**
- Inserts 10 recommendations per inference run
- Each record has unique recommendation_id
- Stores user_id, track_id, track_name, score, timestamp

---

## Test Coverage Summary

### By Component

| Component | # Tests | Status |
|-----------|---------|--------|
| Database Operations | 11 | ✅ |
| Recommendation Model | 15 | ✅ |
| Inference Operations | 15 | ✅ |
| Integration & Edge Cases | 30 | ✅ |
| **TOTAL** | **71** | ✅ |

### By Test Type

| Type | Count |
|------|-------|
| Unit Tests | 60 |
| Integration Tests | 8 |
| Edge Case Tests | 3 |
| **Total** | 71 |

## Test Execution

### Run All Tests
```bash
pytest tests/ -v
```

### Run Tests for DAG #1
```bash
pytest tests/test_database_operations.py tests/test_recommendation_model.py -v
```

### Run Tests for DAG #2
```bash
pytest tests/test_inference_operations.py -v
```

### Generate Coverage Report
```bash
pytest tests/ --cov=dags --cov=py_and_notebooks --cov-report=html
```

## Continuous Integration

GitHub Actions workflow (`.github/workflows/ci-cd-tests.yml`) runs:
1. **Linting** (flake8, black, isort)
2. **Unit Tests** (Python 3.9, 3.10, 3.11)
3. **Integration Tests** (with warnings if DB unavailable)
4. **Coverage Report** (uploaded to Codecov)
5. **Security Scan** (bandit, safety)

## Testing Best Practices

1. **Isolation**: Each test is independent
2. **Mocking**: External dependencies mocked
3. **Fixtures**: Shared test data via pytest fixtures
4. **Assertions**: Clear, descriptive assertions
5. **Documentation**: Each test has docstring explaining purpose

## Next Steps

1. ✅ Create test infrastructure
2. ✅ Write unit tests for all DAG functions
3. ✅ Add integration tests (with test database)
4. ✅ Set up CI/CD workflow
5. 📋 Create test database fixtures for integration testing
6. 📋 Add performance benchmarks for embedding generation
7. 📋 Add load testing for recommendation generation at scale

## Questions?

See `tests/README.md` for detailed testing documentation.
