# 📘 Sistema de Failover + Resync Automático para MySQL con Docker

**Autor:** Leonardo  
**Objetivo del proyecto:** Implementar un sistema de Alta Disponibilidad (HA) para MySQL utilizando Docker Compose, con:  
- Failover automático  
- Replicación asíncrona  
- Resincronización cuando un nodo vuelve  
- Watcher en Python  
- Servicio de resync dedicado  
- API con FastAPI + dashboard web



## 🛠 Tech Stack

<div align="center">

| Docker | MySQL | Python | FastAPI | Bash | TailwindCSS | JavaScript | HTML5 |
|--------|--------|---------|---------|--------|--------------|------------|--------|
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg" width="60"/> | <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mysql/mysql-original.svg" width="60"/> | <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="60"/> | <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/fastapi/fastapi-original.svg" width="55"/> | <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/bash/bash-original.svg" width="60"/> | <img src="https://www.vectorlogo.zone/logos/tailwindcss/tailwindcss-icon.svg" width="60"/> | <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-original.svg" width="60"/> | <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/html5/html5-original.svg" width="60"/> |




</div>



## 🏗 Arquitectura General

El sistema está formado por **contenedores Docker** definidos en `docker-compose.yml`:

- **mysql-primary** → Nodo principal (PRIMARY)  
- **mysql-replica** → Nodo secundario (REPLICA) sincronizado por binlogs  
- **db-watcher** → Servicio Python que monitoriza y dispara el failover  
- **db-resync** → Servicio Python que resincroniza nodos desactualizados  
- **fastapi-dashboard** → API FastAPI + dashboard web (HTML estático)


## 📐 Diagrama general

```
                         ┌─────────────────────────────┐
                         │     fastapi-dashboard       │
                         │   - FastAPI (API REST)      │
                         │   - Dashboard HTML          │
                         └─────────────┬───────────────┘
                                       │
                               Usuario / Navegador
                                       │
                     ┌─────────────────┴─────────────────┐
                     │                                   │
        ┌────────────────────────┐           ┌────────────────────────┐
        │      mysql-primary     │           │     mysql-replica      │
        │      Role: PRIMARY     │◄────────►│     Role: REPLICA      │
        │  Binlogs habilitados   │           │ IO/SQL threads activos │
        └─────────────┬──────────┘           └─────────────┬──────────┘
                      │                                    │
                      └──────────────┬─────────────────────┘
                                     │
                      ┌────────────────────────────┐
                      │        db-watcher          │
                      │  - Heartbeat               │
                      │  - Failover automático     │
                      │  - Registro de eventos     │
                      └────────────────────────────┘

                      ┌────────────────────────────┐
                      │         db-resync          │
                      │  - Dump/restore            │
                      │  - Reconfig. replicación   │
                      └────────────────────────────┘
```



## ⚙️ Flujo de Failover y Recovery

### 🟥 **Cuando el primary cae**

1. `db-watcher` deja de recibir respuesta de `mysql-primary`.  
2. Marca el primary como **DOWN**.  
3. Promueve `mysql-replica` → **PRIMARY** lógico.  
4. Detiene replicación (IO/SQL threads).  
5. Registra el evento en los logs (accesible desde la API/dashboard).


### 🟩 **Cuando el nodo caído vuelve**

1. El nodo puede regresar **desactualizado** respecto al nuevo primary.  
2. `db-watcher` activa el proceso `db-resync`.  
3. Se toma un **dump** del nodo saludable.  
4. Se restaura en el nodo que regresó.  
5. Se reconfigura la replicación (usuario, host, log_file, log_pos).  
6. Se reinician los IO/SQL threads.  
7. Los estados son actualizados y registrados.


## 🚀 Levantar el proyecto

Asegúrate de tener Docker y Docker Compose instalados.

```bash
git clone https://github.com/AFLeonardo/FailOver-BD.git
cd FailOver-BD

# Levantar todos los servicios
docker-compose up -d --build

# Ver contenedores
docker ps
```

Debes ver:
```
mysql-primary
mysql-replica
db-watcher
db-resync
fastapi-dashboard
```

# Comandos importantes

### 🛑 Apagar el primary

```bash
docker stop mysql-primary
```
Esto simula una caída real.
#### `db-watcher` debe promover la réplica automáticamente.

### Comandos para Logs:

```bash
docker logs -f db-watcher
docker logs -f db-resync
docker logs -f fastapi-dashboard
```


## 🆗 Encender nuevamente el primary

```bash
docker start mysql-primary
```

#### Ahora `db-resync` entra en acción:

```bash
docker logs -f db-resync
```

Debe verse:

```
📦 Iniciando backup...
✅ Backup y restore completados.
🔁 Restaurando topología...
```


## 🌐 Acceso al Dashboard y la API

### Dashboard web (HTML estático)
```
http://localhost:8000/static/dashboard.html
```

### FastAPI docs (Swagger UI)
```
http://localhost:8000/docs
```

---

## 🧱 Estructura del repositorio

```
/
├── db-resync/
│   ├── Dockerfile
│   └── resync.py
│
├── db-watcher/
│   ├── Dockerfile
│   └── watcher.py
│
├── fastapi-dashboard/
│   ├── static/
│   │   └── dashboard.html
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
│
├── DB.sql
├── docker-compose.yml
├── LICENSE
├── README.md
```


## 📓 Notas Técnicas

### 📌 Replicación MySQL
- Replicación asíncrona.  
- `server-id` distinto para cada nodo.  
- Binlogs habilitados en el primary.  

### 📌 Watcher (`db-watcher`)
- Implementado en Python.  
- Registra todos los eventos para monitoreo.  

### 📌 Resync (`db-resync`)
- Ejecuta dump + restore automático.  
- Reconfigura la replicación.  
- Vuelve a enganchar el nodo desactualizado.

### 📌 FastAPI + Dashboard (`fastapi-dashboard`)
#### main.py expone:
- Estado del cluster  
- Logs del watcher  
- Acciones manuales (failover, resync)  

#### dashboard.html muestra:
- Estado en tiempo real  
- Últimos eventos  
- Indicadores visuales  


---
# 🎓 Conclusión
Este proyecto implementa un sistema *totalmente funcional y automatizado* de alta disponibilidad MySQL:

- Failover automático
- Resincronización automática
- Recuperación completa de la topología
- Capacidad de repetir el ciclo indefinidamente
- FastAPI para mostrar estado del cluster en el Dashboard
- Todo con Docker + Python