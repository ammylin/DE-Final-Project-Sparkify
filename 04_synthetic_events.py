# 04_synthetic_events.py
"""
Generate synthetic listening events for users based on their music preferences.
Each event includes:
- A unique event ID
- User ID
- Timestamp of the listening event
- Track ID and metadata (name, genre, album, artists)
- Audio features (danceability, energy, valence)
- Popularity score
- Generates a CSV file of synthetic listening events.
Events are generated to reflect user preferences, optionally weighted by track popularity,
and now biased by user age and country for realism.
"""

import numpy as np
import pandas as pd
import uuid
import argparse
import json
from datetime import datetime, timedelta
import ast

def generate_listening_events(
    users_csv: str,
    songs_csv: str,
    output_path: str,
    events_per_user: int = 50,
    seed: int = 42,
    use_popularity_weights: bool = True
):
    np.random.seed(seed)

    # Load users
    users = pd.read_csv(users_csv)

    # Load songs and parse list-like columns
    songs = pd.read_csv(songs_csv)

    # Parse genres and artists stored as strings
    songs['track_genre_list'] = songs['track_genre'].apply(ast.literal_eval)
    songs['artists_list'] = songs['artists'].apply(ast.literal_eval)
    songs['primary_artist'] = songs['artists_list'].apply(lambda x: x[0] if len(x) > 0 else None)

    # Pre-group songs by genre for faster sampling
    songs_by_genre = {}
    for genre in set(g for sublist in songs['track_genre_list'] for g in sublist):
        songs_by_genre[genre] = songs[songs['track_genre_list'].apply(lambda x: genre in x)]

    all_events = []

    # Country-specific genre mapping
    country_bias_map = {
        "Brazil": ['forro', 'samba', 'bossa nova'],
        "USA": ['hip-hop', 'rock', 'country'],
        "Japan": ['j-dance', 'j-pop'],
        "UK": ['rock', 'pop', 'indie'],
        "Germany": ['techno', 'electronic', 'krautrock'],
        "France": ['chanson', 'electronic', 'pop'],
        "Canada": ['rock', 'pop', 'hip-hop'],
        "Mexico": ['reggaeton', 'ranchera', 'pop'],
        "India": ['bollywood', 'indian-pop', 'classical'],
        "Australia": ['rock', 'electronic', 'pop']
    }

    for _, user_row in users.iterrows():
        user_id = user_row['user_id']
        user_age = user_row['age']
        user_country = user_row['country']
        weights = json.loads(user_row['genre_weights'])
        genres = list(weights.keys())
        probs = list(weights.values())

        start_date = datetime(2024, 1, 1)

        for _ in range(events_per_user):
            # ----------------------------
            # Apply age and country biases
            # ----------------------------
            age_bias = {}
            for g in genres:
                if user_age < 25 and g in ['pop', 'electronic', 'hip-hop']:
                    age_bias[g] = 1.2
                elif user_age > 50 and g in ['classical', 'jazz', 'blues']:
                    age_bias[g] = 1.2
                else:
                    age_bias[g] = 1.0

            country_bias = {}
            for g in genres:
                if g in country_bias_map.get(user_country, []):
                    country_bias[g] = 1.2
                else:
                    country_bias[g] = 1.0

            # Combine original weights with biases
            adjusted_probs = []
            for g, p in zip(genres, probs):
                adjusted_probs.append(p * age_bias[g] * country_bias[g])
            adjusted_probs = np.array(adjusted_probs)
            adjusted_probs /= adjusted_probs.sum()  # normalize

            # Choose genre based on adjusted probabilities
            chosen_genre = np.random.choice(genres, p=adjusted_probs)

            # Pick a random track from that genre
            tracks_df = songs_by_genre.get(chosen_genre)
            if tracks_df is None or len(tracks_df) == 0:
                continue

            # Optional: weight by popularity
            if use_popularity_weights:
                track = tracks_df.sample(n=1, weights=tracks_df['popularity']).iloc[0]
            else:
                track = tracks_df.sample(n=1).iloc[0]

            # Generate realistic timestamp
            random_days = np.random.randint(0, 120)
            random_minutes = np.random.randint(0, 1440)
            timestamp = start_date + timedelta(days=random_days, minutes=random_minutes)

            all_events.append({
                "event_id": str(uuid.uuid4()),
                "user_id": user_id,
                "timestamp": timestamp.isoformat(),
                "track_id": track["track_id"],
                "track_name": track["track_name"],
                "track_genre": chosen_genre,
                "album_name": track["album_name"],
                "artists": json.dumps(track["artists_list"]),
                "primary_artist": track["primary_artist"],
                "danceability": track["danceability"],
                "energy": track["energy"],
                "valence": track["valence"],
                "popularity": track["popularity"]
            })

    events_df = pd.DataFrame(all_events)
    events_df.to_csv(output_path, index=False)
    print(f"Generated {len(events_df)} listening events → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--users_csv", type=str, required=True)
    parser.add_argument("--songs_csv", type=str, required=True)
    parser.add_argument("--output_path", type=str, default="synthetic_events.csv")
    parser.add_argument("--events_per_user", type=int, default=50)
    parser.add_argument("--use_popularity_weights", type=bool, default=True)
    args = parser.parse_args()

    generate_listening_events(
        users_csv=args.users_csv,
        songs_csv=args.songs_csv,
        output_path=args.output_path,
        events_per_user=args.events_per_user,
        use_popularity_weights=args.use_popularity_weights
    )