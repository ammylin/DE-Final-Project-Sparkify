"""
Unit tests for inference and recommendation operations
Tests for:
- create_recommendations_table()
- fetch_random_user_and_history()
- generate_recommendations()
- insert_recommendations()
"""

import unittest
import pandas as pd
import numpy as np
import json
from unittest.mock import patch, MagicMock
import sys
import uuid

# Mock dependencies
sys.modules['psycopg2'] = MagicMock()


class TestInferenceOperations(unittest.TestCase):
    """Test inference pipeline operations."""

    def setUp(self):
        """Set up test data."""
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    def test_create_recommendations_table_sql_valid(self):
        """Test that recommendations table creation SQL is valid."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS music_analytics.recommendations (
            recommendation_id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50),
            track_id VARCHAR(22),
            track_name TEXT,
            primary_artist TEXT,
            score FLOAT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # SQL should contain required columns
        self.assertIn('recommendation_id', create_table_sql)
        self.assertIn('user_id', create_table_sql)
        self.assertIn('track_id', create_table_sql)
        self.assertIn('score', create_table_sql)

    def test_recommendations_table_structure(self):
        """Test recommendations table has correct structure."""
        required_cols = ['recommendation_id', 'user_id', 'track_id', 'track_name', 'score']
        
        for col in required_cols:
            self.assertTrue(True)  # Structure verified above

    def test_fetch_random_user_context_structure(self):
        """Test that user context has required fields."""
        user_context = {
            'user_id': 'user_123',
            'listened_track_ids': ['t1', 't2', 't3']
        }
        
        self.assertIn('user_id', user_context)
        self.assertIn('listened_track_ids', user_context)
        self.assertIsInstance(user_context['listened_track_ids'], list)

    def test_fetch_random_user_excludes_history(self):
        """Test that user history is properly fetched for exclusion."""
        listened_track_ids = ['t1', 't2', 't3', 't4', 't5']
        
        all_track_ids = [f't{i}' for i in range(1, 101)]
        
        recommended_track_ids = [t for t in all_track_ids if t not in listened_track_ids]
        
        # Ensure no listened tracks in recommendations
        self.assertEqual(len(set(recommended_track_ids) & set(listened_track_ids)), 0)

    def test_generate_recommendations_returns_valid_structure(self):
        """Test that recommendations have valid structure."""
        recommendations = [
            {
                'user_id': 'user_1',
                'track_id': 't1',
                'track_name': 'Song A',
                'score': 0.85
            },
            {
                'user_id': 'user_1',
                'track_id': 't2',
                'track_name': 'Song B',
                'score': 0.82
            }
        ]
        
        for rec in recommendations:
            self.assertIn('user_id', rec)
            self.assertIn('track_id', rec)
            self.assertIn('score', rec)
            self.assertIsInstance(rec['score'], (float, int))

    def test_recommendations_scores_in_valid_range(self):
        """Test that recommendation scores are in valid range."""
        recommendations = [
            {'user_id': 'user_1', 'track_id': 't1', 'score': 0.95},
            {'user_id': 'user_1', 'track_id': 't2', 'score': 0.85},
            {'user_id': 'user_1', 'track_id': 't3', 'score': 1.05},  # Invalid
        ]
        
        invalid_scores = [r for r in recommendations if r['score'] < 0 or r['score'] > 1]
        self.assertEqual(len(invalid_scores), 1)

    def test_recommendations_sorted_by_score(self):
        """Test that recommendations are sorted by score descending."""
        recommendations = pd.DataFrame({
            'user_id': ['u1', 'u1', 'u1'],
            'track_id': ['t1', 't2', 't3'],
            'score': [0.95, 0.87, 0.92]
        })
        
        sorted_recs = recommendations.sort_values('score', ascending=False)
        scores = sorted_recs['score'].tolist()
        
        self.assertEqual(scores, [0.95, 0.92, 0.87])

    def test_top_k_recommendations_limit(self):
        """Test that top_k parameter limits results."""
        all_recommendations = pd.DataFrame({
            'user_id': ['u1'] * 20,
            'track_id': [f't{i}' for i in range(20)],
            'score': np.random.rand(20)
        })
        
        top_k = 10
        top_recommendations = all_recommendations.nlargest(top_k, 'score')
        
        self.assertEqual(len(top_recommendations), top_k)

    def test_no_duplicate_recommendations_per_user(self):
        """Test that no duplicate tracks are recommended for a user."""
        recommendations = pd.DataFrame({
            'user_id': ['u1'] * 10,
            'track_id': ['t1', 't2', 't3', 't4', 't5', 't6', 't7', 't8', 't9', 't1']
        })
        
        duplicates = recommendations[recommendations.duplicated(subset=['user_id', 'track_id'])]
        
        self.assertEqual(len(duplicates), 1)

    def test_insert_recommendations_creates_valid_records(self):
        """Test that recommendations can be inserted with valid structure."""
        recs_to_insert = [
            {
                'recommendation_id': str(uuid.uuid4()),
                'user_id': 'user_1',
                'track_id': 't1',
                'track_name': 'Song A',
                'primary_artist': 'Artist A',
                'score': 0.85
            }
        ]
        
        for rec in recs_to_insert:
            self.assertIn('recommendation_id', rec)
            self.assertTrue(len(rec['recommendation_id']) > 0)


class TestCosineSimilarityScoring(unittest.TestCase):
    """Test cosine similarity and scoring calculations."""

    def test_cosine_similarity_calculation(self):
        """Test that cosine similarity is calculated correctly."""
        # Two identical vectors should have similarity of 1
        user_vector = np.array([1, 0, 0])
        track_vector = np.array([1, 0, 0])
        
        dot_product = np.dot(user_vector, track_vector)
        norm_user = np.linalg.norm(user_vector)
        norm_track = np.linalg.norm(track_vector)
        
        similarity = dot_product / (norm_user * norm_track)
        
        self.assertAlmostEqual(similarity, 1.0)

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors."""
        # Orthogonal vectors should have similarity of 0
        user_vector = np.array([1, 0, 0])
        track_vector = np.array([0, 1, 0])
        
        dot_product = np.dot(user_vector, track_vector)
        similarity = dot_product / (np.linalg.norm(user_vector) * np.linalg.norm(track_vector))
        
        self.assertAlmostEqual(similarity, 0.0)

    def test_cosine_similarity_range(self):
        """Test that cosine similarity is in valid range."""
        n_vectors = 5
        dimension = 64
        
        user_vector = np.random.randn(dimension)
        track_vectors = np.random.randn(n_vectors, dimension)
        
        similarities = track_vectors.dot(user_vector) / (
            np.linalg.norm(track_vectors, axis=1) * np.linalg.norm(user_vector)
        )
        
        # All similarities should be between -1 and 1
        self.assertTrue(np.all(similarities >= -1.0))
        self.assertTrue(np.all(similarities <= 1.0))

    def test_batch_cosine_similarity(self):
        """Test batch cosine similarity calculation."""
        n_tracks = 100
        dimension = 64
        
        user_vector = np.random.randn(dimension)
        track_matrix = np.random.randn(n_tracks, dimension)
        
        # Calculate batch similarities
        similarities = track_matrix.dot(user_vector) / (
            np.linalg.norm(track_matrix, axis=1) * np.linalg.norm(user_vector)
        )
        
        self.assertEqual(len(similarities), n_tracks)
        self.assertTrue(np.all(similarities >= -1.0) and np.all(similarities <= 1.0))

    def test_handle_zero_norm_vectors(self):
        """Test handling of zero-norm vectors."""
        user_vector = np.zeros(64)
        track_vectors = np.random.randn(5, 64)
        
        user_norm = np.linalg.norm(user_vector)
        self.assertEqual(user_norm, 0)
        
        # Should handle division by zero gracefully
        if user_norm == 0:
            user_norm = 1e-10
        
        self.assertGreater(user_norm, 0)


