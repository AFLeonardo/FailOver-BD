import mysql.connector
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

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
        SELECT primary_node, replica_node, last_failover, last_backup
        FROM system_events
        ORDER BY created_at DESC
        LIMIT 1
    """
    cursor.execute(query)
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row
