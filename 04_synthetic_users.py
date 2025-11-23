# 04_synthetic_users.py
"""
Generate synthetic users with demographic info and music genre preferences.
Each user includes:
- A unique user ID
- Age
- Country
- Favorite genres with associated weights reflecting their music preferences.  
- Generates a CSV file of synthetic users for use in simulating listening events.
"""
import numpy as np
import pandas as pd
import uuid
import json
import argparse
import ast

def generate_users(
    n_users: int,
    songs_csv_path: str,
    output_path: str,
    seed: int = 42
):
    np.random.seed(seed)

    # Load songs and parse genres
    songs = pd.read_csv(songs_csv_path)
    songs['track_genre_list'] = songs['track_genre'].apply(ast.literal_eval)

    # Get all unique genres
    all_genres = sorted(list({g for sublist in songs['track_genre_list'] for g in sublist}))

    countries = [
        "USA", "Canada", "UK", "Germany", "France", 
        "Mexico", "Brazil", "India", "Japan", "Australia"
    ]

    users = []

    for _ in range(n_users):
        user_id = str(uuid.uuid4())
        age = np.random.randint(16, 65)
        country = np.random.choice(countries)

        # Step 1: Choose 1–3 favorite genres
        num_favs = np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
        favorite_genres = list(np.random.choice(all_genres, size=num_favs, replace=False))

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
            replace=False
        )
        for g in extra_genres:
            weights[g] = np.random.uniform(0.01, 0.05)

        # Normalize weights
        total = sum(weights.values())
        weights = {g: round(w / total, 4) for g, w in weights.items()}

        users.append({
            "user_id": user_id,
            "age": age,
            "country": country,
            # store as JSON list for favorite genres
            "favorite_genres": json.dumps(favorite_genres),
            # store as JSON dict for weights
            "genre_weights": json.dumps(weights)
        })

    users_df = pd.DataFrame(users)
    users_df.to_csv(output_path, index=False)
    print(f"Generated {n_users} users → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_users", type=int, default=2000)
    parser.add_argument("--songs_csv_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, default="synthetic_users.csv")
    args = parser.parse_args()

    generate_users(args.n_users, args.songs_csv_path, args.output_path)