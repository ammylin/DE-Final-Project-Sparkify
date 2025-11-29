import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
import hashlib
import warnings

warnings.filterwarnings("ignore")

# CONFIGURATION
EMBEDDING_DIMENSION = 64


# 1. TRACK EMBEDDING LOGIC (PCA-based)
def build_track_matrix(tracks_df: pd.DataFrame):
    """
    Transforms track audio features and genre into 64-dimensional embeddings using PCA.
    """

    # 1. Define Features
    numerical_features = [
        "popularity",
        "duration_ms",
        "danceability",
        "energy",
        "key",
        "loudness",
        "mode",
        "speechiness",
        "acousticness",
        "instrumentalness",
        "liveness",
        "valence",
        "tempo",
        "time_signature",
    ]

    # Only 'first_genre' remains as a purely categorical text field
    categorical_features = ["first_genre"]

    # Clean Data
    tracks_df[numerical_features] = tracks_df[numerical_features].fillna(
        tracks_df[numerical_features].mean()
    )
    tracks_df[categorical_features] = tracks_df[categorical_features].fillna("unknown")

    # 2. Preprocessing Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ],
        remainder="drop",
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
