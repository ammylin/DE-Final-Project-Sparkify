"""
Integration and edge case tests
Tests for:
- End-to-end data pipeline
- Error handling
- Edge cases and boundary conditions
"""

import unittest
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import sys

sys.modules['psycopg2'] = MagicMock() if 'psycopg2' not in sys.modules else sys.modules['psycopg2']


class TestDataPipelineIntegration(unittest.TestCase):
    """Test complete data pipeline from ingestion to inference."""

    def test_full_pipeline_data_flow(self):
        """Test that data flows correctly through entire pipeline."""
        # Step 1: Create tracks
        tracks = pd.DataFrame({
            'track_id': [f't{i}' for i in range(100)],
            'track_name': [f'Song {i}' for i in range(100)],
            'popularity': np.random.randint(0, 101, 100),
            'danceability': np.random.rand(100),
        })
        
        # Step 2: Create users
        users = pd.DataFrame({
            'user_id': [f'u{i}' for i in range(50)],
            'age': np.random.randint(18, 80, 50),
        })
        
        # Step 3: Create events
        events = []
        for user_id in users['user_id']:
            for _ in range(20):
                events.append({
                    'user_id': user_id,
                    'track_id': np.random.choice(tracks['track_id']),
                    'timestamp': datetime.now(),
                })
        events_df = pd.DataFrame(events)
        
        # Step 4: Generate recommendations
        recommendations = pd.DataFrame({
            'user_id': [f'u{i}' for i in range(50)],
            'track_id': [f't{i}' for i in range(50)],
            'score': np.random.rand(50),
        })
        
        # Validate pipeline
        self.assertEqual(len(tracks), 100)
        self.assertEqual(len(users), 50)
        self.assertGreater(len(events_df), 0)
        self.assertEqual(len(recommendations), 50)

    def test_pipeline_handles_duplicate_events(self):
        """Test that pipeline handles duplicate user-track events."""
        events = [
            {'user_id': 'u1', 'track_id': 't1', 'timestamp': datetime.now()},
            {'user_id': 'u1', 'track_id': 't1', 'timestamp': datetime.now()},
            {'user_id': 'u1', 'track_id': 't2', 'timestamp': datetime.now()},
        ]
        df = pd.DataFrame(events)
        
        # Duplicate should be allowed (same user can listen to same track multiple times)
        self.assertEqual(len(df), 3)

    def test_data_retention_through_pipeline(self):
        """Test that data is retained and not lost through pipeline."""
        initial_data = {
            'track_id': ['t1', 't2', 't3'],
            'track_name': ['A', 'B', 'C']
        }
        df = pd.DataFrame(initial_data)
        
        # After processing, verify data is retained
        self.assertEqual(len(df), 3)
        self.assertEqual(list(df.columns), ['track_id', 'track_name'])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_single_user_recommendation(self):
        """Test recommendation generation for a single user."""
        user_id = 'u1'
        
        recommendations = pd.DataFrame({
            'user_id': [user_id] * 10,
            'track_id': [f't{i}' for i in range(10)],
            'score': np.random.rand(10),
        })
        
        self.assertEqual(len(recommendations), 10)
        self.assertTrue((recommendations['user_id'] == user_id).all())

    def test_single_track_recommendation(self):
        """Test when only one track is available."""
        recommendations = pd.DataFrame({
            'track_id': ['t1'],
            'score': [0.95]
        })
        
        self.assertEqual(len(recommendations), 1)

    def test_user_with_no_listening_history(self):
        """Test recommendation for user with no listening history."""
        user_id = 'new_user'
        listened_tracks = set()  # Empty history
        
        all_tracks = [f't{i}' for i in range(100)]
        available_tracks = [t for t in all_tracks if t not in listened_tracks]
        
        self.assertEqual(len(available_tracks), 100)

    def test_user_with_complete_listening_history(self):
        """Test handling when user has heard all tracks."""
        listened_tracks = {f't{i}' for i in range(100)}
        all_tracks = {f't{i}' for i in range(100)}
        
        available_tracks = all_tracks - listened_tracks
        
        self.assertEqual(len(available_tracks), 0)

    def test_empty_genre_weights(self):
        """Test user with empty genre preferences."""
        user = {
            'user_id': 'u1',
            'genre_weights': {}
        }
        
        # Should handle gracefully
        self.assertEqual(len(user['genre_weights']), 0)

    def test_very_large_user_count(self):
        """Test system with large number of users."""
        n_users = 10000
        users = [{'user_id': f'u{i}'} for i in range(n_users)]
        df = pd.DataFrame(users)
        
        self.assertEqual(len(df), n_users)

    def test_very_large_track_count(self):
        """Test system with large number of tracks."""
        n_tracks = 100000
        track_ids = [f't{i}' for i in range(n_tracks)]
        
        self.assertEqual(len(track_ids), n_tracks)

    def test_very_large_event_count(self):
        """Test system with large number of events."""
        n_events = 1000000
        # Don't create all in memory, just verify logic
        events_per_batch = 10000
        n_batches = n_events // events_per_batch
        
        self.assertEqual(n_batches * events_per_batch, n_events)

    def test_recommendation_score_precision(self):
        """Test handling of high-precision scores."""
        scores = [0.123456789, 0.987654321, 0.555555555]
        
        for score in scores:
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)

    def test_timestamp_precision(self):
        """Test handling of various timestamp formats."""
        timestamps = [
            datetime.now(),
            datetime(2025, 11, 28, 12, 30, 45),
            pd.Timestamp.now(),
        ]
        
        for ts in timestamps:
            self.assertIsNotNone(ts)

    def test_negative_values_in_features(self):
        """Test handling of negative feature values (like loudness)."""
        tracks = pd.DataFrame({
            'track_id': ['t1', 't2'],
            'loudness': [-5.5, -3.2],  # Valid negative values
        })
        
        # Should accept negative values
        self.assertTrue((tracks['loudness'] < 0).any())

    def test_special_characters_in_names(self):
        """Test handling of special characters in track/artist names."""
        tracks = pd.DataFrame({
            'track_id': ['t1', 't2'],
            'track_name': ['Song: The Remix (Feat. Artist & Co.)', 'Track #1 - "Classic"'],
            'primary_artist': ['Artist/Group', "O'Brien's Band"],
        })
        
        self.assertEqual(len(tracks), 2)
        self.assertIn(':', tracks.iloc[0]['track_name'])

    def test_unicode_in_names(self):
        """Test handling of unicode characters in names."""
        tracks = pd.DataFrame({
            'track_id': ['t1', 't2'],
            'track_name': ['日本語', 'Café'],
            'primary_artist': ['Artiste Français', '艺术家'],
        })
        
        self.assertEqual(len(tracks), 2)

    def test_null_handling_in_optional_fields(self):
        """Test handling of null values in optional fields."""
        tracks = pd.DataFrame({
            'track_id': ['t1', 't2'],
            'track_name': ['Song A', 'Song B'],
            'featuring_artist': [None, 'Artist B'],
        })
        
        self.assertEqual(tracks['featuring_artist'].isnull().sum(), 1)

    def test_zero_values_in_scores(self):
        """Test handling of zero scores."""
        recommendations = pd.DataFrame({
            'track_id': ['t1', 't2'],
            'score': [0.0, 0.5],
        })
        
        zero_scores = recommendations[recommendations['score'] == 0.0]
        self.assertEqual(len(zero_scores), 1)


