# Spotify Listening Analytics Pipeline  
### End-to-End Data Engineering with Spotify Track Data

This project builds a complete modern **data engineering pipeline** using the Spotify Kaggle dataset plus optional synthetic/API-based listening data.  
The pipeline demonstrates ingestion, storage, transformation, orchestration, analysis, and dashboarding — with a focus on modularity, scalability, observability, and best practices in data engineering.

---

# 1. Project Concept

## Storyline
This project ingests:
- **Spotify track metadata** from Kaggle (audio features, popularity, genres, artists)
- **Synthetic or API-based listening events**

It stores them in a **data lake + warehouse**, transforms them using **Polars or PySpark**, orchestrates the entire workflow with **Airflow or Prefect**, and exposes:
- Analytics tables
- Real SQL queries
- A simple regression/statistical insight
- A Streamlit dashboard for visualization

This design follows a layered modern data stack:
**raw → cleaned → analytics → model → dashboard**

---

# 2. Architecture & Data Flow

Below is the pipeline broken into layers.

Data Sources
→ Ingestion
→ Raw Storage (data lake)
→ Transformations (Polars/PySpark)
→ Warehouse (Postgres/DuckDB)
→ Analytics Tables
→ Regression Model
→ Dashboard


---

## 2.1 Data Sources (Ingestion Layer)

### **Source 1 – Real Data**
**Kaggle Spotify Tracks Dataset**, containing:
- Audio features (danceability, energy, valence, tempo…)
- Track popularity
- Artist metadata
- Genres

### **Source 2 – Semi-Real / Synthetic Data**
You choose one:

#### **Option A (Recommended): Synthetic listening events**
A generator produces:
- `user_id`
- `track_id`
- `timestamp`
- `device`
- `skipped`
- `session_id`

#### **Option B: Spotify Web API (optional add-on)**
Fetch additional metadata for a subset of tracks or artists.

---

## 2.2 Storage Layer (Data Lake + Warehouse)

### **Data Lake (simulated S3)**
Folder structure:
data/raw/spotify_tracks/
data/raw/listening_events/
data/processed/ # cleaned/parquet


### **Warehouse Layer (Postgres or DuckDB)**  
Tables include:

- **tracks**
- **artists**
- **listening_events**
- **daily_aggregates**
- **model_features**

These support downstream queries, dashboards, and regression.

---

## 2.3 Transform + Analysis Layer

Using **Polars or PySpark** for transformations:

### **Cleaning**
- Normalize column names
- Fix datatypes
- Validate IDs
- Handle missing values

### **Analytics Tables**
- Daily listening counts per track/artist  
- Skip rate per track or genre  
- Popularity trends over time  

### **Regression / Statistical Insight**
A simple, meaningful model such as:

**Model:** Logistic or linear regression predicting:
- Skip probability  
OR  
- Popularity bucket  

**Features:**
- danceability  
- energy  
- valence  
- tempo  
- popularity  

**Example insight:**
> Higher danceability is associated with lower probability of skip, controlling for other audio features.

---

## 2.4 Orchestration Layer (Airflow or Prefect)

A pipeline DAG may include tasks like:

1. `download_kaggle_data` or `load_kaggle_export`
2. `generate_listening_events`
3. `load_to_raw_storage`
4. `transform_to_cleaned`
5. `load_to_warehouse`
6. `compute_daily_aggregates`
7. `run_regression_analysis`
8. `update_dashboard_materialized_views` (optional)

Tasks run **daily or on-demand**.

---

## 2.5 Serving / Visualization Layer

### **Option 1: Streamlit Dashboard (recommended)**
It can show:

- Top tracks/artists by daily streams  
- Skip rate by genre  
- Regression insight plots  

---



---

## ✅ Data Ingestion
Real data from Kaggle using:
- `ingestion/ingest_kaggle_tracks.py`  
- OR Kaggle API inside the DAG  

Secondary source:
- `ingestion/generate_listening_events.py` (synthetic event generator)  
- Optional `fetch_spotify_api.py`

---

## ✅ Data Storage
**Lake:**  
`data/raw/` and `data/processed/` as Parquet/CSV  

**Warehouse:**
Postgres or DuckDB with tables:
- tracks  
- artists  
- listening_events  
- daily_track_metrics  

README contains schema diagrams & descriptions.

---

## ✅ Data Querying
Store SQL files in `sql/`.

Example queries:
- Top tracks in past 7 days  
- Skip rate by genre  
- Tracks with high skip probability but high actual popularity  

Use via:
- `psql`
- `sqlalchemy`
- scripts
- or notebooks

---

## ✅ Data Transformation & Analysis

### Example scripts:
transformations/clean_tracks.py
transformations/join_tracks_events.py
analysis/regression_model.py


**Regression output includes:**
- coefficients  
- accuracy/AUC/R²  
- insights  
- a plot used in the dashboard  

---

## ✅ Architecture & Orchestration
Airflow DAG example:
dags/spotify_pipeline_dag.py



[Kaggle + Synthetic Events]
↓
[Ingestion]
↓
[Raw Data Lake]
↓
[Polars/PySpark Transforms]
↓
[Warehouse DB]
↓
[Analytics & Regression]
↓
[Dashboard]



---

## ✅ Containerization, CI/CD, Testing

### **Containerization**
- `Dockerfile`  
- `docker-compose.yml` (runs app + Postgres + optional Airflow)

### **CI/CD**
Workflow in:  
`.github/workflows/ci.yml`

Runs:
- `pytest`
- `flake8` or `ruff`
- (optional) Polars/Spark sample transform

### **Testing**
Unit tests:
- transformation output validity  
- synthetic event generator  

Integration test:
- end-to-end mini pipeline run using small sample data  

---

# 4. Undercurrents of Data Engineering

The README includes a dedicated reflection describing how the project implements:

### **Scalability**
- Parquet + Polars/Spark  
- Decoupled storage & compute  
- DAG-based modular tasks  

### **Modularity & Reusability**
- Ingestion, transformation, modeling, and dashboard modules are independent  
- Reusable transformation & utility functions  

### **Observability**
- Airflow/Prefect logging  
- Pipeline run logs  

### **Data Governance & Security**
- `.env` secrets  
- `.gitignore` includes all data & credentials  
- Clear schema expectations  

### **Reliability & Efficiency**
- Idempotent tasks   
- Partitioned data folders  
- Vectorized Polars transformations  

---


