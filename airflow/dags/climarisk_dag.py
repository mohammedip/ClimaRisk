import time
import logging
import os
from datetime import datetime, timezone, timedelta

import requests as _requests

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger("climarisk.dag")

# ── Config ────────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("POSTGRES_HOST", "postgres"),
    "port":     int(os.environ.get("POSTGRES_PORT", 5432)),
    "dbname":   "climarisk",
    "user":     os.environ.get("POSTGRES_USER", "climarisk"),
    "password": os.environ.get("POSTGRES_PASSWORD", "climarisk"),
}

BACKEND_URL     = os.environ.get("BACKEND_URL", "http://backend:8000")
PUSHGATEWAY_URL = os.environ.get("PROMETHEUS_PUSHGATEWAY_URL", "http://pushgateway:9091")

# ── DAG credentials (service account) ────────────────────────────────────────
DAG_USERNAME = os.environ.get("DAG_USERNAME", "reida")
DAG_PASSWORD = os.environ.get("DAG_PASSWORD", "123456")

# ── DAG default args ──────────────────────────────────────────────────────────
default_args = {
    "owner":            "climarisk",
    "depends_on_past":  False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=2),
    "email_on_failure": False,
    "email_on_retry":   False,
}

dag = DAG(
    dag_id="climarisk_predictions",
    description="Fetch weather + run flood/fire predictions for all active zones",
    default_args=default_args,
    schedule_interval="0 */5 * * *",
    start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    tags=["climarisk", "predictions", "weather"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_conn():
    import psycopg2
    return psycopg2.connect(**DB_CONFIG)


def _get_token() -> str:
    resp = _requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={"username": DAG_USERNAME, "password": DAG_PASSWORD},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


# ── Task 1: Get all active zones ──────────────────────────────────────────────

def get_active_zones(**context):
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, code, latitude, longitude
            FROM zones
            WHERE is_active = TRUE
        """)
        rows = cur.fetchall()
    finally:
        conn.close()

    zones = [
        {
            "id":        row[0],
            "name":      row[1],
            "code":      row[2],
            "latitude":  float(row[3]),
            "longitude": float(row[4]),
        }
        for row in rows
    ]

    logger.info(f"Found {len(zones)} active zones")
    context["ti"].xcom_push(key="zones", value=zones)
    return len(zones)


# ── Task 2: Run predictions for all zones ─────────────────────────────────────

def predict_all_zones(**context):
    zones = context["ti"].xcom_pull(key="zones", task_ids="get_active_zones")
    if not zones:
        logger.warning("No zones found — skipping predictions")
        return

    # Get auth token once for all requests
    try:
        token = _get_token()
    except Exception as e:
        raise Exception(f"Failed to authenticate with backend: {e}")

    headers    = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    success    = 0
    errors     = 0

    for zone in zones:
        try:
            # ── Flood prediction ──────────────────────────────────────────
            flood_resp = _requests.post(
                f"{BACKEND_URL}/api/predictions/flood/{zone['id']}",
                headers=headers,
                timeout=30,
            )

            flood_resp.raise_for_status()
            flood_data  = flood_resp.json()
            flood_prob  = flood_data.get("probability", 0.0)
            flood_level = flood_data.get("risk_level", "LOW")

            # ── Fire prediction ───────────────────────────────────────────
            fire_resp = _requests.post(
                f"{BACKEND_URL}/api/predictions/fire/{zone['id']}",
                headers=headers,
                timeout=30,
            )

            fire_resp.raise_for_status()
            fire_data  = fire_resp.json()
            fire_prob  = fire_data.get("probability", 0.0)
            fire_level = fire_data.get("risk_level", "LOW")

            logger.info(
                f"✅ {zone['name']}: "
                f"flood={flood_level}({flood_prob:.2f}) "
                f"fire={fire_level}({fire_prob:.2f})"
            )
            success += 1
            time.sleep(1.5)
        except Exception as e:
            logger.error(f"❌ {zone['name']}: {e}")
            errors += 1

    duration = time.time() - start_time
    logger.info(f"✅ Done: {success} OK, {errors} errors, {duration:.1f}s")

    context["ti"].xcom_push(key="summary", value={
        "success":  success,
        "errors":   errors,
        "duration": duration,
    })

    if errors > 0:
        raise Exception(f"{errors} zone(s) failed — check logs above")


# ── Task 3: Push metrics to Prometheus Pushgateway ────────────────────────────

def push_metrics(**context):
    summary = context["ti"].xcom_pull(key="summary", task_ids="predict_all_zones")
    if not summary:
        logger.warning("No summary found — skipping metrics push")
        return

    try:
        from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

        registry = CollectorRegistry()

        Gauge("climarisk_dag_run_duration_seconds",
              "Time taken for the last DAG run",
              registry=registry).set(summary["duration"])

        Gauge("climarisk_dag_zones_success",
              "Zones successfully processed in last run",
              registry=registry).set(summary["success"])

        Gauge("climarisk_dag_zones_errors",
              "Zones that failed in last run",
              registry=registry).set(summary["errors"])

        push_to_gateway(PUSHGATEWAY_URL, job="climarisk_airflow", registry=registry)
        logger.info(f"✅ Metrics pushed to {PUSHGATEWAY_URL}")

    except Exception as e:
        logger.warning(f"⚠️  Pushgateway unavailable: {e}")


# ── Wire up tasks ─────────────────────────────────────────────────────────────

t1 = PythonOperator(task_id="get_active_zones",  python_callable=get_active_zones,  dag=dag)
t2 = PythonOperator(task_id="predict_all_zones", python_callable=predict_all_zones, dag=dag)
t3 = PythonOperator(task_id="push_metrics",      python_callable=push_metrics,      dag=dag,
                    trigger_rule="all_done")

t1 >> t2 >> t3