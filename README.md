# DE-Final-Project-Sparkify

# Sparkify Music Recommendation Pipeline  
A full end-to-end data engineering + machine learning system that ingests track metadata, generates synthetic user listening activity, builds a content-based recommendation model, runs scheduled Airflow DAGs to update embeddings and recommendations, and serves results to a Streamlit dashboard.

## Project Overview  
This project builds a production-style music recommendation pipeline that combines:

- **Kaggle track dataset**  
- **Synthetic users + listening event generator**  
- **Content-based recommendation model**  
- **Postgres warehouse**  
- **Airflow orchestration**  
- **Streamlit dashboard**  
- **Automated tests + CI/CD**

The goal is to simulate the infrastructure of a real music analytics platform (“Sparkify”) where new listening activity and track data continuously flow through an ETL + ML pipeline, producing fresh recommendations for every user.

## Dataset Background

The song metadata for this project is based on the public Spotify Tracks Dataset found on Kaggle: https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset. This dataset provides a large collection of tracks along with rich audio features, making it well-suited for building embeddings and powering a recommendation pipeline. This dataset contains about 114,000 rows, where each row represents a single song.

### Dataset Contents

Each row represents one Spotify track, including:
- Track identifiers (id number)
- Artists
- Album name 
- Genre
- Popularity scores
- Audio features (danceability, energy, instrumentalness, etc)
- Timing and rhythm information (tempo, time signature, duration)

These features allow us to build realistic track embeddings and support downstream recommendation logic.

## Introduction / Exploratory Data Analysis (EDA)  
EDA notebooks (`00_eda.ipynb` and `03_eda.ipynb`) explore the structure and quality of the raw Kaggle track dataset.

**Highlights from the EDA:**
- Visualized distribution of genres, artists, and track metadata.  
- Inspected numeric audio features such as:
  - energy  
  - valence  
  - danceability  
  - loudness  
  - speechiness  
  - acousticness  
- Investigated correlations between features and potential data leakage.  
- Identified missing values, inconsistent types, and outliers.  
- Confirmed suitability of audio features for content-based similarity modeling.

The EDA step establishes which features are reliable inputs to the recommendation model.

## Data Cleaning  
The cleaning notebook (`02_clean_data.ipynb`) transforms the raw dataset into a modeling-ready format.

**Key cleaning steps:**
- Dropping unused or redundant columns.  
- Filling or removing missing numeric feature values.  
- Ensuring each track has a unique `track_id`.  
- Normalizing audio features for later vector-based similarity computation.  
- Validating column types and ensuring genre/artist consistency.  
- Exporting cleaned data to CSV for loading into Postgres.

The cleaned dataset becomes the starting point for downstream Airflow DAGs.

## DAG #1 — Ingestion & Embeddings  
The first Airflow DAG (`ingestion_embeddings.py`) is responsible for refreshing model inputs and outputs on a daily schedule.

### **DAG Responsibilities**
1. **Load raw tables**  
   - Pull `tracks`, `users`, and `listening_events` from Postgres.

2. **Build Track Embedding Matrix**  
   - Uses `build_track_matrix()` from `recommendation_model.py`.  
   - Standardizes feature columns.  
   - Saves an (n_tracks × n_features) embedding matrix back to Postgres.

3. **Generate User Vectors**  
   - For each user, aggregate their listening history.  
   - Convert to a numerical vector using `generate_user_vector()`.

4. **Compute User Recommendations**  
   - Compute cosine similarity between the user vector and all track embeddings.  
   - Exclude previously listened tracks.  
   - Write Top-N recommendations to the `user_recommendations` table.

5. **Validation**  
   - Validate schema integrity.  
   - Ensure no null or duplicate IDs.  
   - Confirm embedding shapes.  
   - Verify that every user receives recommendations.

### **Output Tables**
- `track_embeddings`  
- `user_vectors`  
- `user_recommendations`

This DAG is the core of the ML pipeline.
![output](images/successful_dag1.png)
![output](images/inference-graph.png)

## DAG #2 — Inference  
The second DAG or script (`inference.py`) supports **on-demand recommendations**.

### **Functions**
- Loads the latest track embeddings and user listening events.  
- Accepts a specific `user_id`.  
- Runs:
  - vector construction  
  - similarity scoring  
  - Top-N ranking  
- Returns recommendations in a JSON-friendly structure.

This inference layer is used directly by the dashboard and can be triggered programmatically.
![output](images/successful_dag2.png)

## Dashboard (Streamlit)  
`streamlit_app.py` provides an interactive front-end to explore recommendations.

### **Features**
- Dropdown sidebar to select a user.  
- Real-time query to the inference script.  
- Table of:
  - recommended tracks  
  - similarity scores  
  - relevant metadata  
