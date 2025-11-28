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

# HELPER: Deterministic Random Vectors for Genres
def get_genre_anchor(genre_name: str) -> np.ndarray:
    """
    Generates a stable random vector for a specific genre string.
    
    How it works:
    1. Hashes the genre name (e.g., "pop") into a unique fingerprint.
    2. Uses that fingerprint as a Seed for the random number generator.
    3. Generates the vector.
    
    Result: "pop" always produces the exact same vector, every time,
    on any machine, without needing a hardcoded dictionary.
    """
    # 1. Create a hash from the string
    hash_object = hashlib.md5(genre_name.encode())
    
    # 2. Convert hash to an integer seed (keeping it within valid 32-bit range)
    seed = int(hash_object.hexdigest(), 16) % (2**32)
    
    # 3. Create a generator with that seed and produce the 64-dim vector
    rng = np.random.default_rng(seed)
    return rng.random(EMBEDDING_DIMENSION)

# 1. TRACK EMBEDDING LOGIC (PCA)
def build_track_matrix(tracks_df: pd.DataFrame):
    """
    Transforms track audio features and genre into 64-dimensional embeddings using PCA.
    """
    
    # 1. Define Features
    # These are the standard audio features provided by Spotify
    numerical_features = [
        'popularity', 'duration_ms', 'danceability', 'energy', 
        'key', 'loudness', 'mode', 'speechiness', 'acousticness', 
        'instrumentalness', 'liveness', 'valence', 'tempo', 
        'time_signature'
    ]
    
    # 'first_genre' comes from our upstream SQL feature engineering task
    categorical_features = ['first_genre']
    
    # Clean Data: Fill NA values to prevent errors
    # Numeric gets mean, Categorical gets 'unknown'
    tracks_df[numerical_features] = tracks_df[numerical_features].fillna(tracks_df[numerical_features].mean())
    tracks_df[categorical_features] = tracks_df[categorical_features].fillna('unknown')

    # 2. Preprocessing Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            # Scale numerical features (normalize distribution)
            ('num', StandardScaler(), numerical_features),
            # One-Hot Encode categorical features (convert text to binary columns)
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ],
        remainder='drop' 
    )

    # Fit preprocessor and transform data into a sparse matrix
    X_processed = preprocessor.fit_transform(tracks_df)
    
    # 3. Dimensionality Reduction (PCA)
    # Compress the massive sparse matrix down to 64 dense features
    pca = PCA(n_components=EMBEDDING_DIMENSION) 
    X_embeddings = pca.fit_transform(X_processed.toarray())
    
    # Return the embeddings 
    return X_embeddings, None 


# 2. USER EMBEDDING LOGIC (Weighted Average)
def generate_user_vector(genre_weights: dict) -> np.ndarray:
    """
    Creates a user vector by mixing the stable anchor vectors of their favorite genres.
    
    Example
    Input: {'pop': 0.8, 'rock': 0.2}
    Output: A 64-dim vector that is 80% 'Pop Vector' and 20% 'Rock Vector'.
    """
    # Check for empty dictionaries
    if not genre_weights:
        return np.zeros(EMBEDDING_DIMENSION)

    total_vector = np.zeros(EMBEDDING_DIMENSION)
    
    for genre, weight in genre_weights.items():
        # DYNAMICALLY get the anchor using the hash function
        anchor = get_genre_anchor(genre)
        
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
