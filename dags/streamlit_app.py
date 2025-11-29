import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

load_dotenv()

# Auto-refresh every 2 minutes (120,000 ms)
st_autorefresh(interval=120_000, key="auto_refresh")


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


def load_recommendations():
    conn = get_connection()
    query = """
        SELECT
            A.recommendation_id,
            A.user_id,
            A.track_id,
            A.track_name,
            B.first_genre AS track_genre,
            A.primary_artist,
            A.score,
            A.timestamp
        FROM music_analytics.recommendations     A
        JOIN music_analytics.track_primary_genre B
        ON A.track_id = B.track_id
        ORDER BY A.timestamp DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def get_last_update():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT MAX(timestamp) 
        FROM music_analytics.recommendations;
    """
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None


# --- Streamlit UI ---
st.set_page_config(page_title="Music Recommendation Dashboard", layout="wide")

st.title("🎵 Music Recommendation Dashboard")
st.caption("Data generated automatically by the Airflow DAG `inference`")

df_full = load_recommendations()
last_update = get_last_update()

# Sidebar Filters
st.sidebar.header("Filters")
users = df_full["user_id"].unique()
selected_user = st.sidebar.selectbox("Select user:", ["All"] + list(users))

# Create filtered copy
df_filtered = df_full.copy()
if selected_user != "All":
    df_filtered = df_full[df_full["user_id"] == selected_user]

# KPI Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total recommendations", len(df_filtered))
col2.metric("Unique users recommended", df_full["user_id"].nunique())
col3.metric("Most recent generation", str(last_update) if last_update else "-")

# Main Table
st.subheader("🔽 Recommendations table")
st.dataframe(df_filtered, use_container_width=True, height=500)

# Global histogram (all users)
st.subheader("🎨 Genre Distribution (All Users)")
if "track_genre" in df_full.columns and len(df_full):
    genre_counts = df_full["track_genre"].value_counts().sort_values(ascending=False)
    st.bar_chart(genre_counts)
else:
    st.info("No track_genre data available.")

# Per-user histogram
if selected_user != "All":
    st.subheader(f"🎨 Genre Distribution for User: {selected_user}")
    if "track_genre" in df_filtered.columns and len(df_filtered):
        user_genre_counts = df_filtered["track_genre"].value_counts().sort_values(ascending=False)
        st.bar_chart(user_genre_counts)
    else:
        st.info("No track_genre data available for this user.")

# Global Top Tracks
st.subheader("🏆 Top Track Names (All Users)")
if "track_name" in df_full.columns and len(df_full):
    top_tracks = df_full["track_name"].value_counts().head(20)
    st.bar_chart(top_tracks)
else:
    st.info("No track_name data available.")

# Per-user Top Tracks — only show when a specific user is selected
if selected_user != "All":
    st.subheader(f"🏆 Top Track Names for User: {selected_user}")
    if "track_name" in df_filtered.columns and len(df_filtered):
        top_tracks_user = df_filtered["track_name"].value_counts().head(20)
        st.bar_chart(top_tracks_user)
    else:
        st.info("No track_name data available for this user.")

# Global Top Artists
st.subheader("🎤 Top Primary Artists (All Users)")
if "primary_artist" in df_full.columns and len(df_full):
    top_artists = df_full["primary_artist"].value_counts().head(20)
    st.bar_chart(top_artists)
else:
    st.info("No primary_artist data available.")

# Per-user Top Artists — only show when a specific user is selected
if selected_user != "All":
    st.subheader(f"🎤 Top Primary Artists for User: {selected_user}")
    if "primary_artist" in df_filtered.columns and len(df_filtered):
        top_artists_user = df_filtered["primary_artist"].value_counts().head(20)
        st.bar_chart(top_artists_user)
    else:
        st.info("No primary_artist data available for this user.")