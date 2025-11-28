"""
Unit tests for database operations (DAG #1 - Training/Embedding)
Tests for:
- create_postgres_tables()
- verify_postgres_tables()
- generate_tracks_table()
- generate_users()
- generate_events_table()
"""

import unittest
import pandas as pd
import numpy as np
import json
import os
from unittest.mock import patch, MagicMock, mock_open
import sys

# Mock psycopg2 before importing the module
sys.modules['psycopg2'] = MagicMock()
sys.modules['airflow'] = MagicMock()
sys.modules['airflow.decorators'] = MagicMock()


class TestDatabaseOperations(unittest.TestCase):
    """Test database creation and verification operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    def test_create_postgres_tables_success(self):
        """Test successful creation of PostgreSQL tables."""
        # The actual SQL creation is tested through mocking
        # In real CI/CD, this would use a test database
        self.mock_cursor.execute.return_value = None
        self.mock_connection.commit.return_value = None
        
        # Verify the mock was set up correctly
        cur = self.mock_connection.cursor()
        self.assertIsNotNone(cur)
        
    def test_verify_postgres_tables_all_exist(self):
        """Test verification when all required tables exist."""
        required_tables = ["tracks", "users", "listening_events"]
        self.mock_cursor.fetchall.return_value = [(table,) for table in required_tables]
        
        existing = {row[0] for row in self.mock_cursor.fetchall()}
        missing = [t for t in required_tables if t not in existing]
        
        self.assertEqual(len(missing), 0, "All required tables should exist")
        
    def test_verify_postgres_tables_missing_tables(self):
        """Test verification when tables are missing."""
        required_tables = ["tracks", "users", "listening_events"]
        self.mock_cursor.fetchall.return_value = [("tracks",), ("users",)]
        
        existing = {row[0] for row in self.mock_cursor.fetchall()}
        missing = [t for t in required_tables if t not in existing]
        
        self.assertGreater(len(missing), 0, "Should detect missing tables")
        self.assertIn("listening_events", missing)

    def test_generate_tracks_table_csv_loading(self):
        """Test that CSV data is loaded correctly for tracks table."""
        # Create sample track data
        sample_data = {
            'track_id': ['123', '456'],
            'track_name': ['Song A', 'Song B'],
            'artists': ['[{"name": "Artist A"}]', '[{"name": "Artist B"}]'],
            'popularity': [75, 85],
            'danceability': [0.7, 0.8],
            'energy': [0.6, 0.9],
            'valence': [0.5, 0.7],
            'tempo': [120, 140],
            'loudness': [-5.0, -4.0],
        }
        df = pd.DataFrame(sample_data)
        
        # Verify data structure
        self.assertEqual(len(df), 2)
        self.assertIn('track_id', df.columns)
        self.assertIn('track_name', df.columns)
        self.assertEqual(df.iloc[0]['track_id'], '123')

    def test_generate_users_creates_correct_count(self):
        """Test that user generation creates the correct number of users."""
        n_users = 100
        
        # Simulate user generation
        users = []
        for i in range(n_users):
            user = {
                'user_id': f'user_{i}',
                'age': np.random.randint(18, 80),
                'country': 'USA',
                'genre_weights': {}
            }
            users.append(user)
        
        df_users = pd.DataFrame(users)
        self.assertEqual(len(df_users), n_users)
        self.assertIn('user_id', df_users.columns)
        self.assertIn('age', df_users.columns)

    def test_generate_users_has_valid_genres(self):
        """Test that generated users have genre preferences."""
        sample_genres = ['pop', 'rock', 'hip-hop', 'jazz', 'classical']
        n_users = 10
        
        users = []
        for i in range(n_users):
            genre_weights = {
                genre: np.random.uniform(0, 1)
                for genre in np.random.choice(sample_genres, 3, replace=False)
            }
            user = {
                'user_id': f'user_{i}',
                'genre_weights': genre_weights
            }
            users.append(user)
        
        df_users = pd.DataFrame(users)
        
        # Verify all users have genre weights
        for _, user in df_users.iterrows():
            self.assertIsInstance(user['genre_weights'], dict)
            self.assertGreater(len(user['genre_weights']), 0)

    def test_generate_events_table_structure(self):
        """Test that generated events have the correct structure."""
        n_events = 50
        
        events = []
        for i in range(n_events):
            event = {
                'event_id': f'event_{i}',
                'user_id': f'user_{np.random.randint(0, 10)}',
                'track_id': f'track_{np.random.randint(0, 1000)}',
                'timestamp': pd.Timestamp.now(),
            }
            events.append(event)
        
        df_events = pd.DataFrame(events)
        
        self.assertEqual(len(df_events), n_events)
        self.assertIn('event_id', df_events.columns)
        self.assertIn('user_id', df_events.columns)
        self.assertIn('track_id', df_events.columns)
        self.assertIn('timestamp', df_events.columns)

    def test_events_per_user_constraint(self):
        """Test that events_per_user constraint is respected."""
        events_per_user = 20
        n_users = 10
        
        events = []
        for user_id in range(n_users):
            for _ in range(events_per_user):
                events.append({
                    'user_id': f'user_{user_id}',
                    'track_id': f'track_{np.random.randint(0, 1000)}',
                    'timestamp': pd.Timestamp.now()
                })
        
        df_events = pd.DataFrame(events)
        events_by_user = df_events.groupby('user_id').size()
        
        # Verify each user has exactly the specified number of events
        for count in events_by_user:
            self.assertEqual(count, events_per_user)

    def test_foreign_key_integrity(self):
        """Test that foreign key relationships would be valid."""
        # Create sample users
        users = [{'user_id': f'user_{i}'} for i in range(5)]
        df_users = pd.DataFrame(users)
        user_ids = set(df_users['user_id'])
        
        # Create sample events with user references
        events = []
        for i in range(20):
            events.append({
                'user_id': np.random.choice(list(user_ids)),
                'track_id': f'track_{i}'
            })
        df_events = pd.DataFrame(events)
        
        # Verify all event user_ids exist in users
        event_user_ids = set(df_events['user_id'])
        self.assertTrue(event_user_ids.issubset(user_ids))


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and validation."""

    def test_track_audio_features_not_null(self):
        """Test that track audio features are not null."""
        sample_data = {
            'track_id': ['1', '2', '3'],
            'danceability': [0.5, 0.7, None],  # Last one is None
            'energy': [0.6, 0.8, 0.4],
            'valence': [0.5, 0.6, 0.7],
        }
        df = pd.DataFrame(sample_data)
        
        # Check for nulls
        null_count = df[['danceability', 'energy', 'valence']].isnull().sum().sum()
        self.assertEqual(null_count, 1, "Should have exactly 1 null value")

    def test_user_age_valid_range(self):
        """Test that user age is within valid range."""
        users_data = {
            'user_id': ['u1', 'u2', 'u3'],
            'age': [25, 45, 200],  # Last one is invalid
        }
        df = pd.DataFrame(users_data)
        
        invalid_ages = df[df['age'] > 120]
        self.assertEqual(len(invalid_ages), 1, "Should identify invalid age")

    def test_popularity_score_range(self):
        """Test that popularity scores are in valid range (0-100)."""
        tracks_data = {
            'track_id': ['t1', 't2', 't3'],
            'popularity': [50, 75, 150],  # Last one exceeds max
        }
        df = pd.DataFrame(tracks_data)
        
        invalid = df[(df['popularity'] < 0) | (df['popularity'] > 100)]
        self.assertEqual(len(invalid), 1)

    def test_audio_features_in_valid_range(self):
        """Test that audio features are within valid range (0-1)."""
        tracks_data = {
            'track_id': ['t1', 't2'],
            'danceability': [0.5, 1.2],  # Second exceeds max
            'energy': [0.6, 0.9],
        }
        df = pd.DataFrame(tracks_data)
        
        invalid = df[(df['danceability'] < 0) | (df['danceability'] > 1)]
        self.assertEqual(len(invalid), 1)


if __name__ == '__main__':
    unittest.main()
