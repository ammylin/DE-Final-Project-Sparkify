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
            track_name VARCHAR(500),
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
            track_name VARCHAR(255),
            track_genre VARCHAR(100),
            primary_artist VARCHAR(255),
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

    create_tables = create_postgres_tables()
    verify_tables = verify_postgres_tables()
    # debug_postgres_connection()

    # Set the workflow: table creation → table verification
    create_tables >> verify_tables
