# 🔥 Máquina de Estados del Cluster MySQL – Failover + Resync Automático  
**Autor:** Leonardo  
**Formato:** Diagrama ASCII  
**Objetivo:** Explicar visualmente el ciclo completo de operación → failover → resincronización → restauración.

---

# 🟢 ESTADO A — OPERACIÓN NORMAL  
(mysql-primary es Primary, mysql-replica es Replica)

```text
┌──────────────────────────────────────────────────────────┐
│                   ESTADO A: NORMAL                       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   mysql-primary   (PRIMARY, read_only = 0)               │
│          │                                               │
│          │  Replicación binaria                          │
│          ▼                                               │
│   mysql-replica   (REPLICA, read_only = 1)               │
│                                                          │
│   db-watcher  → monitoreando primary                     │
│   db-resync   → inactivo                                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

# 🔴 TRANSICIÓN A → B — FALLA DEL PRIMARY

```text
mysql-primary deja de responder  →  db-watcher detecta 3 fallos seguidos
```

```text
┌──────────────────────────────────────────────────────────┐
│     TRANSICIÓN A → B: FALLA DETECTADA POR WATCHER        │
├──────────────────────────────────────────────────────────┤
│ fallos_seguidos >= max_fallos                            │
│                                                          │
│ db-watcher ejecuta:                                      │
│   STOP REPLICA;                                          │
│   SET GLOBAL read_only = OFF;                            │
│   SET GLOBAL super_read_only = OFF;                      │
│                                                          │
│ mysql-replica se convierte en PRIMARY                    │
│ fail_over_hecho = True                                   │
└──────────────────────────────────────────────────────────┘
```

---

# 🟠 ESTADO B — FAILOVER ACTIVO  
(El sistema sigue funcionando con la réplica promovida)

```text
┌──────────────────────────────────────────────────────────┐
│               ESTADO B: FAILOVER ACTIVO                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   mysql-primary   (caído o desactualizado)               │
│                                                          │
│   mysql-replica   (PRIMARY, read_only = 0)               │
│   → sistema sigue funcionando normalmente                │
│                                                          │
│   db-watcher: fail_over_hecho = True → espera            │
│   db-resync: esperando a que primary vuelva              │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

# 🔁 TRANSICIÓN B → C — EL PRIMARY VUELVE

```text
mysql-primary vuelve a estar online
mysql-replica sigue en modo escritura (read_only = 0)
→ db-resync detecta condiciones para iniciar resincronización
```

```text
┌──────────────────────────────────────────────────────────┐
│          TRANSICIÓN B → C: RESYNC ACTIVADO               │
├──────────────────────────────────────────────────────────┤
│ db-resync verifica:                                      │
│   checar_primary() == True                               │
│   replica_es_primary_actual() == True (read_only=0)      │
│                                                          │
│ → INICIAL RESYNC AUTOMÁTICO                              │
└──────────────────────────────────────────────────────────┘
```

---

# 🟡 ESTADO C — RESYNC EN PROCESO  
(Backup desde el primary temporal → Restore al primary original)

```text
┌────────────────────────────────────────────────────────────────────┐
│                   ESTADO C: RESYNC EN PROCESO                     │
├────────────────────────────────────────────────────────────────────┤
│ 1) Preparar primary original (mysql-primary):                      │
│      SET GLOBAL read_only = ON;                                    │
│      DROP DATABASE appdb;                                          │
│      CREATE DATABASE appdb;                                        │
│                                                                    │
│ 2) Backup + Restore:                                               │
│      mysqldump desde mysql-replica                                 │
│        │                                                           │
│        └──────► Restaurar datos en mysql-primary                   │
│                                                                    │
│ 3) Restaurar replicación original:                                 │
│      mysql-primary → PRIMARY                                       │
│         │                                                          │
│         └──────► mysql-replica → REPLICA                           │
│            read_only = 1                                           │
│                                                                    │
│ 4) resync_hecho = True                                             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

# 🔄 TRANSICIÓN C → A — TODO VUELVE A LA NORMALIDAD

```text
db-watcher detecta:

  fail_over_hecho == True   (hubo failover)
  checar_primary() == True  (primary ya está online)
  replica_es_replica() == True  (read_only = 1)

→ Reactiva el watcher para un NUEVO ciclo
```

---

# 🟢 VUELTA AL ESTADO A — LISTO PARA OTRO CICLO

```text
┌──────────────────────────────────────────────────────────┐
│              ESTADO A (NUEVAMENTE)                       │
├──────────────────────────────────────────────────────────┤
│ mysql-primary  (PRIMARY, read_only=0)                    │
│      │                                                   │
│      └──► mysql-replica  (REPLICA, read_only=1)          │
│                                                          │
│ db-watcher: activo otra vez                              │
│ db-resync: esperando próximo failover                    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

# 🔁 🔁 🔁 CICLO COMPLETO — SE REPITE INFINITAS VECES

```text
    ┌──────────────┐
    │   ESTADO A   │  (OPERACIÓN NORMAL)
    └───────┬──────┘
            │ primary falla
            ▼
    ┌──────────────┐
    │   ESTADO B   │  (FAILOVER ACTIVO)
    └───────┬──────┘
            │ primary vuelve
            ▼
    ┌──────────────┐
    │   ESTADO C   │  (RESYNC)
    └───────┬──────┘
            │ resync completado
            ▼
    ┌──────────────┐
    │   ESTADO A   │  (OPERACIÓN NORMAL)
    └──────────────┘
```

---

# ✔️ Este ciclo puede repetirse N veces  
- Si el primary vuelve a caer → failover automático otra vez  
- Si luego vuelve → resync automático  
- Si vuelve a caer → reinicia el ciclo  

Tu sistema soporta **alta disponibilidad real**, estilo profesional 😎🔥
