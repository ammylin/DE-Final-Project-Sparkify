import psycopg2
import numpy as np
import pandas as pd
import json
import os
from dotenv import load_dotenv

# Try to load .env, but don't crash if it fails
load_dotenv()

# --- CONFIGURATION (With Defaults) ---
# We verify what we are loading to help debugging
db_name = os.getenv("DB_NAME", "musicdb")
db_user = os.getenv("DB_USER", "vscode")
db_pass = os.getenv("DB_PASSWORD", "vscode") # Default to 'vscode'
db_host = "localhost" # Force localhost for local debugging
db_port = os.getenv("DB_PORT", "5432")

print(f"🔌 Connecting to: {db_name} as {db_user} on {db_host}:{db_port}")

# --- 1. CONNECT ---
try:
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_pass,
        host=db_host,
        port=db_port
    )
    print("✅ Connected to Database")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
    print("TIP: Make sure your Docker containers are running (docker ps).")
    exit()

# --- 2. INSPECT A USER VECTOR ---
print("\n--- INSPECTING USER ---")
# Grab a user who actually has genre weights
user_query = """
SELECT user_id, genre_weights, user_embedding 
FROM music_analytics.users 
WHERE user_embedding IS NOT NULL 
LIMIT 1;
"""
try:
    user_row = pd.read_sql(user_query, conn).iloc[0]
    user_id = user_row['user_id']
    raw_user_vec_str = user_row['user_embedding']

    print(f"User ID: {user_id}")
    print(f"Genre Weights: {user_row['genre_weights']}")
    print(f"Raw DB String (First 50 chars): {str(raw_user_vec_str)[:50]}...")

    # PARSE CHECK
    # Mimic your DAG's parsing logic exactly
    clean_str = str(raw_user_vec_str).replace('[', '').replace(']', '').replace('(', '').replace(')', '')
    user_vector = np.fromstring(clean_str, sep=',')
    
    print(f"Parsed Vector Shape: {user_vector.shape}")
    print(f"First 5 values: {user_vector[:5]}")
    
    magnitude = np.linalg.norm(user_vector)
    print(f"User Vector Magnitude: {magnitude}")
    
    if magnitude == 0:
        print("🚨 FAILURE: User Vector is ALL ZEROS. Genre matching failed in DAG #1.")
    else:
        print("✅ User Vector looks healthy.")

except IndexError:
    print("🚨 FAILURE: No users with embeddings found in the table.")
    conn.close()
    exit()
except Exception as e:
    print(f"🚨 FAILURE: Could not parse user vector. Error: {e}")
    conn.close()
    exit()

# --- 3. INSPECT A TRACK VECTOR ---
print("\n--- INSPECTING TRACK ---")
track_query = """
SELECT track_name, track_embedding 
FROM music_analytics.tracks 
WHERE track_embedding IS NOT NULL 
LIMIT 1;
"""
try:
    track_row = pd.read_sql(track_query, conn).iloc[0]
    raw_track_vec_str = track_row['track_embedding']

    clean_track_str = str(raw_track_vec_str).replace('[', '').replace(']', '').replace('(', '').replace(')', '')
    track_vector = np.fromstring(clean_track_str, sep=',')
    
    print(f"Track: {track_row['track_name']}")
    print(f"Track Vector Magnitude: {np.linalg.norm(track_vector)}")
    
    if np.linalg.norm(track_vector) == 0:
        print("🚨 FAILURE: Track Vector is ALL ZEROS. PCA failed.")
    else:
        print("✅ Track Vector looks healthy.")

except Exception as e:
    print(f"🚨 FAILURE: Could not parse track vector. Error: {e}")

# --- 4. MANUAL MATH CHECK ---
if 'user_vector' in locals() and 'track_vector' in locals():
    print("\n--- MANUAL MATH CHECK ---")
    dot_product = np.dot(user_vector, track_vector)
    print(f"Dot Product: {dot_product}")
    
    denom = (np.linalg.norm(user_vector) * np.linalg.norm(track_vector))
    print(f"Denominator: {denom}")
    
    if denom == 0:
        print("Similarity: 0.0 (Division by Zero)")
    else:
        print(f"Calculated Similarity: {dot_product / denom}")

conn.close()