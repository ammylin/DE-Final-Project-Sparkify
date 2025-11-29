from __future__ import annotations
import pandas as pd
import numpy as np
import uuid
import pickle
import psycopg2
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.decorators import task
from dotenv import load_dotenv

load_dotenv()

pickle_path = os.getenv(
    "MODEL_PICKLE_PATH", "/opt/airflow/data/recommendation_model.pkl"
)


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
    dag_id="inference",
    start_date=datetime(2025, 11, 25),
    schedule="*/2 * * * *",
    catchup=False,
    default_args=default_args,
    description="Complete music data pipeline - Synthetic users and listening events",
    tags=["music", "synthetic-data"],
) as dag:

    @task()
    def create_recommendations_table():
        """
        Task #1: Create the empty table for storing recommendations.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS music_analytics.recommendations (
            recommendation_id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(50),
            track_id VARCHAR(22),
            track_name TEXT,
            primary_artist TEXT,
            score FLOAT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES music_analytics.users(user_id)
        );
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(create_table_sql)
            conn.commit()
            cur.close()
            conn.close()
            print("Recommendations table created successfully")
        except Exception as e:
            print(f"Error creating table: {e}")
            raise

    @task()
    def fetch_random_user_and_history():
        """
        Task #2: Pick a random user ID and get their listening history to avoid repeat recommendations.
        """
        conn = get_connection()
        cur = conn.cursor()

        # 1. Pick a random user ID
        cur.execute(
            "SELECT user_id FROM music_analytics.users ORDER BY RANDOM() LIMIT 1;"
        )
        user_id = cur.fetchone()[0]

        # 2. Fetch history to exclude already listened tracks
        cur.execute(
            "SELECT track_id FROM music_analytics.listening_events WHERE user_id = %s;",
            (user_id,),
        )
        # Convert list of tuples to a set for O(1) lookup speed
        listened_track_ids = {row[0] for row in cur.fetchall()}

        cur.close()
        conn.close()

        print(f"Selected User: {user_id} (History: {len(listened_track_ids)} tracks)")

        # Return context dictionary
        return {"user_id": user_id, "listened_track_ids": list(listened_track_ids)}

    @task()
    def generate_recommendations(user_context: dict, top_k: int = 10):
        """
        Task #3: Load the model artifact and compute Cosine Similarity between the specific user vector and ALL track vectors.
        """
        # 1. Load Model Locally
        if not os.path.exists(pickle_path):
            raise FileNotFoundError(f"Pickle not found at {pickle_path}")

        print(f"Loading model artifact from {pickle_path}...")
        with open(pickle_path, "rb") as f:
            model_data = pickle.load(f)
        print("Model loaded successfully.")

        # 2. Unpack Data
        user_id = user_context["user_id"]
        listened_set = set(user_context["listened_track_ids"])

        user_map = model_data["user_map"]  # Dict: User ID -> Vector
        track_matrix = model_data["track_matrix"]  # Matrix: All Track Vectors (N x 64)
        track_meta = model_data[
            "track_meta"
        ]  # List: Metadata corresponding to matrix rows

        # 3. Validation
        if user_id not in user_map:
            raise ValueError(f"User ID {user_id} not found in model artifact.")

        user_vector = user_map[user_id]  # Shape: (64,)

        # 4. Vector Math: Cosine Similarity

        # Calculate norms (magnitudes)
        user_norm = np.linalg.norm(user_vector)
        # Calculate norm for every row in the matrix (axis=1)
        track_norms = np.linalg.norm(track_matrix, axis=1)

        # Avoid division by zero
        track_norms[track_norms == 0] = 1e-10
        if user_norm == 0:
            user_norm = 1e-10

        # Dot product of (1, 64) against (N, 64) -> Result is array of shape (N,)
        dot_products = track_matrix.dot(user_vector)

        # Final scores
        similarity_scores = dot_products / (user_norm * track_norms)
        print("Dot products:")
        print(dot_products)
        print("Similarity scores:")
        print(similarity_scores)

        # 5. Ranking and Filtering
        # Create a list of (index, score) tuples: [(0, 0.98), (1, 0.45), ...]
        scores_with_indices = list(enumerate(similarity_scores))

        # Sort by score descending (highest similarity first)
        scores_with_indices.sort(key=lambda x: x[1], reverse=True)
        print("Top scores with indices:")
        print(scores_with_indices)

        recommendations = []
        for idx, score in scores_with_indices:
            # Look up metadata using the row index
            meta = track_meta[idx]
            t_id = meta["track_id"]

            # Skip if user already listened to this track
            if t_id in listened_set:
                continue

            recommendations.append(
                {
                    "track_id": t_id,
                    "track_name": meta["track_name"],
                    "primary_artist": meta["primary_artist"],
                    "score": float(
                        score
                    ),  # Convert numpy float to python float for JSON serialization
                }
            )

            # Stop once we have top_k
            if len(recommendations) >= top_k:
                break

        print(f"Generated {len(recommendations)} recommendations for {user_id}")
        return {"user_id": user_id, "recs": recommendations}

    @task()
    def save_recommendations(rec_data: dict):
        """
        Task #4: Insert the top k recommendations into Postgres.
        """
        user_id = rec_data["user_id"]
        recs = rec_data["recs"]

        conn = get_connection()
        cur = conn.cursor()

        for r in recs:
            try:
                cur.execute(
                    """
                    INSERT INTO music_analytics.recommendations 
                    (recommendation_id, user_id, track_id, track_name, primary_artist, score)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (
                        str(uuid.uuid4()),
                        user_id,
                        r["track_id"],
                        r["track_name"],
                        r["primary_artist"],
                        r["score"],
                    ),
                )
            except Exception as e:
                print(f"Error inserting recommendation: {e}")

        conn.commit()
        cur.close()
        conn.close()
        print(f"Successfully saved {len(recs)} recommendations for user {user_id}")

    # Define the task pipeline
    setup = create_recommendations_table()
    user_data = fetch_random_user_and_history()

    # Generate recommendations depends on both user data and the model file
    recs = generate_recommendations(user_context=user_data)

    # Save results depends on generation
    save = save_recommendations(recs)

    # Define dependency structure
    setup >> user_data >> recs >> save
