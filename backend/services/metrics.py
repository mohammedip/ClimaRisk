"""
ClimaRisk Prometheus Metrics
==============================
All custom metrics defined in one place.
Import from here in main.py, scheduler, routers, etc.

Usage:
    from services.metrics import (
        flood_predictions_total,
        flood_probability_histogram,
        ...
    )
"""
from prometheus_client import Counter, Histogram, Gauge, Summary

# ── Flood predictions ─────────────────────────────────────────────────────────
flood_predictions_total = Counter(
    "climarisk_flood_predictions_total",
    "Total number of flood predictions made",
    ["risk_level", "source"],   # source: manual | scheduler | airflow
)

flood_probability_histogram = Histogram(
    "climarisk_flood_probability",
    "Distribution of flood probability scores",
    ["source"],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

# ── Fire predictions ──────────────────────────────────────────────────────────
fire_predictions_total = Counter(
    "climarisk_fire_predictions_total",
    "Total number of fire predictions made",
    ["risk_level", "source"],
)

fire_probability_histogram = Histogram(
    "climarisk_fire_probability",
    "Distribution of fire probability scores",
    ["source"],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

# ── Alerts ────────────────────────────────────────────────────────────────────
alerts_created_total = Counter(
    "climarisk_alerts_created_total",
    "Total number of alerts auto-created",
    ["hazard_type", "risk_level"],
)

active_alerts_gauge = Gauge(
    "climarisk_active_alerts",
    "Current number of active (unresolved) alerts",
    ["hazard_type"],
)

# ── Zones ─────────────────────────────────────────────────────────────────────
active_zones_gauge = Gauge(
    "climarisk_active_zones_total",
    "Total number of active monitored zones",
)

# ── Airflow DAG ───────────────────────────────────────────────────────────────
dag_run_duration = Summary(
    "climarisk_dag_run_duration_seconds",
    "Time taken for a full Airflow DAG prediction run",
)

dag_zone_errors = Counter(
    "climarisk_dag_zone_errors_total",
    "Number of zones that failed during DAG run",
)

# ── Weather API ───────────────────────────────────────────────────────────────
weather_fetch_duration = Histogram(
    "climarisk_weather_fetch_duration_seconds",
    "Time taken to fetch weather data from Open-Meteo",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
)

weather_fetch_errors = Counter(
    "climarisk_weather_fetch_errors_total",
    "Number of failed weather API calls",
)

# ── System resources (psutil) ─────────────────────────────────────────────────
cpu_usage_gauge = Gauge(
    "climarisk_system_cpu_percent",
    "Current CPU usage percentage",
)

ram_usage_gauge = Gauge(
    "climarisk_system_ram_percent",
    "Current RAM usage percentage",
)

ram_used_bytes_gauge = Gauge(
    "climarisk_system_ram_used_bytes",
    "Current RAM used in bytes",
)