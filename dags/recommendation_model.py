import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
import hashlib
import warnings

warnings.filterwarnings('ignore')

# CONFIGURATION
EMBEDDING_DIMENSION = 64

# 1. TRACK EMBEDDING LOGIC (PCA-based)
def build_track_matrix(tracks_df: pd.DataFrame):
    """
    Transforms track audio features and genre into 64-dimensional embeddings using PCA.
    """
    
    # 1. Define Features
    numerical_features = [
        'popularity', 'duration_ms', 'danceability', 'energy', 
        'key', 'loudness', 'mode', 'speechiness', 'acousticness', 
        'instrumentalness', 'liveness', 'valence', 'tempo', 
        'time_signature'
    ]
    
    # Only 'first_genre' remains as a purely categorical text field
    categorical_features = ['first_genre']
    
    # Clean Data
    tracks_df[numerical_features] = tracks_df[numerical_features].fillna(tracks_df[numerical_features].mean())
    tracks_df[categorical_features] = tracks_df[categorical_features].fillna('unknown')

    # 2. Preprocessing Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ],
        remainder='drop' 
    )

    # Fit preprocessor
    X_processed = preprocessor.fit_transform(tracks_df)
    
    # 3. Dimensionality Reduction (PCA)
    pca = PCA(n_components=EMBEDDING_DIMENSION) 
    X_embeddings = pca.fit_transform(X_processed.toarray())
    
    return X_embeddings, None 


# 2. USER EMBEDDING LOGIC (Weighted Average)
def generate_user_vector(genre_weights: dict, genre_centroids: dict) -> np.ndarray:
    """
    Creates a user vector by mixing the real centroids of genres found in the track data.
    
    Args:
        genre_weights: {'pop': 0.8, 'rock': 0.2} (User's taste)
        genre_centroids: {'pop': [0.1, ...], 'rock': [0.9, ...]} (Actual average of tracks)
    """
    if not genre_weights:
        return np.zeros(EMBEDDING_DIMENSION)

    total_vector = np.zeros(EMBEDDING_DIMENSION)
    
    for genre, weight in genre_weights.items():
        # Get the ACTUAL average vector for this genre from the track data
        # If the genre doesn't exist in our tracks, use a zero vector (neutral)
        anchor = genre_centroids.get(genre, np.zeros(EMBEDDING_DIMENSION))
        
        # Add the weighted anchor vector to the total
        total_vector += anchor * weight
    
    return total_vector


# import pickle
# import numpy as np
# import pandas as pd
# from sklearn.preprocessing import StandardScaler
# from sklearn.metrics.pairwise import cosine_similarity
# from scipy.sparse import csr_matrix
# import json


# def build_track_matrix(tracks_df):
#     # Ensure genre_single exists
#     if "genre_single" not in tracks_df.columns:

#         def pick_first(x):
#             if isinstance(x, (list, tuple)):
#                 return x[0] if len(x) > 0 else None
#             return x

#         tracks_df["genre_single"] = tracks_df["track_genre"].apply(
#             lambda x: pick_first(eval(x)) if isinstance(x, str) else pick_first(x)
#         )

#     audio_features = ["danceability", "energy", "valence", "tempo", "loudness"]

#     # Standardize features
#     scaler = StandardScaler()
#     scaled = scaler.fit_transform(tracks_df[audio_features])
#     X = csr_matrix(scaled)

#     return X, scaler  # Return the scaler for inverse transformation if needed


# def recommend_for_user(user, tracks_df, events_df, X, top_k=10):
#     user_id = user["user_id"]

#     # Parse genre_weights
#     if isinstance(user["genre_weights"], str):
#         genre_weights = json.loads(user["genre_weights"])
#     else:
#         genre_weights = user["genre_weights"]

#     def genre_score(genre):
#         return genre_weights.get(genre, 0)

#     tracks_df = tracks_df.copy()
#     tracks_df["genre_pref"] = tracks_df["genre_single"].apply(genre_score)

#     # Listening history
#     user_events = events_df[events_df["user_id"] == user_id].copy()
#     listened_track_ids = user_events["track_id"].tolist()
#     user_events.loc[:, "genre"] = user_events["track_genre"]

#     genre_counts = user_events["genre"].value_counts().to_dict()
#     tracks_df["history_boost"] = tracks_df["genre_single"].apply(
#         lambda g: np.log1p(genre_counts.get(g, 0))
#     )

#     # Content similarity
#     if len(listened_track_ids) > 0:
#         listened_indices = tracks_df.index[
#             tracks_df["track_id"].isin(listened_track_ids)
#         ]
#         user_vector = (
#             X[listened_indices].mean(axis=0).A
#         )  # convert sparse to numpy array
#         content_sim = cosine_similarity(user_vector, X)[0]
#     else:
#         content_sim = np.zeros(len(tracks_df))
#     tracks_df["content_sim"] = content_sim

#     # Popularity + exploration
#     exploration = user.get("exploration_weight", 0.1)
#     pop_norm = (tracks_df["popularity"] - tracks_df["popularity"].min()) / (
#         tracks_df["popularity"].max() - tracks_df["popularity"].min()
#     )
#     explore_noise = np.random.rand(len(tracks_df))
#     tracks_df["explore_pop"] = (
#         pop_norm * (1 - exploration) + exploration * explore_noise
#     )

#     # Final score
#     tracks_df["final_score"] = (
#         0.40 * tracks_df["genre_pref"]
#         + 0.30 * tracks_df["content_sim"]
#         + 0.20 * tracks_df["history_boost"]
#         + 0.10 * tracks_df["explore_pop"]
#     )

#     # Filter out already listened tracks
#     recommended = tracks_df[~tracks_df["track_id"].isin(listened_track_ids)]

#     return recommended.sort_values("final_score", ascending=False).head(top_k)[
#         ["track_id", "track_name", "primary_artist", "genre_single", "final_score"]
#     ]


# def recommend_for_all_users(users_df, tracks_df, events_df):
#     print("Starting recommendation training...")
#     X, scaler = build_track_matrix(tracks_df)

#     all_results = []

#     for i, user in users_df.iterrows():
#         print(f"Processing user {i+1}/{len(users_df)}")
#         recs = recommend_for_user(user, tracks_df, events_df, X, top_k=10)

#         recs["user_id"] = user["user_id"]

#         all_results.append(recs)

#     # Save the model as pickle
#     # Convert X (csr_matrix) to dense numpy array to ensure compatibility with pickle
#     X_dense = X.toarray()

#     with open("/opt/airflow/data/recommendation_model.pkl", "wb") as f:

#         pickle.dump({"X": X_dense, "scaler": scaler}, f)

#     return pd.concat(all_results, ignore_index=True)
