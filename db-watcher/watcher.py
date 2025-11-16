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
    fallos_seguidos = 0
    global fail_over_hecho

    print("👀 Iniciando watcher...")

    while True:
        if fail_over_hecho:
            time.sleep(tiempo_espera)
            continue

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