- Auto-refresh for live updates.  
- Uses Postgres + dotenv for environment configuration.

The dashboard demonstrates how analysts or product managers would consume the pipeline’s output.

# Dashboard Visualizations  

The Streamlit dashboard provides an interactive interface for exploring recommendations generated by the Airflow pipelines. It surfaces several insights about **global listening trends**, **individual user behavior**, and the **final recommendation outputs** stored in Postgres. These visualizations demonstrate how model outputs are consumed and interpreted by analysts or product managers.

---

## 🎤 Top Primary Artists (All Users & Per User)

![Top Primary Artists](images/dashboard_top_artists.png)

This chart summarizes the **most frequently listened-to primary artists across all synthetic users**.  
It aggregates listening events and counts how many times each artist appears as the primary artist for a played track.

**What this view shows:**

- Global popularity patterns across the entire user base  
- Which artists dominate listening behavior  
- How synthetic users behave relative to real-world expectations  
- Whether listening patterns are balanced or skewed toward certain artists  

Below the global chart is a **per-user version** that shows the top primary artists for a selected user. This makes it easy to compare:

- Individual user preferences  
- Alignment (or misalignment) with global popularity  
- How personalized the recommendation engine must be to serve each user  

---

## Genre Distribution (Per User)

![Genre Distribution](images/dashboard_tracks_and_genre.png)

This visualization shows the **genre distribution for a selected user**, based on their listening history.  
Each bar represents how many tracks from each genre the user has consumed.

**What this view shows:**

- Dominant genres in the user's listening behavior  
- Whether users have diverse or concentrated music tastes  
- How genre preferences influence user embeddings  
- Which genres are likely to shape future recommendations  

Genre-level insights help validate that the recommendation engine produces results consistent with user preferences.

---

## Top Track Names (All Users)

Also shown in the second screenshot is a chart of the **Top Track Names across all users**.  
This represents the most frequently played tracks in the synthetic dataset.

**What this view shows:**

- Global track-level popularity  
- Whether tracks correlate with top artists and genres  
- Skew or imbalance in listening behaviors  
- How track popularity may affect recommendation scoring  

This helps provide context for why certain tracks appear frequently in recommendations.

---

## Full Recommendations Table

![Recommendations Table](images/dashboard_recommendations.png)

The dashboard includes a **Recommendations Table** that displays the results of the Airflow `inference` DAG.  
This table is a direct view of the `user_recommendations` table stored in Postgres and refreshed automatically.

Each row includes:

- `recommendation_id` — unique identifier  
- `user_id` — user receiving the recommendation  
- `track_id` — recommended track  
- `track_name` — name of the track  
- `track_genre` — genre of the track  
- `primary_artist` — primary associated artist  
- `score` — cosine similarity score  
- `timestamp` — when the recommendation was generated  

**Why this table matters:**

- Validates that the recommendation engine is producing outputs on schedule  
- Shows the total number of recommendations and unique users served  
- Provides the timestamp of the most recent Airflow run  
- Allows inspection of recommendation quality and diversity  

This table represents the final stage of the pipeline—where embedded features, user vectors, and similarity-based ranking become actionable recommendations.

---


# Testing

Our pipeline uses a **two-layer testing strategy** designed for data engineering workflows:  
(1) fast Python logic tests that run in CI, and  
(2) runtime validation tasks embedded directly in Airflow to ensure end-to-end data quality.

---

## 1. Python Simulation Tests (Logic-Level)

All Python tests live under:

```
tests/
├── conftest.py
├── test_database_operations.py
├── test_inference_operations.py
├── test_recommendation_model.py
└── test_integration_edge_cases.py
```

These tests **do not call Airflow tasks**. Instead, they simulate core pipeline logic using small, controlled pandas DataFrames and numpy vectors.

### These tests cover:
- database operation behavior (mocked connections, schema expectations)  
- recommendation logic (cosine similarity, ranking, filtering listened tracks)  
- inference logic (pickle loading, embedding math, missing-user edge cases)  
- boundary conditions and failure cases (empty histories, malformed embeddings)  
- shared fixtures for consistent, deterministic test data  

---

## 2. Airflow DAG Validation Tasks (Runtime Data Quality)

In addition to Python tests, each major DAG includes **explicit validation tasks** that run every time the pipeline executes.

Validation logic exists in:

```
dags/model_pipeline/ingestion_embeddings.py
dags/model_pipeline/inference.py
```

### These validators enforce:
- required Postgres tables exist and contain rows  
- tracks/users/events tables have correct schema and no duplicate IDs  
- track and user embeddings are non-null and correctly formatted  
- the model pickle contains expected structures (`user_map`, `track_matrix`, `track_meta`)  
- generated recommendations contain valid fields and non-negative scores  

