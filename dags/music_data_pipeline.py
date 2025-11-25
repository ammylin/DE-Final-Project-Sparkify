from __future__ import annotations
import pandas as pd
import numpy as np
import uuid
import json
import ast
from datetime import datetime, timedelta
from airflow import DAG
from airflow.decorators import task

DATA_DIR = "/opt/airflow/data"
SONGS_CSV = f"{DATA_DIR}/cleaned_spotify_tracks.csv"

default_args = {
    "owner": "Sparkify",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="music_data_pipeline",
    start_date=datetime(2025, 11, 25),
    schedule_interval="@daily",
    catchup=False,
    default_args=default_args,
    description="Music data pipeline",
    tags=["music", "synthetic-data"],
) as dag:

    @task()
    def check_songs_data():
        """Task 1: Verify that song data exists"""
        try:
            # ✅ Using the correct variable
            songs_df = pd.read_csv(SONGS_CSV, nrows=5)
            required_columns = ["track_id", "track_name", "track_genre", "artists"]

            missing_columns = [
                col for col in required_columns if col not in songs_df.columns
            ]
            if missing_columns:
                raise ValueError(f"Missing columns: {missing_columns}")

            print(f"✅ Song data verified. Columns: {list(songs_df.columns)}")
            return f"Data OK - {len(songs_df.columns)} columns found"

        except FileNotFoundError:
            raise FileNotFoundError(f"❌ File not found: {SONGS_CSV}")
        except Exception as e:
            raise Exception(f"❌ Error checking data: {e}")

    @task()
    def generate_sample_users():
        """Task 2: Generate sample users (simple version)"""
        sample_users = [
            {
                "user_id": "user_001",
                "age": 25,
                "country": "USA",
                "favorite_genre": "pop",
            },
            {
                "user_id": "user_002",
                "age": 30,
                "country": "Mexico",
                "favorite_genre": "rock",
            },
            {
                "user_id": "user_003",
                "age": 22,
                "country": "Brazil",
                "favorite_genre": "samba",
            },
        ]

        users_df = pd.DataFrame(sample_users)
        # ✅ Using the correct variable
        output_path = f"{DATA_DIR}/sample_users.csv"
        users_df.to_csv(output_path, index=False)

        print(f"✅ Sample users generated: {len(users_df)} users")
        print(f"📁 Saved to: {output_path}")

        return f"Generated {len(users_df)} sample users"

    # Dependencies
    data_check = check_songs_data()
    users_task = generate_sample_users()
    data_check >> users_task
