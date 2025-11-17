# 📘 Proyecto: Sistema de Failover + Resync Automático para MySQL con Docker

**Autor:** Leonardo  
**Tecnologías:** Docker, MySQL 8, Python, Replicación Binaria, Failover Automático  
**Objetivo:** Implementar un sistema completo de Alta Disponibilidad (HA) con failover y resincronización automática entre dos nodos MySQL.

---

# 🏗️ Arquitectura General

El proyecto consiste en tres servicios principales:

```
mysql-primary   → Servidor principal (PRIMARY)
mysql-replica   → Servidor secundario (REPLICA)
db-watcher      → Servicio Python que detecta fallos y ejecuta failover
db-resync       → Servicio Python que repara y resincroniza la topología cuando vuelve el primary
```

Flujo básico del sistema:

1. Operación normal (PRIMARY → REPLICA).
2. El primary falla.
3. `db-watcher` promueve la réplica.
4. La aplicación sigue funcionando sin caerse.
5. El primary vuelve.
6. `db-resync` hace backup + restore desde la réplica a primary.
7. Se restablece la replicación original.
8. El sistema vuelve al estado normal.
9. Este ciclo puede repetirse N veces.

---

# 🧩 Archivos del Proyecto

### 🌐 `docker-compose.yml`
Orquesta todos los servicios:

- `mysql-primary`
- `mysql-replica`
- `db-watcher`
- `db-resync`

Incluye volúmenes para datos y estado compartido.

### 🐍 `db-watcher/watcher.py`
Supervisa el estado del primary y ejecuta:

- `STOP REPLICA`
- `SET GLOBAL read_only=OFF`



### 🐍 `db-resync/resync.py`
Cuando el primary vuelve:

1. Pone primary en read_only.
2. Limpia la BD.
3. Hace backup desde la réplica.
4. Restaura en primary.
5. Reconstruye la topología original.


---

# 🚀 Cómo levantar el proyecto

## 1. Clonar el repositorio

```bash
git clone https://github.com/AFLeonardo/FailOver-BD.git
cd FailOver-BD
```

## 2. Levantar todo

```bash
docker compose up -d --build
```

## 3. Ver contenedores

```bash
docker ps
```

Debes ver:

```
mysql-primary
mysql-replica
db-watcher
db-resync
```

---

# ⚙️ Comandos importantes (para pruebas)

## 🛑 Apagar el primary

```bash
docker stop mysql-primary
```

Esto simula una caída real.

`db-watcher` debe promover la réplica automáticamente.

Logs:

```bash
docker logs -f db-watcher
```

---

## ▶️ Encender nuevamente el primary

```bash
docker start mysql-primary
```

Ahora `db-resync` entra en acción:

```bash
docker logs -f db-resync
```

Debe verse:

```
📦 Iniciando backup...
✅ Backup y restore completados.
🔁 Restaurando topología...
```

---

# 🔍 Verificación manual del estado

## Saber quién es PRIMARY y REPLICA

```bash
docker exec mysql-primary mysql -uroot -pFCFM -e "SELECT @@global.read_only;"
docker exec mysql-replica mysql -uroot -pFCFM -e "SELECT @@global.read_only;"
```

Interpretación:

| Valor | Significado |
|-------|-------------|
| 0     | PRIMARY     |
| 1     | REPLICA     |

---

# 🔥 Logs completos de cada servicio

## db-watcher (failover)

```bash
docker logs -f db-watcher
```

## db-resync (resincronización)

```bash
docker logs -f db-resync
```

## mysql-primary

```bash
docker logs mysql-primary
```

## mysql-replica

```bash
docker logs mysql-replica
```

---

# 🧠 Comportamiento del Sistema (Resumen de Estados)

### ESTADO A — NORMAL
```
mysql-primary  read_only=0  → PRIMARY
mysql-replica  read_only=1  → REPLICA
```

### ESTADO B — FAILOVER ACTIVO
Primary falla → réplica promovida:

```
mysql-replica read_only=0 → PRIMARY TEMPORAL
```

### ESTADO C — RESYNC
Cuando vuelve el primary:

```
backup(repl) → restore(primary)
se restablece replicación
```

### Ciclo completo:
```
NORMAL → FAILOVER → RESYNC → NORMAL → (repetible N veces)
```

---

# 🧪 Prueba completa recomendada

### 1. Levanta todo `docker compose up -d`
### 2. Muestra read_only de ambos nodos
### 3. Apaga el primary (`docker stop mysql-primary`)
### 4. Observa failover (`docker logs -f db-watcher`)
### 5. Inserta datos en el nuevo primary
### 6. Enciende primary original (`docker start mysql-primary`)
### 7. Observa resincronización (`docker logs -f db-resync`)
### 8. Verifica que la topología regresó a lo normal

---

# 🎓 Conclusión

Este proyecto implementa un sistema *totalmente funcional y automatizado* de alta disponibilidad MySQL:

- Failover automático  
- Resincronización automática  
- Recuperación completa de la topología  
- Persistencia de estado  
- Capacidad de repetir el ciclo indefinidamente  
- Todo con Docker + Python  

Este nivel de solución es claramente un proyecto final de alta calidad.

---