### Why:
These checks protect the *live* pipeline from corrupted tables, malformed embeddings, broken pickle artifacts, or invalid recommendation output—issues that cannot be detected by offline tests alone.

---

## 3. How Both Layers Work Together

| Layer | Validates | Runs In | Purpose |
|-------|-----------|---------|---------|
| **Python Simulation Tests** | Logic and model behavior | Local / CI | Fast, isolated verification of core functions |
| **Airflow Validation Tasks** | Real data, Postgres state, embeddings, pickle integrity | Airflow runtime | Prevents invalid data from entering production tables |

This hybrid approach ensures both **functional correctness** and **pipeline reliability** without the overhead of executing full DAGs in CI.

# GitHub Actions CI/CD Workflow

The project uses **GitHub Actions** to automatically run tests, linting, and security checks on every push or pull request to `main` or `develop`. The workflow ensures stability, code quality, and early detection of issues.

The pipeline includes four jobs: **tests**, **lint**, **security**, and **build-status**.

---

## 1. Test Job — Unit Tests & Coverage

Runs the core validation for the recommendation logic, synthetic data functions, and DAG utilities.

**Steps performed:**
- Install dependencies  
- Run `flake8` for syntax checks  
- Execute unit tests:

```bash
pytest tests/ -v --tb=short --ignore=tests/test_integration_edge_cases.py
```

- Generate coverage reports  
- Upload results to Codecov  

**Purpose:** ensure that core logic remains correct and regression-free.

---

## 2. Lint Job — Formatting & Static Analysis

Runs style and formatting tools:

- **isort** for import ordering  
- **black** for formatting  
- **pylint** for static analysis  

Lint errors do **not** block merges (`continue-on-error: true`) but provide useful feedback.

---

## 3. Security Job — Vulnerability Checks

Uses:

- **Bandit** to scan Python code  
- **Safety** to check dependencies  

Findings surface security issues without blocking development.

---

## 4. Build Status Job

Runs after testing and marks the overall workflow as pass/fail based on the test results.

---

## Why It Matters

- Prevents logic regressions  
- Ensures consistent, high-quality code  
- Surfaces security risks early  
- Keeps the development workflow stable and reliable  

This CI/CD pipeline provides automated assurance that every commit maintains the integrity of the project.



## Limitations & Future Work  

### **Current Limitations**
- The recommendation model is purely content-based and does not incorporate:
  - collaborative filtering  
  - temporal patterns  
  - user session behaviors  
- Synthetic listening data may not fully represent real-world behavior.  
- No deduplication or advanced validation yet in Airflow DAGs.  
- Inference is synchronous and not optimized for large user populations.  
- Feature engineering does not yet include embeddings learned from deep models.

### **Future Improvements**
- Integrate **collaborative filtering** or **hybrid models**.  
- Add real-time streaming ingestion with Kafka/Kinesis.  
- Expand synthetic generator to simulate:
  - session length  
  - skip behavior  
  - popularity biases  
- Replace basic cosine similarity with:
  - neural embeddings  
  - metric learning  
  - autoencoder-based track representations  
- Add caching and asynchronous inference for scalability.


# Setup Instructions

This section describes how to set up the three core components required to run the Sparkify Music Recommendation Pipeline: **PostgreSQL**, **Airflow**, and **Streamlit**.

---

## PostgreSQL Setup

PostgreSQL is the data warehouse used to store:
- cleaned track metadata  
- synthetic users  
- listening events  
- track embeddings  
- user recommendations  

### **1. Install PostgreSQL**

**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```


### **2. Create the Database**
```bash
createdb sparkify
```

### **3. Configure Environment Variables**
Create a `.env` file:
```
DB_NAME=sparkify
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

### **4. Test the Connection**
```bash
psql -d sparkify -U postgres
```

---

## Airflow Setup

Airflow orchestrates ingestion, embedding generation, and recommendation refresh.
With the docker-compose file and .Dockerfile updated with the necessary Airflow configurations, run the following to start the Airflow services, build the image, and staart the container:
```bash
cd .devcontainer
docker compose build --no-cache
docker compose up -d
```

Open Airflow UI:  
http://localhost:8080

### **5. Enable DAGs**
Turn on:
- `ingestion_embeddings`  
- `inference` 

---

## Streamlit Setup

Streamlit hosts the interactive dashboard for exploring recommendations.

### **1. Install Dependencies**
If using the provided file:
```bash
pip install -r requirements-streamlit.txt
```

### **2. Run the Dashboard**
```bash
streamlit run streamlit_app.py
```

### **3. Access the UI**
Open:  
http://localhost:8501

Streamlit will:
- connect to PostgreSQL  
- display top tracks, genres, and artists  
- allow selecting specific users  
- show the recommendation table  

---


