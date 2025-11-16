# Failover MySQL + Docker + Watcher — Guía rápida de comandos

## 1. Levantar entorno
```bash
docker compose up -d
docker ps
```

---

## 2. Entrar a MySQL

### Primary:
```bash
docker exec -it mysql-primary mysql -uroot -pFCFM
```

### Replica:
```bash
docker exec -it mysql-replica mysql -uroot -pFCFM
```

---

## 3. Crear usuario de replicación (en PRIMARY)
```sql
CREATE USER 'repl'@'%' IDENTIFIED BY 'replpass';
GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'repl'@'%';
FLUSH PRIVILEGES;
```
### 3.1 Consultar el binlog
```
SHOW MASTER STATUS;
```

---

## 4. Configurar la réplica
```bash
docker exec -it mysql-replica mysql -uroot -pFCFM
```

```sql
STOP REPLICA;

CHANGE REPLICATION SOURCE TO
  SOURCE_HOST='mysql-primary',
  SOURCE_USER='repl',
  SOURCE_PASSWORD='replpass',
  SOURCE_LOG_FILE='mysql-bin.000001',
  SOURCE_LOG_POS=<POSICION>,
  SOURCE_PORT=3306,
  GET_SOURCE_PUBLIC_KEY=1;

START REPLICA;
SHOW REPLICA STATUS\G;
```

---

## 5. Probar replicación
### En primary:
```sql
USE appdb;
INSERT INTO prueba (nombre) VALUES ('test1');
```

### En replica:
```sql
USE appdb;
SELECT * FROM prueba;
```

---

## 6. Crear acceso root desde watcher (necesario para automatización)

### En primary y réplica:
```sql
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'FCFM';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

---

## 7. Construir watcher
```bash
docker compose down
docker compose up -d --build
docker logs -f db-watcher
```

---

## 8. Ejecutar failover automático
```bash
docker stop mysql-primary
```

Ver watcher:
```bash
docker logs -f db-watcher
```

Debe mostrar:
```
Primary falló...
⚠️ Ejecutando failover...
✅ Failover completado.
```

---

## 9. Probar que réplica ahora es Primary:
```bash
docker exec -it mysql-replica mysql -uroot -pFCFM
```

```sql
USE appdb;
INSERT INTO prueba (nombre) VALUES ('post-failover');
SELECT * FROM prueba;
```

---

## 10. Reiniciar todo (si es necesario)
```bash
docker compose down -v
docker compose up -d --build
```

---
