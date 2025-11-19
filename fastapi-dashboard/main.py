import mysql.connector
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

# ---- ENDPOINT /status ----
class StatusResponse(BaseModel):
    primary_node: str | None = None
    replica_node: str | None = None
    event_type: str | None = None
    last_failover: str | None = None

@app.get("/status")
def get_status():
    row = get_latest_status()
    return row

def get_latest_status():
    conn = mysql.connector.connect(
        host="mysql-replica",      # aquí va tu host (por ejemplo: "localhost" o el nombre del contenedor)
        port=3306,       # si usas otro puerto, cámbialo
        user="appuser",      # tu usuario MySQL
        password="apppass",  # tu contraseña
        database="appdb" # o el nombre real de tu BD
    )

    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT primary_node, replica_node, last_failover, last_backup, event_type
        FROM system_events
        ORDER BY created_at DESC
        LIMIT 1
    """
    cursor.execute(query)
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row

# Montar archivos estáticos (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")