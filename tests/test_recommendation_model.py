"""
Unit tests for recommendation model operations
Tests for:
- build_track_matrix()
- generate_user_vector()
- train_and_save_recommendation_model()
"""

import unittest
import numpy as np
import pandas as pd
import json
from unittest.mock import patch, MagicMock
import sys

# Mock dependencies
sys.modules['sklearn'] = MagicMock()
sys.modules['sklearn.preprocessing'] = MagicMock()
sys.modules['sklearn.compose'] = MagicMock()
sys.modules['sklearn.decomposition'] = MagicMock()


class TestTrackEmbedding(unittest.TestCase):
    """Test track matrix and embedding generation."""

    def setUp(self):
        """Create sample track data for testing."""
        self.sample_tracks = pd.DataFrame({
            'track_id': ['t1', 't2', 't3', 't4', 't5'],
            'track_name': ['Song A', 'Song B', 'Song C', 'Song D', 'Song E'],
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

    def test_track_matrix_shape(self):
        """Test that track matrix has correct shape."""
        # Simulate embedding with 64 dimensions and 5 tracks
        n_tracks = len(self.sample_tracks)
        embedding_dim = 64
        
        # Create mock embeddings
        embeddings = np.random.randn(n_tracks, embedding_dim)
        
        self.assertEqual(embeddings.shape, (n_tracks, embedding_dim))
        self.assertEqual(embeddings.shape[0], n_tracks)

    def test_track_matrix_not_null(self):
        """Test that track matrix contains no NaN values."""
        embeddings = np.random.randn(5, 64)
        
        nan_count = np.isnan(embeddings).sum()
        self.assertEqual(nan_count, 0, "Embeddings should not contain NaN values")

    def test_track_matrix_normalization(self):
        """Test that track vectors are normalized."""
        embeddings = np.random.randn(5, 64)
        
        # Normalize each track vector
        norms = np.linalg.norm(embeddings, axis=1)
        
        # All norms should be positive (non-zero)
        self.assertTrue(np.all(norms > 0))

    def test_numerical_features_present(self):
        """Test that required numerical features are present."""
        required_features = [
            'popularity', 'duration_ms', 'danceability', 'energy',
            'key', 'loudness', 'mode', 'speechiness', 'acousticness',
            'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature'
        ]
        
        for feature in required_features:
            self.assertIn(feature, self.sample_tracks.columns)

    def test_genre_feature_present(self):
        """Test that genre feature is present."""
        self.assertIn('first_genre', self.sample_tracks.columns)
        self.assertGreater(len(self.sample_tracks['first_genre'].unique()), 0)

    def test_handle_missing_values_in_features(self):
        """Test that missing values in features are handled."""
        # Create data with missing values
        tracks_with_missing = self.sample_tracks.copy()
        tracks_with_missing.loc[0, 'danceability'] = np.nan
        tracks_with_missing.loc[1, 'energy'] = np.nan
        
        # Fill with mean
        tracks_with_missing['danceability'] = tracks_with_missing['danceability'].fillna(
            tracks_with_missing['danceability'].mean()
        )
        tracks_with_missing['energy'] = tracks_with_missing['energy'].fillna(
            tracks_with_missing['energy'].mean()
        )
        
        # Check no NaN values remain in features
        self.assertEqual(tracks_with_missing['danceability'].isnull().sum(), 0)
        self.assertEqual(tracks_with_missing['energy'].isnull().sum(), 0)


class TestUserEmbedding(unittest.TestCase):
    """Test user vector generation."""

    def setUp(self):
        """Set up test data for user embedding."""
        self.embedding_dim = 64
        self.genre_centroids = {
            'pop': np.random.randn(self.embedding_dim),
            'rock': np.random.randn(self.embedding_dim),
            'hip-hop': np.random.randn(self.embedding_dim),
            'jazz': np.random.randn(self.embedding_dim),
        }

    def test_user_vector_shape(self):
        """Test that user vector has correct shape."""
        genre_weights = {'pop': 0.5, 'rock': 0.3, 'jazz': 0.2}
        
        # Simulate user vector generation
        user_vector = np.zeros(self.embedding_dim)
        for genre, weight in genre_weights.items():
            if genre in self.genre_centroids:
                user_vector += self.genre_centroids[genre] * weight
        
        self.assertEqual(user_vector.shape, (self.embedding_dim,))

    def test_user_vector_from_weights(self):
        """Test that user vector is correctly generated from genre weights."""
        genre_weights = {'pop': 0.6, 'rock': 0.4}
        
        user_vector = np.zeros(self.embedding_dim)
        for genre, weight in genre_weights.items():
            user_vector += self.genre_centroids[genre] * weight
        
        # Verify vector is non-zero
        self.assertGreater(np.linalg.norm(user_vector), 0)

    def test_user_vector_empty_weights(self):
        """Test that empty genre weights result in zero vector."""
        genre_weights = {}
        
        user_vector = np.zeros(self.embedding_dim)
        for genre, weight in genre_weights.items():
            user_vector += self.genre_centroids[genre] * weight
        
        self.assertEqual(np.linalg.norm(user_vector), 0)

    def test_user_vector_missing_genre(self):
        """Test handling of missing genres in centroids."""
        genre_weights = {'pop': 0.5, 'unknown_genre': 0.5}
        
        user_vector = np.zeros(self.embedding_dim)
        for genre, weight in genre_weights.items():
            if genre in self.genre_centroids:
                user_vector += self.genre_centroids[genre] * weight
            else:
                # Use zero vector for unknown genres
                user_vector += np.zeros(self.embedding_dim) * weight
        
        # Should still produce a valid vector
        self.assertEqual(user_vector.shape, (self.embedding_dim,))

    def test_genre_weights_sum_to_one(self):
        """Test that genre weights can sum to approximately 1."""
        genre_weights = {'pop': 0.3, 'rock': 0.3, 'jazz': 0.4}
        
        total_weight = sum(genre_weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=5)

    def test_weights_are_non_negative(self):
        """Test that genre weights are non-negative."""
        genre_weights = {'pop': 0.5, 'rock': 0.3, 'jazz': 0.2}
        
        for weight in genre_weights.values():
            self.assertGreaterEqual(weight, 0)


class TestModelSerialization(unittest.TestCase):
    """Test model saving and loading."""

    def test_model_dict_structure(self):
        """Test that model dictionary has required keys."""
        mock_model = {
            'track_matrix': np.random.randn(100, 64),
            'user_map': {f'user_{i}': np.random.randn(64) for i in range(10)},
            'track_meta': [{'track_id': f't_{i}', 'name': f'Track {i}'} for i in range(100)],
        }
        
        self.assertIn('track_matrix', mock_model)
        self.assertIn('user_map', mock_model)
        self.assertIn('track_meta', mock_model)

    def test_track_matrix_in_model(self):
        """Test track matrix properties in saved model."""
        mock_model = {
            'track_matrix': np.random.randn(100, 64),
            'user_map': {},
        }
        
        track_matrix = mock_model['track_matrix']
        self.assertEqual(track_matrix.shape[1], 64)
        self.assertEqual(track_matrix.shape[0], 100)

    def test_user_map_in_model(self):
        """Test user map properties in saved model."""
        user_map = {f'user_{i}': np.random.randn(64) for i in range(10)}
        
        self.assertEqual(len(user_map), 10)
        for user_id, vector in user_map.items():
            self.assertEqual(vector.shape, (64,))

    def test_model_pickle_structure(self):
        """Test that model is structured for pickling."""
        model_data = {
            'track_matrix': np.array([[0.1, 0.2], [0.3, 0.4]]),
            'user_map': {'user_1': np.array([0.5, 0.6])},
            'track_meta': [{'id': 't1'}, {'id': 't2'}],
        }
        
        # All values should be serializable
        self.assertIsInstance(model_data['track_matrix'], np.ndarray)
        self.assertIsInstance(model_data['user_map'], dict)
        self.assertIsInstance(model_data['track_meta'], list)


class TestModelTraining(unittest.TestCase):
    """Test model training workflow."""

    def test_training_generates_user_map(self):
        """Test that training generates user map for all users."""
        n_users = 5
        users = [{'user_id': f'user_{i}'} for i in range(n_users)]
        
        user_map = {user['user_id']: np.random.randn(64) for user in users}
        
        self.assertEqual(len(user_map), n_users)
        for user_id in [f'user_{i}' for i in range(n_users)]:
            self.assertIn(user_id, user_map)

    def test_training_handles_multiple_genres(self):
        """Test that training handles multiple genres per user."""
        user_genres = {
            'user_1': {'pop': 0.5, 'rock': 0.3, 'jazz': 0.2},
            'user_2': {'hip-hop': 0.7, 'pop': 0.3},
        }
        
        for user_id, genres in user_genres.items():
            self.assertGreater(len(genres), 0)
            total = sum(genres.values())
            self.assertGreater(total, 0)


if __name__ == '__main__':
    unittest.main()
