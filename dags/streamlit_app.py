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
            recommendation_id,
            user_id,
            track_id,
            track_name,
            primary_artist,
            score,
            timestamp
        FROM music_analytics.recommendations
        ORDER BY timestamp DESC;
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

df = load_recommendations()
last_update = get_last_update()

# Sidebar Filters
st.sidebar.header("Filters")
users = df["user_id"].unique()
selected_user = st.sidebar.selectbox("Select user:", ["All"] + list(users))
if selected_user != "All":
    df = df[df["user_id"] == selected_user]

# KPI Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total recommendations", len(df))
col2.metric("Unique users recommended", df["user_id"].nunique())
col3.metric("Most recent generation", str(last_update) if last_update else "-")

# Main Table
st.subheader("🔽 Recommendations table")
st.dataframe(df, use_container_width=True, height=500)

# Score distribution chart
st.subheader("📈 Score distribution")
if len(df):
    st.bar_chart(df["score"])
else:
    st.info("No data available for this selection.")
