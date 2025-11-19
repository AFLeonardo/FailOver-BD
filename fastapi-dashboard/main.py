import os
from typing import List, Optional
from datetime import datetime
import mysql.connector
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

# ---------- MODELOS ----------

class Event(BaseModel):
    event_type: str
    primary_node: Optional[str] = None
    replica_node: Optional[str] = None
    last_failover: Optional[datetime] = None
    last_backup: Optional[datetime] = None
    created_at: Optional[datetime] = None

class StatusResponse(BaseModel):
    primary_node: Optional[str] = None
    replica_node: Optional[str] = None
    event_type: Optional[str] = None
    created_at: Optional[datetime] = None   # ← fecha oficial
    history: List[Event] = []


def get_db_conn():
    return mysql.connector.connect(
        host="mysql-replica",   # servicio docker
        port=3306,
        user="appuser",
        password="apppass",
        database="appdb",
    )

def get_latest_status():
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT primary_node,
               replica_node,
               last_failover,
               last_backup,
               created_at,
               event_type
        FROM system_events
        ORDER BY created_at DESC
        LIMIT 1
    """
    cursor.execute(query)
    row = cursor.fetchone()

    cursor.close()
    conn.close()
    return row

def get_last_events(limit: int = 10):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT primary_node,
               replica_node,
               last_failover,
               last_backup,
               created_at,
               event_type
        FROM system_events
        ORDER BY created_at DESC
        LIMIT %s
    """
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows


# ---- ENDPOINT /status ----
@app.get("/status", response_model=StatusResponse)
def get_status():
    latest = get_latest_status()
    history = get_last_events(limit=10)

    if not latest:
        return StatusResponse(history=[])

    return StatusResponse(
        primary_node=latest.get("primary_node"),
        replica_node=latest.get("replica_node"),
        event_type=latest.get("event_type"),
        last_failover=None,
        last_backup=None,
        history=history,
        created_at=latest.get("created_at")
    )


# ---------- STATIC ----------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
