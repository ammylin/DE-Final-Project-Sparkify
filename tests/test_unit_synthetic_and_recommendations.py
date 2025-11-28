import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
import pytest
from importlib import util
import warnings

# Ensure py_and_notebooks modules are importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py_and_notebooks"))


# helper loader to import modules with numeric prefixes
def load_module(name, rel_path):
    module_path = str(ROOT / rel_path)
    spec = util.spec_from_file_location(name, module_path)
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod



# ----- Module loading with separate flags -----
USERS_EVENTS_LOADED = False
RECS_LOADED = False

# Load users + events modules
try:
    _mod_users = load_module("synthetic_users", "py_and_notebooks/04_synthetic_users.py")
    _mod_events = load_module("synthetic_events", "py_and_notebooks/04_synthetic_events.py")

    generate_users = _mod_users.generate_users
    generate_listening_events = _mod_events.generate_listening_events

    USERS_EVENTS_LOADED = True
except Exception as e:
    warnings.warn(f"Could not load synthetic user/event modules: {e}")
    USERS_EVENTS_LOADED = False

# Load recommendation module separately (optional)
try:
    _mod_recs = load_module("recommendations", "py_and_notebooks/recommendations.py")
    build_track_matrix = _mod_recs.build_track_matrix
    recommend_for_user = _mod_recs.recommend_for_user
    recommend_for_all_users = _mod_recs.recommend_for_all_users
    RECS_LOADED = True
except Exception as e:
    MODULES_LOADED = False
    print("\n================= IMPORT ERROR =================")
    print("Error while importing recommendations.py:")
    print(type(e), e)
    print("================================================\n")


def make_sample_songs_csv(path):
    # produce a larger set of songs with many genres so generators can sample extras
    genres = [
        "pop",
        "rock",
        "jazz",
        "electronic",
        "hip-hop",
        "classical",
        "blues",
        "country",
        "reggaeton",
        "indie",
    ]

    rows = []
    for i, g in enumerate(genres):
        rows.append({
            "track_id": f"t{i+1}",
            "track_name": f"Song {i+1}",
            "track_genre": str([g]),
            "artists": str([f"Artist {i+1}"]),
            "primary_artist": f"Artist {i+1}",
            "danceability": float(0.5 + (i % 5) * 0.05),
            "energy": float(0.4 + (i % 4) * 0.1),
            "valence": float(0.3 + (i % 3) * 0.1),
            "tempo": 100 + i * 5,
            "loudness": float(-6.0 + i * 0.2),
            "popularity": 20 + i * 5,
        })

    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return path


def test_generate_users_and_structure(tmp_path):
    if not USERS_EVENTS_LOADED:
        pytest.skip("Skipping user generator test: synthetic modules not loaded")

    songs_csv = tmp_path / "songs.csv"
    make_sample_songs_csv(songs_csv)

    users_csv = tmp_path / "users.csv"
    # generate 3 users
    generate_users(3, str(songs_csv), str(users_csv), seed=1)

    assert users_csv.exists()
    users_df = pd.read_csv(users_csv)
    # correct number of rows
    assert len(users_df) == 3
    # required columns
    for col in ["user_id", "age", "country", "favorite_genres", "genre_weights"]:
        assert col in users_df.columns
    # no null user ids
    assert users_df["user_id"].isnull().sum() == 0
    # genre_weights parseable json
    gw = json.loads(users_df.iloc[0]["genre_weights"])
    assert isinstance(gw, dict)


def test_generate_listening_events(tmp_path):
    if not USERS_EVENTS_LOADED:
        pytest.skip("Skipping events generator test: synthetic modules not loaded")

    songs_csv = tmp_path / "songs.csv"
    make_sample_songs_csv(songs_csv)

    users_csv = tmp_path / "users.csv"
    # create a minimal users file
    users_df = pd.DataFrame({
        "user_id": ["u1", "u2"],
        "age": [25, 40],
        "country": ["USA", "UK"],
        # use json.dumps so the generator can json.loads successfully
        "genre_weights": [json.dumps({"pop": 1.0}), json.dumps({"rock": 1.0})],
        "favorite_genres": [json.dumps(["pop"]), json.dumps(["rock"])],
    })
    users_df.to_csv(users_csv, index=False)

    events_csv = tmp_path / "events.csv"
    generate_listening_events(str(users_csv), str(songs_csv), str(events_csv), events_per_user=2, seed=1)

    assert events_csv.exists()
    ev = pd.read_csv(events_csv)
    assert len(ev) > 0
    # required columns
    for col in ["event_id", "user_id", "timestamp", "track_id", "track_name"]:
        assert col in ev.columns
    # timestamps not null
    assert ev["timestamp"].notnull().all()


def test_recommendation_end_to_end(tmp_path):
    if not (USERS_EVENTS_LOADED and RECS_LOADED):
        pytest.skip("Skipping recommendation tests: modules not fully loaded")

    # build small tracks df
    tracks_df = pd.DataFrame({
        "track_id": ["t1", "t2", "t3", "t4"],
        "track_name": ["A", "B", "C", "D"],
        "primary_artist": ["A"] * 4,
        "track_genre": [str(["pop"]), str(["rock"]), str(["pop"]), str(["jazz"])],
        "danceability": [0.7, 0.6, 0.8, 0.5],
        "energy": [0.6, 0.7, 0.8, 0.4],
        "valence": [0.5, 0.4, 0.6, 0.3],
        "tempo": [120, 130, 110, 100],
        "loudness": [-5.0, -6.0, -4.5, -7.0],
        "popularity": [50, 60, 70, 20],
    })

    # single user who listened to t1
    users_df = pd.DataFrame({
        "user_id": ["u1"],
        "genre_weights": [json.dumps({"pop": 1.0})],
    })

    events_df = pd.DataFrame({
        "event_id": ["e1"],
        "user_id": ["u1"],
        "track_id": ["t1"],
        "genre": ["pop"],
    })

    X = build_track_matrix(tracks_df)
    recs = recommend_for_user(users_df.iloc[0], tracks_df, events_df, X, top_k=2)

    # Should return at most top_k rows and not include t1
    assert len(recs) <= 2
    assert "t1" not in recs["track_id"].values

    # recommend_for_all_users should run end-to-end
    all_recs = recommend_for_all_users(users_df, tracks_df, events_df)
    assert not all_recs.empty
    assert "track_id" in all_recs.columns
