import pandas as pd
import ast
import json
from recommendations import (
    build_track_matrix,
    recommend_for_user,
    recommend_for_all_users
)

# ---------------------------------------------------------
# 1. Load your synthetic data
# ---------------------------------------------------------
users_df = pd.read_csv("synthetic_users.csv")
tracks_df = pd.read_csv("data/cleaned_spotify_tracks.csv")
events_df = pd.read_csv("synthetic_events.csv")

# Convert genre_weights from string to dict
users_df['genre_weights'] = users_df['genre_weights'].apply(json.loads)

# Add default exploration weight if missing
if 'exploration_weight' not in users_df.columns:
    users_df['exploration_weight'] = 0.1  # default value

# ---------------------------------------------------------
# 2. Preprocess tracks
# ---------------------------------------------------------
# Convert stringified list of genres to Python list
tracks_df['track_genre'] = tracks_df['track_genre'].apply(ast.literal_eval)

# Create 'genre_single' column for recommendation model
tracks_df['genre_single'] = tracks_df['track_genre'].apply(lambda x: x[0] if len(x) > 0 else None)

# Drop tracks with no genre
tracks_df = tracks_df.dropna(subset=['genre_single']).reset_index(drop=True)

# ---------------------------------------------------------
# 3. Preprocess events
# ---------------------------------------------------------
# Make sure the event genre column exists
if 'track_genre' in events_df.columns:
    events_df['genre'] = events_df['track_genre']
else:
    raise ValueError("Events CSV is missing 'track_genre' column")

# ---------------------------------------------------------
# 4. Validate required columns
# ---------------------------------------------------------
required_track_cols = [
    "track_id", "track_name", "primary_artist",
    "genre_single", "danceability", "energy",
    "valence", "tempo", "loudness", "popularity"
]
missing = [c for c in required_track_cols if c not in tracks_df.columns]
if missing:
    raise ValueError(f"Tracks missing required columns: {missing}")

required_user_cols = ["user_id", "genre_weights", "exploration_weight"]
missing = [c for c in required_user_cols if c not in users_df.columns]
if missing:
    raise ValueError(f"Users missing required columns: {missing}")

required_event_cols = ["user_id", "track_id", "genre"]
missing = [c for c in required_event_cols if c not in events_df.columns]
if missing:
    raise ValueError(f"Events missing required columns: {missing}")

# ---------------------------------------------------------
# 5. Build track matrix (content vectors)
# ---------------------------------------------------------
X = build_track_matrix(tracks_df)

# ---------------------------------------------------------
# 6. Test recommendations for a single user
# ---------------------------------------------------------
test_user = users_df.iloc[0]
print("\nTop 10 recommendations for user:", test_user["user_id"])
recs = recommend_for_user(test_user, tracks_df, events_df, X, top_k=10)

# Pretty-print recommendations
for idx, row in recs.iterrows():
    print(f"{idx+1}. {row['track_name']} by {row['primary_artist']} [{row['genre_single']}] - Score: {row['final_score']:.3f}")

# ---------------------------------------------------------
# 7. Generate recommendations for all users
# ---------------------------------------------------------
print("\nGenerating recommendations for ALL users...")
all_recs = recommend_for_all_users(users_df, tracks_df, events_df)

# Pretty-print top 3 recommendations for first 5 users
for user_id, group in all_recs.groupby("user_id"):
    print(f"\nUser: {user_id}")
    for idx, row in group.head(3).iterrows():
        print(f"{idx+1}. {row['track_name']} by {row['primary_artist']} [{row['genre_single']}] - Score: {row['final_score']:.3f}")
    # Limit to first 5 users for readability
    if all_recs.index.get_loc(idx) > 15:
        break

print("\nTotal recommendations generated:", len(all_recs))
