import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import json


def build_track_matrix(tracks_df):
    # Ensure genre_single exists
    if "genre_single" not in tracks_df.columns:

        def pick_first(x):
            if isinstance(x, (list, tuple)):
                return x[0] if len(x) > 0 else None
            return x

        tracks_df["genre_single"] = tracks_df["track_genre"].apply(
            lambda x: pick_first(eval(x)) if isinstance(x, str) else pick_first(x)
        )

    audio_features = ["danceability", "energy", "valence", "tempo", "loudness"]

    # Standardize features
    scaler = StandardScaler()
    scaled = scaler.fit_transform(tracks_df[audio_features])
    X = csr_matrix(scaled)

    return X, scaler  # Return the scaler for inverse transformation if needed


def recommend_for_user(user, tracks_df, events_df, X, top_k=10):
    user_id = user["user_id"]

    # Parse genre_weights
    if isinstance(user["genre_weights"], str):
        genre_weights = json.loads(user["genre_weights"])
    else:
        genre_weights = user["genre_weights"]

    def genre_score(genre):
        return genre_weights.get(genre, 0)

    tracks_df = tracks_df.copy()
    tracks_df["genre_pref"] = tracks_df["genre_single"].apply(genre_score)

    # Listening history
    user_events = events_df[events_df["user_id"] == user_id].copy()
    listened_track_ids = user_events["track_id"].tolist()
    user_events.loc[:, "genre"] = user_events["track_genre"]

    genre_counts = user_events["genre"].value_counts().to_dict()
    tracks_df["history_boost"] = tracks_df["genre_single"].apply(
        lambda g: np.log1p(genre_counts.get(g, 0))
    )

    # Content similarity
    if len(listened_track_ids) > 0:
        listened_indices = tracks_df.index[
            tracks_df["track_id"].isin(listened_track_ids)
        ]
        user_vector = (
            X[listened_indices].mean(axis=0).A
        )  # convert sparse to numpy array
        content_sim = cosine_similarity(user_vector, X)[0]
    else:
        content_sim = np.zeros(len(tracks_df))
    tracks_df["content_sim"] = content_sim

    # Popularity + exploration
    exploration = user.get("exploration_weight", 0.1)
    pop_norm = (tracks_df["popularity"] - tracks_df["popularity"].min()) / (
        tracks_df["popularity"].max() - tracks_df["popularity"].min()
    )
    explore_noise = np.random.rand(len(tracks_df))
    tracks_df["explore_pop"] = (
        pop_norm * (1 - exploration) + exploration * explore_noise
    )

    # Final score
    tracks_df["final_score"] = (
        0.40 * tracks_df["genre_pref"]
        + 0.30 * tracks_df["content_sim"]
        + 0.20 * tracks_df["history_boost"]
        + 0.10 * tracks_df["explore_pop"]
    )

    # Filter out already listened tracks
    recommended = tracks_df[~tracks_df["track_id"].isin(listened_track_ids)]

    return recommended.sort_values("final_score", ascending=False).head(top_k)[
        ["track_id", "track_name", "primary_artist", "genre_single", "final_score"]
    ]


def recommend_for_all_users(users_df, tracks_df, events_df, chunk_size=500):
    print("Starting recommendation training...")
    X, scaler = build_track_matrix(tracks_df)

    all_results = []

    for start in range(0, len(users_df), chunk_size):
        end = min(start + chunk_size, len(users_df))
        chunk = users_df.iloc[start:end]

        print(f"Processing users {start+1} to {end} / {len(users_df)}")

        for i, user in chunk.iterrows():
            recs = recommend_for_user(user, tracks_df, events_df, X, top_k=10)
            recs["user_id"] = user["user_id"]
            all_results.append(recs)

        print(f"Finished processing users {start+1} to {end}")

    # Save the model as pickle
    # Convert X (csr_matrix) to dense numpy array to ensure compatibility with pickle
    X_dense = X.toarray()

    with open("/opt/airflow/data/recommendation_model.pkl", "wb") as f:

        pickle.dump({"X": X_dense, "scaler": scaler}, f)

    return pd.concat(all_results, ignore_index=True)