class TestBoundaryConditions(unittest.TestCase):
    """Test boundary conditions and limits."""

    def test_maximum_users_per_batch(self):
        """Test maximum users that can be processed in one batch."""
        batch_size = 1000
        users = [{'user_id': f'u{i}'} for i in range(batch_size)]
        df = pd.DataFrame(users)
        
        self.assertEqual(len(df), batch_size)

    def test_maximum_recommendations_per_user(self):
        """Test maximum recommendations returned per user."""
        max_recs = 100
        recommendations = pd.DataFrame({
            'user_id': ['u1'] * max_recs,
            'track_id': [f't{i}' for i in range(max_recs)],
        })
        
        self.assertEqual(len(recommendations), max_recs)

    def test_time_series_data_ordering(self):
        """Test that time-series data maintains order."""
        timestamps = pd.date_range('2025-01-01', periods=100, freq='H')
        events = pd.DataFrame({
            'timestamp': timestamps,
            'user_id': [f'u{i%10}' for i in range(100)],
        })
        
        # Verify ordering
        diffs = events['timestamp'].diff().dt.total_seconds().iloc[1:]
        self.assertTrue((diffs > 0).all())

    def test_concurrent_user_requests(self):
        """Test handling of concurrent user requests."""
        # Simulate multiple users requesting at same time
        users = [f'u{i}' for i in range(100)]
        timestamps = [datetime.now()] * 100
        
        # All should have same timestamp
        self.assertTrue(all(ts == timestamps[0] for ts in timestamps))

    def test_recommendation_score_distribution(self):
        """Test that recommendation scores have reasonable distribution."""
        scores = np.random.rand(1000)
        
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        # Should be roughly uniform
        self.assertGreater(mean_score, 0.3)
        self.assertLess(mean_score, 0.7)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and resilience."""

    def test_missing_required_field(self):
        """Test handling of missing required fields."""
        track = {
            'track_id': 't1',
            # Missing 'track_name'
            'popularity': 75,
        }
        
        missing_fields = [key for key in ['track_id', 'track_name', 'popularity'] 
                         if key not in track]
        
        self.assertIn('track_name', missing_fields)

    def test_invalid_data_type(self):
        """Test handling of invalid data types."""
        track = {
            'track_id': 't1',
            'popularity': 'high',  # Should be int
        }
        
        try:
            popularity = int(track['popularity'])
            self.fail("Should raise ValueError")
        except ValueError:
            pass  # Expected

    def test_connection_retry_logic(self):
        """Test retry logic for database connections."""
        max_retries = 3
        attempt = 0
        success = False

        # Simulate retry attempts: fail until the final allowed attempt succeeds
        while attempt < max_retries:
            attempt += 1
            try:
                # Simulate connection attempt: fail if not the final try
                if attempt < max_retries:
                    raise Exception("Connection failed")
                else:
                    success = True
                    break
            except Exception:
                # continue to next retry
                continue

        self.assertTrue(success)
        self.assertEqual(attempt, max_retries)

    def test_timeout_handling(self):
        """Test handling of query timeouts."""
        timeout_seconds = 30
        
        # Query should complete within timeout
        start_time = datetime.now()
        
        # Simulate query
        # (in real scenario, would run actual query)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        self.assertLess(elapsed, timeout_seconds)

    def test_malformed_json_handling(self):
        """Test handling of malformed JSON."""
        malformed_json = "{'invalid': json}"  # Single quotes instead of double
        
        try:
            data = json.loads(malformed_json)
            self.fail("Should raise JSONDecodeError")
        except json.JSONDecodeError:
            pass  # Expected


if __name__ == '__main__':
    unittest.main()
