from __future__ import annotations
import pandas as pd
import numpy as np
import uuid
import json
import ast
import subprocess
import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.decorators import task
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Configuration
DATA_DIR = "/opt/airflow/data"
SONGS_CSV = f"{DATA_DIR}/cleaned_spotify_tracks.csv"
USERS_CSV = f"{DATA_DIR}/synthetic_users.csv"
EVENTS_CSV = f"{DATA_DIR}/synthetic_events.csv"


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


default_args = {
    "owner": "Sparkify",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="music_data_pipeline",
    start_date=datetime(2025, 11, 25),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    description="Complete music data pipeline - Synthetic users and listening events",
    tags=["music", "synthetic-data"],
) as dag:

    @task()
    def create_postgres_tables():
        """Task 1: Create empty tables in PostgreSQL for music data for tracks, songs and events"""

        create_tables_sql = """
        CREATE SCHEMA IF NOT EXISTS music_analytics;

        -- Original music tracks table
        CREATE TABLE IF NOT EXISTS music_analytics.tracks (
            track_id VARCHAR(22) PRIMARY KEY,
            artists JSONB,                    -- Lists like jsons
            track_name TEXT,
            track_genre JSONB,                -- Lists like jsons
            explicit INTEGER,
            popularity INTEGER,
            danceability FLOAT,
            energy FLOAT,
            key INTEGER,
            loudness FLOAT,
            mode INTEGER,
            speechiness FLOAT,
            acousticness FLOAT,
            instrumentalness FLOAT,
            liveness FLOAT,
            valence FLOAT,
            tempo FLOAT,
            duration_ms INTEGER,
            time_signature INTEGER,
            primary_artist VARCHAR(255),
            duration_sec FLOAT,
            duration_min FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Users table
        CREATE TABLE IF NOT EXISTS music_analytics.users (
            user_id VARCHAR(50) PRIMARY KEY,
            age INTEGER,
            country VARCHAR(50),
            favorite_genres JSONB,
            genre_weights JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Listening events table
        CREATE TABLE IF NOT EXISTS music_analytics.listening_events (
            event_id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50),
            timestamp TIMESTAMP,
            track_id VARCHAR(50),
            track_name TEXT,
            track_genre VARCHAR(100),
            primary_artist TEXT,
            danceability FLOAT,
            energy FLOAT,
            valence FLOAT,
            loudness FLOAT,
            tempo FLOAT,
            popularity INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES music_analytics.users(user_id)
        );
        """

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(create_tables_sql)
            conn.commit()
            cur.close()
            conn.close()
            print("Tables created successfully")
            return "OK"
        except Exception as e:
            print(f"Error creating tables: {e}")
            raise

    @task()
    def verify_postgres_tables():
        """Task 2: Verify that required PostgreSQL tables exist in the music_analytics schema"""

        required_tables = [
            "tracks",
            "users",
            "listening_events",
        ]

        schema = "music_analytics"

        verify_sql = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{schema}';
        """

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(verify_sql)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            existing = {row[0] for row in rows}
            missing = [t for t in required_tables if t not in existing]

            if missing:
                raise ValueError(f"Missing tables: {missing}")

            print("All required tables exist")
            return "OK"

        except Exception as e:
            print(f"Error verifying tables: {e}")
            raise

    # I need to verify that Postgres connection works
    @task()
    def debug_postgres_connection():
        """Task: Check that DB connection works and print version"""
        try:
            print("DB_NAME =", os.getenv("DB_NAME"))
            print("DB_USER =", os.getenv("DB_USER"))
            print("DB_HOST =", os.getenv("DB_HOST"))
            print("DB_PORT =", os.getenv("DB_PORT"))

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print("PostgreSQL version:", version[0])
            cur.close()
            conn.close()
            return "Connection OK"
        except Exception as e:
            print("Connection failed:", e)
            raise

    @task
    def generate_tracks_table():
        """Task 3: Load CSV data into music_analytics.tracks table"""
        CSV_PATH = "/opt/airflow/data/cleaned_spotify_tracks.csv"

        # Read CSV
        df = pd.read_csv(CSV_PATH)

        # Connect to Postgres
        conn = get_connection()
        cur = conn.cursor()

        for _, row in df.iterrows():
            try:
                cur.execute(
                    """
                    INSERT INTO music_analytics.tracks (
                        track_id, artists, track_name, track_genre, explicit,
                        popularity, danceability, energy, key, loudness,
                        mode, speechiness, acousticness, instrumentalness, liveness,
                        valence, tempo, duration_ms, time_signature, primary_artist,
                        duration_sec, duration_min
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (track_id) DO NOTHING;
                """,
                    (
                        row["track_id"],
                        json.dumps(row["artists"]),
                        row["track_name"],
                        json.dumps(row["track_genre"]),
                        row["explicit"],
                        row["popularity"],
                        row["danceability"],
                        row["energy"],
                        row["key"],
                        row["loudness"],
                        row["mode"],
                        row["speechiness"],
                        row["acousticness"],
                        row["instrumentalness"],
                        row["liveness"],
                        row["valence"],
                        row["tempo"],
                        row["duration_ms"],
                        row["time_signature"],
                        row["primary_artist"],
                        row["duration_sec"],
                        row["duration_min"],
                    ),
                )
            except Exception as e:
                print(f"Error inserting row {row['track_id']}: {e}")
                continue

        conn.commit()
        cur.close()
        conn.close()
        print("Tracks table populated successfully")
        return "OK"

    @task
    def generate_users(n_users: int = 2000):
        """Task 4: Generate users and load them into music_analytics.users table"""
        np.random.seed(42)

        conn = get_connection()
        tracks_df = pd.read_sql(
            "SELECT track_id, track_genre FROM music_analytics.tracks;", conn
        )
        conn.close()

        tracks_df["track_genre_list"] = tracks_df["track_genre"].apply(ast.literal_eval)
        all_genres = sorted(
            list({g for sublist in tracks_df["track_genre_list"] for g in sublist})
        )

        countries = [
            "USA",
            "Canada",
            "UK",
            "Germany",
            "France",
            "Mexico",
            "Brazil",
            "India",
            "Japan",
            "Australia",
        ]

        users = []
        for _ in range(n_users):
            user_id = str(uuid.uuid4())
            age = np.random.randint(16, 65)
            country = np.random.choice(countries)

            # Step 1: Choose 1–3 favorite genres
            num_favs = np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
            favorite_genres = list(
                np.random.choice(all_genres, size=num_favs, replace=False)
            )

            # Step 2–4: Assign weights (favorite genres high, others low)
            weights = {}
            for i, g in enumerate(favorite_genres):
                if i == 0:
                    weights[g] = np.random.uniform(0.40, 0.60)
                elif i == 1:
                    weights[g] = np.random.uniform(0.20, 0.30)
                elif i == 2:
                    weights[g] = np.random.uniform(0.10, 0.20)

            # Add small "exploration" genre weights
            num_extras = np.random.randint(2, 5)
            extra_genres = np.random.choice(
                [g for g in all_genres if g not in favorite_genres],
                size=num_extras,
                replace=False,
            )
            for g in extra_genres:
                weights[g] = np.random.uniform(0.01, 0.05)

            # Normalize weights
            total = sum(weights.values())
            weights = {g: round(w / total, 4) for g, w in weights.items()}

            users.append(
                {
                    "user_id": user_id,
                    "age": age,
                    "country": country,
                    "favorite_genres": json.dumps(favorite_genres),
                    "genre_weights": json.dumps(weights),
                }
            )

        # Insert into users table
        conn = get_connection()
        cur = conn.cursor()
        for u in users:
            try:
                cur.execute(
                    """
                    INSERT INTO music_analytics.users (user_id, age, country, favorite_genres, genre_weights)
                    VALUES (%s,%s,%s,%s,%s)
                    ON CONFLICT (user_id) DO NOTHING;
                """,
                    (
                        u["user_id"],
                        u["age"],
                        u["country"],
                        u["favorite_genres"],
                        u["genre_weights"],
                    ),
                )
            except Exception as e:
                print(f"Error inserting user {u['user_id']}: {e}")
                continue

        conn.commit()
        cur.close()
        conn.close()
        print(f"Generated {n_users} users → music_analytics.users table")

    @task
    def generate_listening_events(
        events_per_user: int = 50, use_popularity_weights: bool = True
    ):
        """Task 5: Generate users and load them into music_analytics.listening_events table"""
        np.random.seed(42)

        conn = get_connection()
        tracks_df = pd.read_sql("SELECT * FROM music_analytics.tracks;", conn)

        users_df = pd.read_sql("SELECT * FROM music_analytics.users;", conn)
        conn.close()

        tracks_df["track_genre_list"] = tracks_df["track_genre"].apply(ast.literal_eval)

        # Extract primary artist if not already
        if "primary_artist" not in tracks_df.columns:
            tracks_df["primary_artist"] = tracks_df["artists"].apply(
                lambda x: (
                    ast.literal_eval(x)[0] if len(ast.literal_eval(x)) > 0 else None
                )
            )

        # Pre-group songs by genre
        songs_by_genre = {}
        for genre in set(
            g for sublist in tracks_df["track_genre_list"] for g in sublist
        ):
            songs_by_genre[genre] = tracks_df[
                tracks_df["track_genre_list"].apply(lambda x: genre in x)
            ]

        all_events = []

        # Country-specific genre bias
        country_bias_map = {
            "Brazil": ["forro", "samba", "bossa nova"],
            "USA": ["hip-hop", "rock", "country"],
            "Japan": ["j-dance", "j-pop"],
            "UK": ["rock", "pop", "indie"],
            "Germany": ["techno", "electronic", "minimal-techno"],
            "France": ["chanson", "electronic", "pop"],
            "Canada": ["rock", "pop", "hip-hop"],
            "Mexico": ["reggaeton", "ranchera", "pop"],
            "India": ["bollywood", "indian-pop", "classical"],
            "Australia": ["rock", "electronic", "pop"],
        }

        for _, user_row in users_df.iterrows():
            user_id = user_row["user_id"]
            user_age = user_row["age"]
            user_country = user_row["country"]
            # weights = json.loads(user_row["genre_weights"])
            weights = user_row["genre_weights"]
            if isinstance(weights, str):  # If it's a string, parse it as JSON
                weights = json.loads(weights)
            elif isinstance(
                weights, dict
            ):  # If it's already a dictionary, no need to parse
                pass
            else:
                print(
                    f"Error: Unexpected type for genre_weights: {type(weights)} for user_id {user_id}"
                )
                continue

            genres = list(weights.keys())
            probs = list(weights.values())

            start_date = datetime(2024, 1, 1)

            for _ in range(events_per_user):
                # Age bias
                age_bias = {
                    g: (
                        1.2
                        if (user_age < 25 and g in ["pop", "electronic", "hip-hop"])
                        or (user_age > 50 and g in ["classical", "jazz", "blues"])
                        else 1.0
                    )
                    for g in genres
                }

                # Country bias
                country_bias = {
                    g: 1.2 if g in country_bias_map.get(user_country, []) else 1.0
                    for g in genres
                }

                # Combine weights
                adjusted_probs = np.array(
                    [p * age_bias[g] * country_bias[g] for g, p in zip(genres, probs)]
                )
                adjusted_probs /= adjusted_probs.sum()

                # Pick genre
                chosen_genre = np.random.choice(genres, p=adjusted_probs)

                # Pick track from that genre
                genre_tracks = songs_by_genre.get(chosen_genre)
                if genre_tracks is None or len(genre_tracks) == 0:
                    continue

                track = genre_tracks.sample(
                    n=1,
                    weights=(
                        genre_tracks["popularity"] if use_popularity_weights else None
                    ),
                ).iloc[0]

                # Timestamp
                timestamp = start_date + timedelta(
                    days=np.random.randint(0, 120), minutes=np.random.randint(0, 1440)
                )

                all_events.append(
                    {
                        "event_id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "timestamp": timestamp,
                        "track_id": track["track_id"],
                        "track_name": track["track_name"],
                        "track_genre": chosen_genre,
                        "primary_artist": track["primary_artist"],
                        "danceability": float(track["danceability"]),
                        "energy": float(track["energy"]),
                        "valence": float(track["valence"]),
                        "loudness": float(track["loudness"]),
                        "tempo": float(track["tempo"]),
                        "popularity": float(track["popularity"]),
                    }
                )

        # Insert into listening_events table
        conn = get_connection()
        cur = conn.cursor()
        for event in all_events:
            try:
                cur.execute(
                    """
                    INSERT INTO music_analytics.listening_events (event_id, user_id, timestamp, track_id, track_name, track_genre, primary_artist, danceability, energy, valence, loudness, tempo, popularity)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (event_id) DO NOTHING;
                """,
                    (
                        event["event_id"],
                        event["user_id"],
                        event["timestamp"],
                        event["track_id"],
                        event["track_name"],
                        event["track_genre"],
                        event["primary_artist"],
                        event["danceability"],
                        event["energy"],
                        event["valence"],
                        event["loudness"],
                        event["tempo"],
                        event["popularity"],
                    ),
                )
            except Exception as e:
                print(f"Error inserting user {event['event_id']}: {e}")
                continue

        conn.commit()
        cur.close()
        conn.close()
        print(
            f"Generated {len(all_events)} listening events → music_analytics.listening_events table"
        )

    @task
    def train_recommendation_model():
        """Task 6: Train recommendation model using listening events data and save it as a pickle file"""

    create_tables = create_postgres_tables()
    verify_tables = verify_postgres_tables()
    create_tracks_table = generate_tracks_table()
    create_users_table = generate_users(n_users=2000)
    create_events_table = generate_listening_events(
        events_per_user=20, use_popularity_weights=True
    )
    # train_model = train_recommendation_model()
    # debug_postgres_connection()

    # Set the workflow
    (
        create_tables
        >> verify_tables
        >> create_tracks_table
        >> create_users_table
        >> create_events_table
        # >> train_model
    )
