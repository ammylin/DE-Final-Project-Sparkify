"""
Pytest configuration and shared fixtures for Sparkify tests
"""

import pytest
import pandas as pd
import numpy as np
import json
from datetime import datetime
import os


@pytest.fixture
def sample_tracks():
    """Fixture providing sample track data."""
    return pd.DataFrame({
        'track_id': ['t1', 't2', 't3', 't4', 't5'],
        'track_name': ['Song A', 'Song B', 'Song C', 'Song D', 'Song E'],
        'primary_artist': ['Artist 1', 'Artist 2', 'Artist 3', 'Artist 4', 'Artist 5'],
        'first_genre': ['pop', 'rock', 'pop', 'hip-hop', 'rock'],
        'popularity': [75, 65, 80, 70, 85],
        'duration_ms': [180000, 200000, 190000, 210000, 195000],
        'danceability': [0.7, 0.5, 0.8, 0.6, 0.4],
        'energy': [0.6, 0.8, 0.7, 0.9, 0.5],
        'key': [0, 1, 2, 3, 4],
        'loudness': [-5.0, -4.5, -5.5, -4.0, -6.0],
        'mode': [1, 0, 1, 1, 0],
        'speechiness': [0.03, 0.04, 0.02, 0.05, 0.01],
        'acousticness': [0.1, 0.2, 0.15, 0.05, 0.3],
        'instrumentalness': [0.0, 0.01, 0.02, 0.0, 0.1],
        'liveness': [0.1, 0.15, 0.12, 0.2, 0.08],
        'valence': [0.5, 0.4, 0.6, 0.7, 0.3],
        'tempo': [120, 140, 130, 150, 110],
        'time_signature': [4, 4, 4, 4, 3],
    })


@pytest.fixture
def sample_users():
    """Fixture providing sample user data."""
    genres = ['pop', 'rock', 'hip-hop', 'jazz', 'classical']
    users = []
    for i in range(10):
        genre_weights = {
            genre: np.random.uniform(0, 1)
            for genre in np.random.choice(genres, 3, replace=False)
        }
        users.append({
            'user_id': f'user_{i}',
            'age': np.random.randint(18, 80),
            'country': 'USA',
            'genre_weights': genre_weights,
        })
    return pd.DataFrame(users)


@pytest.fixture
def sample_events(sample_users, sample_tracks):
    """Fixture providing sample listening events."""
    events = []
    for user_id in sample_users['user_id']:
        for _ in range(5):
            event = {
                'event_id': f'event_{len(events)}',
                'user_id': user_id,
                'track_id': np.random.choice(sample_tracks['track_id']),
                'timestamp': pd.Timestamp.now(),
                'track_name': 'Sample Track',
                'primary_artist': 'Sample Artist',
            }
            events.append(event)
    return pd.DataFrame(events)


@pytest.fixture
def sample_recommendations(sample_users, sample_tracks):
    """Fixture providing sample recommendations."""
    recommendations = []
    for user_id in sample_users['user_id']:
        for track in sample_tracks['track_id'][:3]:
            recommendations.append({
                'user_id': user_id,
                'track_id': track,
                'track_name': 'Recommended Track',
                'score': np.random.rand(),
            })
    return pd.DataFrame(recommendations)


@pytest.fixture
def embedding_dimension():
    """Fixture providing embedding dimension constant."""
    return 64


@pytest.fixture
def sample_embeddings(embedding_dimension):
    """Fixture providing sample track embeddings."""
    n_tracks = 100
    return np.random.randn(n_tracks, embedding_dimension)


@pytest.fixture
def sample_user_vectors(embedding_dimension):
    """Fixture providing sample user vectors."""
    n_users = 50
    return {f'user_{i}': np.random.randn(embedding_dimension) for i in range(n_users)}


@pytest.fixture
def mock_db_connection():
    """Fixture providing mock database connection."""
    from unittest.mock import MagicMock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


@pytest.fixture
def temp_data_dir(tmp_path):
    """Fixture providing temporary directory for test data."""
    return tmp_path


@pytest.fixture
def test_config():
    """Fixture providing test configuration."""
    return {
        'db_name': 'test_sparkify',
        'db_user': 'test_user',
        'db_password': 'test_password',
        'db_host': 'localhost',
        'db_port': 5432,
        'model_pickle_path': '/tmp/test_model.pkl',
        'embedding_dimension': 64,
        'n_users': 100,
        'events_per_user': 20,
    }


# Pytest configuration options
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )


# Pytest hooks
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Hook to add test duration to report."""
    if call.when == "call":
        item.test_duration = call.stop - call.start