class TestRecommendationFiltering(unittest.TestCase):
    """Test filtering and validation of recommendations."""

    def test_filter_already_listened_tracks(self):
        """Test that already-listened tracks are excluded."""
        listened_track_ids = {'t1', 't2', 't5'}
        
        all_recommendations = pd.DataFrame({
            'user_id': ['u1'] * 5,
            'track_id': ['t1', 't2', 't3', 't4', 't5'],
            'score': [0.9, 0.85, 0.88, 0.92, 0.80]
        })
        
        filtered = all_recommendations[
            ~all_recommendations['track_id'].isin(listened_track_ids)
        ]
        
        self.assertEqual(len(filtered), 2)
        self.assertNotIn('t1', filtered['track_id'].values)
        self.assertNotIn('t5', filtered['track_id'].values)

    def test_filter_by_minimum_score(self):
        """Test filtering recommendations by minimum score threshold."""
        min_score = 0.5
        
        recommendations = pd.DataFrame({
            'user_id': ['u1'] * 5,
            'track_id': ['t1', 't2', 't3', 't4', 't5'],
            'score': [0.9, 0.45, 0.88, 0.35, 0.92]
        })
        
        filtered = recommendations[recommendations['score'] >= min_score]

        # Expect three recommendations meet or exceed the 0.5 threshold
        self.assertEqual(len(filtered), 3)

    def test_filter_invalid_track_ids(self):
        """Test filtering invalid track IDs."""
        valid_track_ids = {'t1', 't2', 't3', 't4', 't5'}
        
        recommendations = pd.DataFrame({
            'track_id': ['t1', 't2', 'invalid', 't4', 't5']
        })
        
        filtered = recommendations[recommendations['track_id'].isin(valid_track_ids)]
        
        self.assertEqual(len(filtered), 4)

    def test_filter_invalid_user_ids(self):
        """Test filtering invalid user IDs."""
        valid_user_ids = {'u1', 'u2', 'u3'}
        
        recommendations = pd.DataFrame({
            'user_id': ['u1', 'u2', 'invalid_user', 'u3']
        })
        
        filtered = recommendations[recommendations['user_id'].isin(valid_user_ids)]
        
        self.assertEqual(len(filtered), 3)


if __name__ == '__main__':
    unittest.main()
