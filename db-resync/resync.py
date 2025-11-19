import time
import subprocess
import mysql.connector
from mysql.connector import Error

ROOT_PASSWORD = "FCFM"
DB_NAME = "appdb"
REPL_USER = "repl"
REPL_PASS = "replpass"
CHECK_INTERVAL = 10  # segundos

resync_hecho = False


def conectar(host):
    return mysql.connector.connect(
        host=host,
        port=3306,
        user="root",
        password=ROOT_PASSWORD
    )


def primary_original_disponible():
    try:
        conn = conectar("mysql-primary")
        conn.close()
        return True
    except Error:
        return False


def replica_es_primary_actual():
    """
    Revisamos si mysql-replica está en modo escritura.
    Si read_only = 0 -> está actuando como primary.
    """
    try:
        conn = conectar("mysql-replica")
        cur = conn.cursor()
        cur.execute("SELECT @@global.read_only;")
        (read_only,) = cur.fetchone()
        cur.close()
        conn.close()
        return int(read_only) == 0
    except Error:
        return False


def preparar_primary_original():
    print("🔧 Preparando mysql-primary en modo seguro (solo lectura y DB limpia)...")
    conn = conectar("mysql-primary")
    cur = conn.cursor()
    #cur.execute("SET GLOBAL super_read_only = ON;")
    cur.execute("SET GLOBAL read_only = ON;")
    cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
    cur.execute(f"CREATE DATABASE {DB_NAME};")
    conn.commit()
    cur.close()
    conn.close()
    print("✅ mysql-primary preparado.")


def backup_y_restore():
    print("📦 Iniciando backup desde mysql-replica y restore a mysql-primary...")

    cmd = (
        f"mysqldump --skip-ssl -h mysql-replica -uroot -p{ROOT_PASSWORD} {DB_NAME} "
        f"| mysql --skip-ssl -h mysql-primary -uroot -p{ROOT_PASSWORD} {DB_NAME}"
    )

    subprocess.run(cmd, shell=True, check=True)
    print("✅ Backup y restore completados.")


def configurar_primary_como_primary_y_replica_como_replica():
    """
    Escenario B:
    - mysql-primary vuelve a ser PRIMARY
    - mysql-replica vuelve a ser RÉPLICA
    """

    print("🔁 Configurando mysql-primary como PRIMARY y mysql-replica como REPLICA...")

    # 1) En mysql-primary: crear usuario de replicación y obtener MASTER STATUS
    conn_p = conectar("mysql-primary")
    cur_p = conn_p.cursor()

    # Crear usuario repl si no existe
    try:
        cur_p.execute(
            f"CREATE USER IF NOT EXISTS '{REPL_USER}'@'%' IDENTIFIED BY '{REPL_PASS}';"
        )
    except Error as e:
        print("⚠️ Aviso al crear usuario repl en primary:", e)

    cur_p.execute(
        f"GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO '{REPL_USER}'@'%';"
    )
    cur_p.execute("FLUSH PRIVILEGES;")

    cur_p.execute("SHOW MASTER STATUS;")
    row = cur_p.fetchone()
    if not row:
        raise RuntimeError("SHOW MASTER STATUS no devolvió información en mysql-primary.")

    file, position = row[0], row[1]
    print(f"ℹ️ MASTER STATUS en primary: File={file}, Position={position}")

    conn_p.commit()
    cur_p.close()
    conn_p.close()

    # 2) En mysql-replica: apuntarla a mysql-primary
    conn_r = conectar("mysql-replica")
    cur_r = conn_r.cursor()

    cur_r.execute("STOP REPLICA;")

    change_cmd = (
        f"CHANGE REPLICATION SOURCE TO "
        f"SOURCE_HOST='mysql-primary', "
        f"SOURCE_USER='{REPL_USER}', "
        f"SOURCE_PASSWORD='{REPL_PASS}', "
        f"SOURCE_LOG_FILE='{file}', "
        f"SOURCE_LOG_POS={position}, "
        f"SOURCE_PORT=3306, "
        f"GET_SOURCE_PUBLIC_KEY=1;"
    )
    cur_r.execute(change_cmd)

    cur_r.execute("START REPLICA;")
    # Volver a dejar la réplica en solo lectura
    cur_r.execute("SET GLOBAL read_only = ON;")
    cur_r.execute("SET GLOBAL super_read_only = ON;")

    conn_r.commit()
    cur_r.close()
    conn_r.close()

    print("✅ Topología restaurada: mysql-primary = PRIMARY, mysql-replica = REPLICA.")


def habilitar_escritura_en_primary():
    conn = conectar("mysql-primary")
    cur = conn.cursor()
    cur.execute("SET GLOBAL super_read_only = OFF;")
    cur.execute("SET GLOBAL read_only = OFF;")
    conn.commit()
    cur.close()
    conn.close()
    print("✅ mysql-primary ahora acepta escrituras.")


def main():
    
    print("👀 Iniciando db-resync (resincronización automática)...")

    while True:

        # 1) Ver si mysql-primary ya está disponible
        if not primary_original_disponible():
            print("⏳ mysql-primary todavía no está disponible. Esperando...")
            time.sleep(CHECK_INTERVAL)
            continue

        # 2) Ver si mysql-replica está actuando como primary (read_only=0)
        if not replica_es_primary_actual():
            print("ℹ️ mysql-replica NO está en modo escritura. Posible que no haya failover aún.")
            time.sleep(CHECK_INTERVAL)
            continue

        print("✅ Condiciones detectadas: primary original arriba y réplica actuando como primary.")
        print("🚀 Iniciando proceso de resincronización...")

        try:
            preparar_primary_original()
            backup_y_restore()
            configurar_primary_como_primary_y_replica_como_replica()
            habilitar_escritura_en_primary()
            print("🎉 Resincronización completada.")
        except Exception as e:
            print("❌ Error durante la resincronización:", e)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
