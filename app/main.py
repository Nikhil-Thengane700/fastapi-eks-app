import os
import time
import logging

import psycopg2
from fastapi import FastAPI, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="fastapi-eks-app")

# --- simple in-memory metrics ---
REQUEST_COUNT = Counter("app_requests_total", "Total requests", ["endpoint"])

# --- DB config (from env vars, populated via ConfigMap + Secret) ---
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=3,
    )


@app.get("/health")
def health():
    """Liveness check - process is up. No external dependencies checked."""
    REQUEST_COUNT.labels(endpoint="/health").inc()
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness check - can this pod actually serve traffic (DB reachable)?"""
    REQUEST_COUNT.labels(endpoint="/ready").inc()
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return Response(content='{"status": "not ready"}', status_code=503, media_type="application/json")


@app.get("/")
def root():
    REQUEST_COUNT.labels(endpoint="/").inc()
    return {"message": "fastapi-eks-app is running"}


@app.get("/db-time")
def db_time():
    """Simple DB-connected endpoint - proves the app can talk to RDS."""
    REQUEST_COUNT.labels(endpoint="/db-time").inc()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT NOW();")
    result = cur.fetchone()
    cur.close()
    conn.close()
    return {"db_time": str(result[0])}


@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
