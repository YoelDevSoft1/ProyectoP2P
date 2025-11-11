# ✅ Estado de la Base de Datos

## 📊 Resumen

**¡SÍ TIENES BASE DE DATOS Y ESTÁ FUNCIONANDO!** 🎉

## 🔍 Verificación Actual

### 1. Contenedor PostgreSQL
- **Estado**: ✅ **RUNNING** (Up 2 hours, healthy)
- **Contenedor**: `p2p_postgres`
- **Imagen**: `timescale/timescaledb:latest-pg15`
- **Puerto**: `5432:5432`
- **Health Check**: ✅ **HEALTHY**

### 2. Base de Datos
- **Nombre**: `p2p_db`
- **Usuario**: `p2p_user`
- **Contraseña**: `p2p_password_change_me` (configurada en docker-compose.yml)
- **Estado**: ✅ **ACTIVA**

### 3. Tablas Creadas
Las siguientes tablas existen en la base de datos:

1. ✅ **`users`** - Usuarios del sistema
2. ✅ **`trades`** - Operaciones de trading
3. ✅ **`price_history`** - Historial de precios
4. ✅ **`alerts`** - Alertas del sistema
5. ✅ **`app_config`** - Configuración persistente

### 4. Configuración
- **DATABASE_URL**: `postgresql://p2p_user:p2p_password_change_me@localhost:5432/p2p_db`
- **Estado**: ✅ **CONFIGURADO** en `.env`

## 📈 Datos Actuales

Para verificar los datos en la base de datos, ejecuta:

```bash
# Ver cantidad de registros
docker exec p2p_postgres psql -U p2p_user -d p2p_db -c "
  SELECT 
    'trades' as tabla, COUNT(*) as registros FROM trades
  UNION ALL
  SELECT 'alerts', COUNT(*) FROM alerts
  UNION ALL
  SELECT 'price_history', COUNT(*) FROM price_history
  UNION ALL
  SELECT 'app_config', COUNT(*) FROM app_config;
"
```

## 🔧 Comandos Útiles

### Conectar a la Base de Datos
```bash
# Conectar desde Docker
docker exec -it p2p_postgres psql -U p2p_user -d p2p_db

# Conectar desde fuera de Docker (requiere cliente PostgreSQL)
psql -h localhost -p 5432 -U p2p_user -d p2p_db
```

### Ver Todas las Tablas
```bash
docker exec p2p_postgres psql -U p2p_user -d p2p_db -c "\dt"
```

### Ver Estructura de una Tabla
```bash
# Ver estructura de la tabla alerts
docker exec p2p_postgres psql -U p2p_user -d p2p_db -c "\d+ alerts"

# Ver estructura de la tabla trades
docker exec p2p_postgres psql -U p2p_user -d p2p_db -c "\d+ trades"
```

### Ver Datos
```bash
# Ver últimos 10 trades
docker exec p2p_postgres psql -U p2p_user -d p2p_db -c "SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;"

# Ver últimas 10 alertas
docker exec p2p_postgres psql -U p2p_user -d p2p_db -c "SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;"

# Ver configuración persistente
docker exec p2p_postgres psql -U p2p_user -d p2p_db -c "SELECT * FROM app_config;"
```

## 🗄️ Estructura de las Tablas

### Tabla: `users`
- Almacena información de usuarios del sistema
- Campos: `id`, `email`, `username`, `hashed_password`, `created_at`, etc.

### Tabla: `trades`
- Almacena operaciones de trading
- Campos: `id`, `user_id`, `asset`, `fiat`, `amount`, `price`, `status`, `created_at`, etc.

### Tabla: `price_history`
- Almacena historial de precios P2P
- Campos: `id`, `asset`, `fiat`, `bid_price`, `ask_price`, `avg_price`, `timestamp`, etc.

### Tabla: `alerts`
- Almacena alertas del sistema
- Campos: `id`, `type`, `title`, `message`, `asset`, `fiat`, `percentage`, `created_at`, etc.

### Tabla: `app_config`
- Almacena configuración persistente
- Campos: `id`, `key`, `value`, `value_type`, `description`, `created_at`, `updated_at`

## 🔍 Verificación de Salud

### Health Check del Backend
```bash
curl http://localhost:8000/api/v1/health
```

Debe retornar:
```json
{
  "status": "healthy",
  "services": {
    "postgresql": {
      "status": "connected"
    },
    "postgresql_async": {
      "status": "healthy"
    }
  }
}
```

### Health Check Específico de Base de Datos
```bash
curl http://localhost:8000/api/v1/health/db
```

Debe retornar:
```json
{
  "status": "healthy",
  "total_trades": 0,
  "database": "postgresql"
}
```

## 📊 Volúmenes de Datos

Los datos están almacenados en un volumen de Docker:
- **Volumen**: `postgres_data`
- **Ubicación en host**: `/var/lib/docker/volumes/proyectop2p_postgres_data/_data`
- **Persistencia**: ✅ Los datos persisten aunque reinicies el contenedor

## 🔄 Backup y Restore

### Crear Backup
```bash
# Backup completo de la base de datos
docker exec p2p_postgres pg_dump -U p2p_user p2p_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup solo de datos (sin estructura)
docker exec p2p_postgres pg_dump -U p2p_user -a p2p_db > backup_data_$(date +%Y%m%d_%H%M%S).sql
```

### Restaurar Backup
```bash
# Restaurar desde backup
cat backup_20250101_120000.sql | docker exec -i p2p_postgres psql -U p2p_user -d p2p_db
```

## ⚠️ Problemas Comunes

### Problema: Base de datos no responde
**Solución**:
```bash
# Verificar que el contenedor esté corriendo
docker ps | grep postgres

# Reiniciar el contenedor
docker-compose restart postgres

# Ver logs
docker-compose logs postgres
```

### Problema: No se pueden crear tablas
**Solución**:
```bash
# Verificar que las tablas existan
docker exec p2p_postgres psql -U p2p_user -d p2p_db -c "\dt"

# Si faltan tablas, reiniciar el backend para que las cree
docker-compose restart backend
```

### Problema: Error de conexión
**Solución**:
1. Verificar que `DATABASE_URL` esté correcto en `.env`
2. Verificar que el contenedor esté corriendo
3. Verificar que el puerto 5432 esté disponible

## ✅ Conclusión

**Tu base de datos está funcionando correctamente:**
- ✅ Contenedor corriendo y saludable
- ✅ Base de datos creada
- ✅ Tablas creadas
- ✅ Configuración correcta
- ✅ Datos persistiendo

**No hay problemas con la base de datos. Todo está funcionando como debería.**

