import time
import mysql.connector
from mysql.connector import Error

max_fallos = 3
tiempo_espera = 5
fail_over_hecho = False

def checar_primary():
    try:
        conn = mysql.connector.connect(
            host="mysql-primary",
            port=3306,
            user="root",
            password="FCFM"
        )
        if conn.is_connected():
            conn.close()
            return True
    except Error:
        return False

def replica_es_replica():
    """Devuelve True si mysql-replica está en read_only=1 (o sea, otra vez como réplica)."""
    try:
        conn = mysql.connector.connect(
            host="mysql-replica",
            port=3306,
            user="root",
            password="FCFM"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT @@global.read_only;")
        (read_only,) = cursor.fetchone()
        cursor.close()
        conn.close()
        return int(read_only) == 1
    except Error:
        return False

def promover_replica():
    global fail_over_hecho
    try:
        conn = mysql.connector.connect(
            host="mysql-replica",
            port=3306,
            user="root",
            password="FCFM"
        )
        cursor = conn.cursor()
        print("⚠️ Ejecutando failover: promoviendo réplica...")

        cursor.execute("STOP REPLICA;")
        cursor.execute("SET GLOBAL read_only = OFF;")
        cursor.execute("SET GLOBAL super_read_only = OFF;")
        conn.commit()

        cursor.close()
        conn.close()

        fail_over_hecho = True
        print("✅ Failover completado.")
    except Error as e:
        print("❌ Error al promover réplica:", e)

def main():
    global fail_over_hecho
    fallos_seguidos = 0

    print("👀 Iniciando watcher...")

    while True:
        # 🔄 REARMAR el watcher cuando la topología original se haya restaurado
        # Condición: ya hicimos un failover, el primary vuelve a responder
        # y la réplica volvió a estar en read_only (otra vez como réplica).
        if fail_over_hecho and checar_primary() and replica_es_replica():
            print("🔁 Topología restaurada (primary arriba y réplica en read_only). Reactivando watcher.")
            fail_over_hecho = False
            fallos_seguidos = 0

        # Si ya hicimos failover y todavía no se restaura la topología, no hacer nada.
        if fail_over_hecho:
            time.sleep(tiempo_espera)
            continue

        # Monitoreo normal del primary
        if checar_primary():
            fallos_seguidos = 0
            print("Primary OK")
        else:
            fallos_seguidos += 1
            print("Primary falló:", fallos_seguidos)

            if fallos_seguidos >= max_fallos:
                promover_replica()

        time.sleep(tiempo_espera)

if __name__ == "__main__":
    main()
